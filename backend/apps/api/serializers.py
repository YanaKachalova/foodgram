from rest_framework import serializers

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
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientAmountWrite(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=8, decimal_places=2)


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    author = UserReadSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id","author","name","text","image","cooking_time",
            "tags","ingredients","pub_date","is_favorited","is_in_shopping_cart"
        )

    def _get_user(self):
        req = self.context.get("request")
        return getattr(req, "user", None) if req else None

    def get_ingredients(self, obj):
        rows = obj.recipe_ingredients.select_related("ingredient")
        data = []
        for row in rows:
            ing = getattr(row, "ingredient", None)
            data.append({
                "id": row.ingredient_id,
                "name": getattr(ing, "name", None),
                "measurement_unit": getattr(ing, "measurement_unit", None),
                "amount": row.amount,
            })
        return data

    def get_is_favorited(self, obj):
        user = self._get_user()
        return False if not user or user.is_anonymous else Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self._get_user()
        return False if not user or user.is_anonymous else ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = IngredientAmountWrite(many=True, write_only=True)
    image = Base64ImageField(required=False)

    class Meta:
        model = Recipe
        fields = ("name","text","image","cooking_time","tags","ingredients")

    def validate(self, attrs):
        tags = attrs.get("tags") or []
        if not tags:
            raise serializers.ValidationError({"tags": "Нужно указать хотя бы один тег."})
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({"tags": "Теги не должны повторяться."})

        ings = attrs.get("ingredients") or []
        if not ings:
            raise serializers.ValidationError({"ingredients": "Нужен хотя бы один ингредиент."})
        seen = set()
        for item in ings:
            iid = item["id"]
            if iid in seen:
                raise serializers.ValidationError({"ingredients": "Ингредиенты не должны дублироваться."})
            seen.add(iid)
            if item["amount"] <= 0:
                raise serializers.ValidationError({"ingredients": f"Количество для id={iid} должно быть > 0."})
        return attrs

    def _set_m2m(self, recipe, tags, ingredients):
        recipe.tags.set(Tag.objects.filter(slug__in=tags))
        RecipeIngredient.objects.filter(recipe=recipe).delete()
        rows = []
        ing_map = {i.id: i for i in Ingredient.objects.filter(id__in=[x["id"] for x in ingredients])}
        for item in ingredients:
            rows.append(RecipeIngredient(
                recipe=recipe, ingredient=ing_map[item["id"]], amount=item["amount"]
            ))
        RecipeIngredient.bulk_create(rows) if hasattr(RecipeIngredient, 'bulk_create') else RecipeIngredient.objects.bulk_create(rows)

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(author=self.context["request"].user, **validated_data)
        self._set_m2m(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)

        if tags is None and ingredients is None:
            return instance

        if tags is None:
            tags_data = [t.slug for t in instance.tags.all()]
        else:
            tags_data = tags

        if ingredients is None:
            ingredients_data = [
                {"id": ri.ingredient_id, "amount": ri.amount}
                for ri in instance.recipe_ingredients.all()
            ]
        else:
            ingredients_data = ingredients

        self._set_m2m(instance, tags_data, ingredients_data)
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
