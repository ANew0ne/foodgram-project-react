from django.urls import include, path
from rest_framework import routers

from api.views import (RecipeViewSet, IngredientViewSet,
                       TagViewSet, FoodgramUserViewSet)

namespace = 'api'

v1_router = routers.DefaultRouter()
v1_router.register('recipes', RecipeViewSet, basename='recipes')
v1_router.register('ingredients', IngredientViewSet, basename='ingredients')
v1_router.register('tags', TagViewSet, basename='tags')
v1_router.register('users', FoodgramUserViewSet, basename='users')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
