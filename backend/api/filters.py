from django_filters.rest_framework import (FilterSet, filters)

from recipes.models import Tag, Recipe, Ingredient


class RecipeFilter(FilterSet):
    """
    Фильтр для рецептов, позволяющий фильтровать
    по тегам, избранному, списку покупок и автору.
    """
    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.NumberFilter(method='filter_by_favorited')
    is_in_shopping_cart = filters.NumberFilter(
        method='filter_by_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'is_favorited', 'is_in_shopping_cart', 'author')

    def filter_by_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(favoritesrecipes__user=user)
        return queryset

    def filter_by_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated and value:
            return queryset.filter(shoppingcartrecipes__user=user)
        return queryset


class IngredientFilter(FilterSet):
    """Фильтр для ингредиентов, позволяющий фильтровать по названию тэгов."""

    name = filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
