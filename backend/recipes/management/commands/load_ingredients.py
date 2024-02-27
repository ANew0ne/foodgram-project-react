import json

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open('data/ingredients.json', 'rb') as f:
            data = json.load(f)
        ingredients = []
        for ingredient_data in data:
            ingredients.append(
                Ingredient(
                    name=ingredient_data['name'],
                    measurement_unit=ingredient_data['measurement_unit'],
                )
            )
        Ingredient.objects.bulk_create(ingredients, ignore_conflicts=True)
