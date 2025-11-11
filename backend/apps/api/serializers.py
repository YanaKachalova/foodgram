from rest_framework import serializers

from apps.recipes.models import (Tag,
                                 Ingredient,
                                 Recipe,
                                 RecipeIngredient,
                                 Favorite,
                                 ShoppingCart)
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
    author = serializers.SerializerMethodField()
    ingredients = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id","author","name","text","image","cooking_time",
            "tags","ingredients","created","is_favorited","is_in_shopping_cart"
        )

    def get_author(self, obj):
        u = obj.author
        return {"id": u.id, "username": u.username}

    def get_ingredients(self, obj):
        rows = obj.ri.select_related("ingredient")
        return [
            {
                "id": r.ingredient_id,
                "name": r.ingredient.name,
                "measurement_unit": r.ingredient.measurement_unit,
                "amount": str(r.amount),
            }
            for r in rows
        ]

    def get_is_favorited(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return Favorite.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeWriteSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.SlugField(), write_only=True)
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
        from apps.recipes.models import Tag, Ingredient, RecipeIngredient
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
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tags is not None or ingredients is not None:
            self._set_m2m(instance, tags or [t.slug for t in instance.tags.all()], ingredients or [
                {"id": ri.ingredient_id, "amount": ri.amount} for ri in instance.ri.all()
            ])
        return instance

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
