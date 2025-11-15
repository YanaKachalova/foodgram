from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.db.models.functions import Lower


User = settings.AUTH_USER_MODEL


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=7, unique=True, help_text='#RRGGBB')
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=128)
    measurement_unit = models.CharField(max_length=32)

    class Meta:
        constraints = [
            UniqueConstraint(fields=('name', 'measurement_unit'),
                             name='unique_ingredient'),
        ]
        indexes = [
            models.Index(Lower('name'), name='ingredient_name_lower_idx'),
        ]
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}'


class Recipe(models.Model):
    author = models.ForeignKey(User,
                               related_name='recipes',
                               on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    image = models.ImageField(upload_to='recipes/')
    text = models.TextField()
    cooking_time = models.PositiveIntegerField(help_text='В минутах')
    tags = models.ManyToManyField('Tag',
                                  through='RecipeTag',
                                  related_name='recipes')
    ingredients = models.ManyToManyField('Ingredient',
                                         through='RecipeIngredient',
                                         related_name='recipes')
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-pub_date',)
        indexes = [models.Index(fields=['-pub_date'])]

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            UniqueConstraint(fields=('recipe', 'tag'),
                             name='unique_recipe_tag'),
        ]

    def __str__(self):
        return f'{self.recipe} — {self.tag}'


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe,
                               related_name='recipe_ingredients',
                               on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient,
                                   on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=('recipe', 'ingredient'),
                             name='unique_recipe_ingredient'),
        ]

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

    def __str__(self):
        return f'{self.user} — {self.recipe}'
