from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower


User = settings.AUTH_USER_MODEL


class Tag(models.Model):
    name = models.CharField(max_length=64,
                            unique=True,
                            verbose_name='Название')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='Слаг')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128,
                            verbose_name='Название')
    measurement_unit = models.CharField(max_length=32,
                                        verbose_name='Единица измерения')

    class Meta:
        constraints = [
            UniqueConstraint(fields=('name', 'measurement_unit'),
                             name='unique_ingredient'),
        ]
        indexes = [
            models.Index(Lower('name'), name='ingredient_name_lower_idx'),
        ]
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE,
                               verbose_name='Автор')
    name = models.CharField(max_length=256, verbose_name='Название')
    image = models.ImageField(upload_to='recipes/', verbose_name='Фото')
    text = models.TextField(verbose_name='Описание')
    cooking_time = models.PositiveIntegerField(validators=[
        MinValueValidator(1, message='Время не может быть меньше 1 минуты'),
        MaxValueValidator(1440, message='Время больше 1440 минут'), ],
        help_text='В минутах',
        verbose_name='Время готовки')
    tags = models.ManyToManyField('Tag',
                                  through='RecipeTag',
                                  related_name='recipes',
                                  verbose_name='Теги')
    ingredients = models.ManyToManyField('Ingredient',
                                         through='RecipeIngredient',
                                         related_name='recipes',
                                         verbose_name='Ингредиенты')
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        ordering = ('-pub_date',)
        indexes = (models.Index(fields=('-pub_date',)),)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe,
                               on_delete=models.CASCADE,
                               verbose_name='рецепт')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, verbose_name='тег')

    class Meta:
        constraints = [
            UniqueConstraint(fields=('recipe', 'tag'),
                             name='unique_recipe_tag'),
        ]
        verbose_name = 'Тег рецепта'
        verbose_name_plural = 'Теги рецепта'

    def __str__(self):
        return f'{self.recipe} — {self.tag}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               related_name='recipe_ingredients',
                               on_delete=models.CASCADE,
                               verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE,
                                   verbose_name='Ингредиент')
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1)],
                                         verbose_name='Количество')

    class Meta:
        constraints = [
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_recipe_ingredient'),
        ]
        verbose_name = 'Ингедиент для рецепта'
        verbose_name_plural = 'Ингедиенты для рецепта'

    def __str__(self):
        return f'{self.ingredient} × {self.amount} для {self.recipe}'


class Favorite(models.Model):
    user = models.ForeignKey(User,
                             related_name='favorites',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               related_name='in_favorites',
                               on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_favorite'),
        ]
        ordering = ('-created',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} — {self.recipe}'


class ShoppingCart(models.Model):
    user = models.ForeignKey(User,
                             related_name='cart',
                             on_delete=models.CASCADE)
    recipe = models.ForeignKey(Recipe,
                               related_name='in_carts',
                               on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=('user', 'recipe'),
                             name='unique_cart_item'),
        ]
        ordering = ('-created',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'

    def __str__(self):
        return f'{self.user} — {self.recipe}'
