from django.contrib import admin

from .models import (Recipe, Ingredient, Tag, RecipeIngredient,
                     ShoppingCart, Favorites)


admin.site.empty_value_display = 'пусто'


class IngridientsInLine(admin.StackedInline):
    """Отображение связанных ингредиентов в админке рецепта."""
    model = RecipeIngredient
    extra = 0


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Административный класс для управления рецептами."""
    inlines = (IngridientsInLine, )
    list_display = (
        'name',
        'author',
    )
    list_filter = (
        'tags',
    )
    search_fields = (
        'name',
        'author',
    )


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Административный класс для управления ингридиентами."""
    list_display = (
        'name',
        'measurement_unit'
    )
    list_editable = (
        'measurement_unit',
    )
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Административный класс для управления тэгами."""
    list_display = (
        'name',
        'color',
        'slug'
    )
    list_editable = (
        'color',
        'slug'
    )
    search_fields = ('name',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Административный класс для управления списком покупок."""

    list_display = (
        'user',
        'recipe'
    )
    search_fields = ('user',)


@admin.register(Favorites)
class FavoritesAdmin(admin.ModelAdmin):
    """Административный класс для управления списком избранного."""

    list_display = (
        'user',
        'recipe'
    )
    search_fields = ('user',)
