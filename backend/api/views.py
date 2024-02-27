import io
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from django.contrib.auth import get_user_model
from django.db.models import Sum
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
    UserSerializer,
    TagSerializer, IngredientSerializer,
    RecipesOfUserSerializer, FavoriteSerializer,
    ShoppingCartSerializer, SubscriptionSerializer
)
from recipes.models import (Recipe, Tag, Ingredient, Favorites,
                            ShoppingCart, RecipeIngredient)
from users.models import Subscription


UserModel = get_user_model()


class RecipeViewSet(ModelViewSet):
    """
    API-интерфейс для просмотра, создания, обновления и удаления рецептов.
    """

    queryset = Recipe.objects.all().select_related(
        'author'
    ).prefetch_related('tags', 'ingredients')
    pagination_class = FoodgramPageNumberPagination
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    ordering_fields = ('-pub_date', 'name',)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return super().get_queryset().recipe_annotate(self.request.user)
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action in permissions.SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    @staticmethod
    def download_file(ingredients):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        pdfmetrics.registerFont(TTFont('Roboto', 'Roboto.ttf'))
        p.setFont('Roboto', 18)
        p.drawString(220, 800, 'Список покупок')
        x = 20
        y = 750
        for ingredient in ingredients:
            key = (f'• {ingredient["ingredient__name"]} '
                   f'({ingredient["ingredient__measurement_unit"]})')
            value = ingredient["amount"]
            p.drawString(x, y, f'{key} — {value}')
            y -= 20
        p.showPage()
        p.save()
        buffer.seek(0)
        return FileResponse(buffer,
                            as_attachment=True,
                            filename='shopping-list.pdf')

    @staticmethod
    def create_new_object(serializer, pk, request):
        data = {'user': request.user.id, 'recipe': pk}
        context = {'request': request}
        serializer = serializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @staticmethod
    def delete_object(model, pk, request):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        deleted_count = model.objects.filter(
            user=user, recipe=recipe).delete()[0]
        if not deleted_count:
            return Response(
                {'ошибка': 'Этот рецепт уже удален из списка'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True,
            methods=('POST',),
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        return self.create_new_object(FavoriteSerializer, pk, request)

    @action(detail=True,
            methods=('POST',),
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        return self.create_new_object(ShoppingCartSerializer, pk, request)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk):
        return self.delete_object(Favorites, pk, request)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk):
        return self.delete_object(ShoppingCart, pk, request)

    @action(detail=False,
            methods=('GET',),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shoppingcartrecipes__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            amount=Sum('amount')
        ).order_by('ingredient__name')
        if not ingredients:
            return Response({'Ошибка': 'Список покупок пуст'},
                            status=status.HTTP_404_NOT_FOUND)

        return self.download_file(ingredients)


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

    queryset = UserModel.objects.all()
    serializer_class = UserSerializer
    pagination_class = FoodgramPageNumberPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_permissions(self):
        if self.action == 'me':
            return (permissions.IsAuthenticated(),)
        return super().get_permissions()

    @action(detail=True,
            methods=('POST',),
            permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        get_object_or_404(UserModel, id=id)
        data = {'user': request.user.pk, 'subscription': id}
        context = {'request': request}
        serializer = SubscriptionSerializer(data=data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        subscription = get_object_or_404(UserModel, id=id)
        deleted_count = Subscription.objects.filter(
            user=request.user,
            subscription=subscription
        ).delete()[0]
        if not deleted_count:
            return Response(
                {'ошибка': 'Такой подписки не существует'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response('Вы отписались от этого пользователя',
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=False,
            methods=('GET',),
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        user = request.user
        queryset = UserModel.objects.filter(subscriptions__user=user)
        paginator = FoodgramPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = RecipesOfUserSerializer(
            page,
            many=True,
            context={'request': request}
        ).data
        return paginator.get_paginated_response(serializer)
