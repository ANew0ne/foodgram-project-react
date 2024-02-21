from colorfield.fields import ColorField
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model


UserModel = get_user_model()

MAX_LENGTH = 200


class Tag(models.Model):
    """Модель тэгов."""

    name = models.CharField('Название', max_length=MAX_LENGTH, unique=True)
    color = ColorField('Цвет в HEX', unique=True)
    slug = models.SlugField(
        'Уникальный слаг',
        max_length=MAX_LENGTH,
        unique=True,
    )

    class Meta:
        verbose_name = 'тэг'
        verbose_name_plural = 'Тэги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиентов."""

    name = models.CharField('Название', max_length=MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MAX_LENGTH,
    )

    class Meta:
        verbose_name = 'ингридиент'
        verbose_name_plural = 'Ингридиенты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredients',
            )
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель рецептов."""

    author = models.ForeignKey(
        UserModel,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        verbose_name='Список ингредиентов'
    )
    name = models.CharField('Название', max_length=MAX_LENGTH)
    text = models.TextField('Описание')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                1,
                'Время приготовления не может быть меньше 1 минуты'
            )
        ]
    )
    image = models.ImageField(
        'Фото рецепта',
        upload_to='recipes/images/',
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name

    def get_favorites_count(recipe):
        return Favorites.objects.filter(recipe=recipe).count()


class RecipeIngredient(models.Model):
    """Модель связи между рецептами и ингредиентами."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                1,
                'Количество не может быть меньше 1'
            )
        ]
    )

    class Meta:
        default_related_name = 'recipe_ingredient'

    def __str__(self):
        return f'{self.recipe.name}: {self.ingredient.name}'


class BaseListModel(models.Model):
    """Базовая модель для избранного и списка покупок."""

    user = models.ForeignKey(
        UserModel, on_delete=models.CASCADE, related_name='%(class)susers'
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='%(class)srecipes'
    )

    class Meta:
        abstract = True
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_%(class)s',
            )
        ]

    def __str__(self):
        return (
            f'Рецепт "{self.recipe.name}" добавлен '
            f'в {self._meta.verbose_name} пользователя {self.user.username}'
        )


class Favorites(BaseListModel):
    """Модель списка избранного."""

    class Meta(BaseListModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'


class ShoppingCart(BaseListModel):
    """Модель списка покупок."""

    class Meta(BaseListModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Список покупок'
