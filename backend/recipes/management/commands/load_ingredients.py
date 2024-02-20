import json
from recipes.models import Ingredient
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):

        with open('data/ingredients.json', 'rb') as f:
            data = json.load(f)
            for ingredient_data in data:
                Ingredient.objects.get_or_create(
                    name=ingredient_data['name'],
                    measurement_unit=ingredient_data['measurement_unit'],
                )
