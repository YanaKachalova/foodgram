from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from djoser.serializers import (UserSerializer as BaseUserSerializer,
                                UserCreateSerializer)

from apps.recipes.models import (Tag,
                                 Ingredient,
                                 Recipe,
                                 RecipeIngredient,
                                 Favorite,
                                 ShoppingCart)
from apps.users.models import Follow
from .fields import Base64ImageField


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientAmountWrite(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }


class UserReadSerializer(BaseUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'avatar',
                  'is_subscribed')

    def get_is_subscribed(self, author):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return (
            user
            and user.is_authenticated
            and author.following.filter(user_id=user.pk).exists()) or False


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients',
        many=True
    )
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def _get_user(self):
        request = self.context.get('request')
        return getattr(request, 'user', None) if request else None

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return recipe.in_favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return recipe.in_carts.filter(user=user).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountWrite(many=True,
                                        write_only=True,
                                        allow_empty=False)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True
    )
    image = Base64ImageField()

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

        # Проверка на дублирование ингредиентов, их наличие
        seen = set()
        for item in ingredients:
            ingredient_id = item.get('id')
            if ingredient_id in seen:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты не должны дублироваться.'})
            seen.add(ingredient_id)
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно указать хотя бы один ингредиент.'
            })

        # Проверка сузествования ингредиента
        ingredient_ids = [item.get('id') for item in ingredients]
        existing_ids = set(
            Ingredient.objects
            .filter(id__in=ingredient_ids)
            .values_list('id', flat=True)
        )
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError({
                'ingredients': 'Указаны несуществующие ингредиенты.'
            })

        # Проверка на наличие тегов и их дублирование
        tags = attrs.get('tags') or []
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно указать хотя бы один тег.'
            })

        tag_ids = [tag.id for tag in tags]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError({
                'tags': 'Теги не должны дублироваться.'
            })

        # Проверка на время готовки >= 1 минут
        cooking_time = attrs.get('cooking_time')
        if cooking_time is not None and cooking_time < 1:
            raise serializers.ValidationError({
                'cooking_time': 'Время готовки должно быть больше 1 минуты.'
            })
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
        recipe_ingredients = []
        for item in ingredients:
            ingredient = ing_map[item['id']]
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient,
                    amount=item['amount'],
                ))
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        author = self.context['request'].user
        data = dict(validated_data, author=author)
        recipe = Recipe.objects.create(**data)
        self._set_m2m(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        instance = super().update(instance, validated_data)

        if tags is None and ingredients is None:
            return
        if tags is None:
            tags_data = instance.tags.all()
        else:
            tags_data = tags
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


class ShoppingCartSerializer(FavoriteSerializer):
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


class FollowReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    email = serializers.ReadOnlyField(source='author.email')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    avatar = serializers.ImageField(source='author.avatar', read_only=True)

    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='author.recipes.count',
        read_only=True,
    )

    class Meta:
        model = Follow
        fields = ('id',
                  'email',
                  'username',
                  'first_name',
                  'last_name',
                  'avatar',
                  'is_subscribed',
                  'recipes',
                  'recipes_count',
                  )

    def get_is_subscribed(self, follow):
        request = self.context.get('request')
        user = request.user
        author = follow.author
        return (
            user and user.is_authenticated
            and author.following.filter(user=user).exists()
        )


    def get_recipes(self, follow):
        request = self.context.get('request')
        queryset = follow.author.recipes.all()

        try:
            limit = int(request.query_params.get('recipes_limit'))
            queryset = queryset[:limit]
        except (TypeError, ValueError):
            pass

        return RecipeShortSerializer(queryset, many=True).data


class FollowCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Follow
        fields = ()

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        author = self.context['author']

        if user is None or not user.is_authenticated:
            raise serializers.ValidationError('Требуется авторизация.')

        if author == user:
            raise serializers.ValidationError('Нельзя подписаться на себя.')

        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError('Уже подписаны.')

        return Follow.objects.create(user=user, author=author)
