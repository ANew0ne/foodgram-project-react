from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction

from api.image_fields import Base64ImageField
from users.models import Subscription
from recipes.models import (Ingredient, Recipe, Favorites, ShoppingCart,
                            RecipeIngredient, Tag)


UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор модели пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and obj and request.user.is_authenticated:
            return obj.subscriptions.filter(
                user=request.user,
                subscription=obj
            ).exists()
        return False


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор модели Тэгов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор модели Ингредиентов."""

    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.ReadOnlyField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class IngredientsInRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов в рецепт."""

    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class PreviewRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для рецепта в сокращенном виде."""
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    tags = TagSerializer(many=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='recipe_ingredient',
        many=True
    )
    image = Base64ImageField(required=True, allow_null=False)
    is_favorited = serializers.BooleanField(read_only=True, default=False)
    is_in_shopping_cart = serializers.BooleanField(read_only=True,
                                                   default=False)

    class Meta:
        model = Recipe
        exclude = ('pub_date',)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи рецептов."""

    ingredients = IngredientsInRecipeWriteSerializer(many=True)
    image = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = Recipe
        exclude = ('pub_date', 'author')

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data

    def validate(self, data):
        ingredients = data.get('ingredients')
        tags = data.get('tags')
        if not (ingredients and tags):
            raise serializers.ValidationError('Не все поля заполнены.')
        if (len(set([tuple(item.items()) for item in ingredients]))
                != len(ingredients)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )
        if len(set(tags)) != len(tags):
            raise serializers.ValidationError('Тэги не должны повторяться.')
        return data

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        author = self.context.get('request').user
        recipe = Recipe.objects.create(author=author, **validated_data)
        recipe.tags.set(tags)
        self.get_ingredients(recipe, ingredients)
        return recipe

    @staticmethod
    def get_ingredients(recipe, ingredients_list):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(recipe=recipe,
                              ingredient=ingredient['id'],
                              amount=ingredient['amount'])
                for ingredient in ingredients_list]
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        instance.tags.set(tags)
        instance.ingredients.clear()
        self.get_ingredients(instance, ingredients)
        return super().update(instance, validated_data)


class RecipesOfUserSerializer(UserSerializer):
    """Сериализатор для рецептов пользователя."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        recipes_limit = (self.context['request'].query_params.
                         get('recipes_limit'))
        recipes = obj.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except ValueError:
                pass
        serializer = PreviewRecipeSerializer(
            recipes,
            many=True,
            context=self.context)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class FavoriteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserModel.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = Favorites
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if Favorites.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в избранном.'
            )
        return data

    def to_representation(self, instance):
        recipe = instance.recipe
        return PreviewRecipeSerializer(recipe, context=self.context).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserModel.objects.all())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')

    def validate(self, data):
        user = data.get('user')
        recipe = data.get('recipe')
        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже есть в списке покупок.'
            )
        return data

    def to_representation(self, instance):
        recipe = instance.recipe
        return PreviewRecipeSerializer(recipe, context=self.context).data


class SubscriptionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=UserModel.objects.all())
    subscription = serializers.PrimaryKeyRelatedField(
        queryset=UserModel.objects.all())

    class Meta:
        model = Subscription
        fields = ('user', 'subscription')

    def validate(self, data):
        user = data.get('user')
        subscription = data.get('subscription')
        if user == subscription:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя',
            )
        if Subscription.objects.filter(
            user=user, subscription=subscription
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя',
            )
        return data

    def to_representation(self, instance):
        subscription = instance.subscription
        return RecipesOfUserSerializer(subscription, context=self.context).data
