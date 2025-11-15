import django_filters as filters

from apps.recipes.models import Recipe, Tag, Ingredient


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.NumberFilter(method="filter_is_favorited")
    is_in_shopping_cart = filters.NumberFilter(method="filter_is_in_cart")
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Recipe
        fields = ("author", "tags", "is_favorited", "is_in_shopping_cart", "name")

    def filter_is_favorited(self, queryset, name, value):
        if value is None:
            return queryset
        if int(value) == 0:
            return queryset
        user = getattr(self.request, "user", None)
        if user is None or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(in_favorites__user=user).distinct()

    def filter_is_in_cart(self, queryset, name, value):
        if value is None:
            return queryset
        if int(value) == 0:
            return queryset
        user = getattr(self.request, 'user', None)
        if user is None or not user.is_authenticated:
            return queryset.none()
        return queryset.filter(in_carts__user=user).distinct()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
