import csv
from django.core.management.base import BaseCommand, CommandError

from apps.recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV'

    def add_arguments(self, parser):
        parser.add_argument('--path', default='data/ingredients.csv')

    def handle(self, *args, **opts):
        path = opts['path']
        try:
            file = open(path, encoding='utf-8')
        except FileNotFoundError as err:
            raise CommandError(f'Файл не найден: {path}') from err

        with file:
            reader = csv.reader(file, delimiter=',')
            created = 0
            for row in reader:
                if len(row) < 2:
                    continue

                name = row[0].strip()
                measurement_unit = row[1].strip()
                _, is_created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=measurement_unit,)
                created += int(is_created)

        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты: создано={created}.'
        ))
