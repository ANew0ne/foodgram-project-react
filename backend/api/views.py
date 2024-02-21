import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from djoser.views import UserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters import RecipeFilter, IngredientFilter
from api.paginators import FoodgramPageNumberPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (
    RecipeReadSerializer, RecipeWriteSerializer,
    PreviewRecipeSerializer, UserSerializer,
    TagSerializer, IngredientSerializer,
    RecipesOfUserSerializer
)
from recipes.models import Recipe, Tag, Ingredient, Favorites, ShoppingCart
from users.models import Subscription, FoodgramUser


class RecipeViewSet(ModelViewSet):
    """
    API-интерфейс для просмотра, создания, обновления и удаления рецептов.
    """

    queryset = Recipe.objects.all()
    pagination_class = FoodgramPageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering_fields = ('-pub_date', 'name',)

    def get_serializer_class(self):
        if self.action in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @action(detail=True,
            methods=('POST', 'DELETE'),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        user = request.user
        if request.method == 'POST':
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                return Response(
                    {'ошибка': 'Такого рецепта не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Favorites.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'ошибка': 'Этот рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorites.objects.create(user=user, recipe=recipe)
            serializer = PreviewRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            if not Favorites.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'ошибка': 'Такого рецепта нет в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorites.objects.filter(user=user, recipe=recipe).delete()
            return Response(
                'Рецепт удален из избранного',
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True,
            methods=('POST', 'DELETE'),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        user = request.user

        if request.method == 'POST':
            try:
                recipe = Recipe.objects.get(id=pk)
            except Recipe.DoesNotExist:
                return Response(
                    {'ошибка': 'Такого рецепта не существует.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'ошибка': 'Этот рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = PreviewRecipeSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            recipe = get_object_or_404(Recipe, id=pk)
            if not ShoppingCart.objects.filter(user=user,
                                               recipe=recipe).exists():
                return Response(
                    {'ошибка': 'Такого рецепта нет в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response('Рецепт удален из списка покупок',
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('GET',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user = request.user
        recipes = Recipe.objects.filter(shoppingcartrecipes__user=user)
        if not recipes:
            return Response({'Ошибка': 'Список покупок пуст'},
                            status=status.HTTP_404_NOT_FOUND)

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        pdfmetrics.registerFont(TTFont('Verdana', 'Verdana.ttf'))
        p.setFont('Verdana', 18)
        p.drawString(220, 800, 'Список покупок')
        ingredients = {}
        for recipe in recipes:
            for recipe_ingredient in recipe.recipe_ingredient.all():
                ingredient_key = (
                    f'• {recipe_ingredient.ingredient.name} '
                    f'({recipe_ingredient.ingredient.measurement_unit})'
                )
                if ingredient_key in ingredients:
                    ingredients[ingredient_key] += recipe_ingredient.amount
                else:
                    ingredients[ingredient_key] = recipe_ingredient.amount
        x = 20
        y = 750
        for key, value in ingredients.items():
            p.drawString(x, y, f'{key} — {value}')
            y = y - 20
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer,
                            as_attachment=True,
                            filename='shopping-list.pdf')


class TagViewSet(ReadOnlyModelViewSet):
    """API-интерфейс для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    """API-интерфейс для просмотра ингредиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class FoodgramUserViewSet(UserViewSet):
    """API-интерфейс для управления профилями пользователей и подписками."""

    queryset = FoodgramUser.objects.all()
    serializer_class = UserSerializer
    pagination_class = FoodgramPageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=True,
            methods=('POST', 'DELETE'),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        user = request.user
        if request.method == 'POST':
            subscription = get_object_or_404(FoodgramUser, id=id)
            if user == subscription:
                return Response(
                    {'ошибка': 'Вы не можете подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Subscription.objects.filter(
                user=user,
                subscription=subscription
            ).exists():
                return Response(
                    {'ошибка': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, subscription=subscription)
            serializer = RecipesOfUserSerializer(subscription,
                                                 context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            subscription = get_object_or_404(FoodgramUser, id=id)
            if not Subscription.objects.filter(
                user=user,
                subscription=subscription
            ).exists():
                return Response({'ошибка': 'Такой подписки не существует'},
                                status=status.HTTP_400_BAD_REQUEST)
            Subscription.objects.filter(
                user=user, subscription=subscription
            ).delete()
            return Response('Вы отписались от этого пользователя',
                            status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('GET',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = FoodgramUser.objects.filter(subscriptions__user=user)
        paginator = FoodgramPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RecipesOfUserSerializer(
            page,
            many=True,
            context={'request': request}
        ).data
        return paginator.get_paginated_response(serializer)
