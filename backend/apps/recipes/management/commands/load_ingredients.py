import csv
from django.core.management.base import BaseCommand, CommandError
from apps.recipes.models import Ingredient

class Command(BaseCommand):
    help = "Загрузка ингредиентов из CSV"

    def add_arguments(self, parser):
        parser.add_argument("--path", default="data/ingredients.csv")

    def handle(self, *args, **opts):
        path = opts["path"]
        created = skipped = 0
        try:
            with open(path, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    _, is_created = Ingredient.objects.get_or_create(
                        name=row["name"].strip(),
                        measurement_unit=row["measurement_unit"].strip(),
                    )
                    created += int(is_created)
                    skipped += int(not is_created)
        except FileNotFoundError:
            raise CommandError(f"Файл не найден: {path}")
        self.stdout.write(self.style.SUCCESS(
            f"Ингредиенты: создано={created}, пропущено={skipped}"
        ))
