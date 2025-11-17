import csv
from django.core.management.base import BaseCommand, CommandError

from apps.recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка ингредиентов из CSV'

    def add_arguments(self, parser):
        parser.add_argument('--path', default='data/ingredients.csv')

    def handle(self, *args, **opts):
        path = opts['path']
        created = skipped = 0
        try:
            file = open(path, encoding='utf-8')
        except FileNotFoundError as err:
            raise CommandError(f'Файл не найден: {path}') from err

        with file:
            reader = csv.DictReader(file)
            for row in reader:
                _, is_created = Ingredient.objects.get_or_create(
                    name=row['name'].strip(),
                    measurement_unit=row['measurement_unit'].strip(),)
                created += int(is_created)
                skipped += int(not is_created)

        self.stdout.write(self.style.SUCCESS(
            f'Ингредиенты: создано={created}, пропущено={skipped}'
        ))
