from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.recipes.models import (Tag,
                                 Ingredient,
                                 Recipe,
                                 RecipeIngredient,
                                 Favorite,
                                 ShoppingCart)
from apps.users.serializers import UserReadSerializer
from .fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountWrite(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'text',
            'image',
            'cooking_time',
            'tags',
            'ingredients',
            'pub_date',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def _get_user(self):
        req = self.context.get('request')
        return getattr(req, 'user', None) if req else None

    def get_ingredients(self, recipe):
        rows = recipe.recipe_ingredients.select_related('ingredient')
        return [
            {
                'id': row.ingredient_id,
                'name': row.ingredient.name,
                'measurement_unit': row.ingredient.measurement_unit,
                'amount': row.amount,
            }
            for row in rows
        ]


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountWrite(many=True, write_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ('name',
                  'text',
                  'image',
                  'cooking_time',
                  'tags',
                  'ingredients')
        extra_kwargs = {
            'tags': {'allow_empty': False},
        }

    def validate(self, attrs):
        ingredients = attrs.get('ingredients') or []
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужен хотя бы один ингредиент.'})
        seen = set()
        for item in ingredients:
            ingredient_id = item.get('id')
            if ingredient_id in seen:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты не должны дублироваться.'})
            seen.add(ingredient_id)
        return attrs

    def _set_m2m(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        ing_map = {
            ingredient.id: ingredient
            for ingredient in Ingredient.objects.filter(
                id__in=[item['id'] for item in ingredients]
            )
        }
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ing_map[item['id']],
                amount=item['amount'],
            )
            for item in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = super().create(validated_data)
        self._set_m2m(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)
        if tags is None and ingredients is None:
            return instance
        tags_data = (
            [tag.slug for tag in instance.tags.all()]
            if tags is None
            else tags)

        if ingredients is None:
            ingredients_data = [
                {'id': ri.ingredient_id, 'amount': ri.amount}
                for ri in instance.recipe_ingredients.all()
            ]
        else:
            ingredients_data = ingredients

        self._set_m2m(instance, tags_data, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    """Короткое представление рецепта для избранного и корзины."""

    image = Base64ImageField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для списка избранного."""

    class Meta:
        model = Favorite
        fields = ('recipe',)

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']

        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError({'detail': 'Рецепт уже в избранном.'})

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return Favorite.objects.create(user=user, **validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для списка покупок."""

    class Meta:
        model = ShoppingCart
        fields = ('recipe',)

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = attrs['recipe']

        if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError({'detail': 'Рецепт уже в списке покупок.'})

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        return ShoppingCart.objects.create(user=user, **validated_data)
