# Generated by Django 3.2.3 on 2024-02-21 14:42

import colorfield.fields
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import re


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Favorites',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'избранное',
                'verbose_name_plural': 'Избранное',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Ingredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('measurement_unit', models.CharField(max_length=200, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'ингридиент',
                'verbose_name_plural': 'Ингридиенты',
            },
        ),
        migrations.CreateModel(
            name='Recipe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('text', models.TextField(verbose_name='Описание')),
                ('cooking_time', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Время приготовления не может быть меньше 1 минуты')], verbose_name='Время приготовления (в минутах)')),
                ('image', models.ImageField(upload_to='recipes/images/', verbose_name='Фото рецепта')),
                ('pub_date', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Дата публикации')),
            ],
            options={
                'verbose_name': 'рецепт',
                'verbose_name_plural': 'Рецепты',
                'ordering': ['-pub_date'],
                'default_related_name': 'recipes',
            },
        ),
        migrations.CreateModel(
            name='RecipeIngredient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, 'Количество не может быть меньше 1')], verbose_name='Количество')),
            ],
            options={
                'default_related_name': 'recipe_ingredient',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Название')),
                ('color', colorfield.fields.ColorField(default='#FFFFFF', image_field=None, max_length=25, samples=None, verbose_name='Цвет в HEX')),
                ('slug', models.SlugField(max_length=200, unique=True, validators=[django.core.validators.RegexValidator(flags=re.RegexFlag['IGNORECASE'], message='Слаг может содержать только буквы, цифры, _ и -', regex='^[-a-zA-Z0-9_]+$')], verbose_name='Уникальный слаг')),
            ],
            options={
                'verbose_name': 'тэг',
                'verbose_name_plural': 'Тэги',
                'default_related_name': 'tags',
            },
        ),
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('recipe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shoppingcartrecipes', to='recipes.recipe')),
            ],
            options={
                'verbose_name': 'список покупок',
                'verbose_name_plural': 'Список покупок',
                'abstract': False,
            },
        ),
    ]
