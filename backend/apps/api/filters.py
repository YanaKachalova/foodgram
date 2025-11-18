import django_filters as filters

from apps.recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.NumberFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.filters.NumberFilter(
        method='filter_is_in_cart')

    class Meta:
        model = Recipe
        fields = ('author',
                  'tags',
                  'name')

    def filter_is_favorited(self, queryset, name, filter_value):
        if filter_value is None or int(filter_value) == 0:
            return queryset
        user = self.request.user
        return queryset.filter(in_favorites__user_id=user.pk)

    def filter_is_in_cart(self, queryset, name, filter_value):
        if filter_value is None or int(filter_value) == 0:
            return queryset
        user = self.request.user
        return queryset.filter(in_carts__user_id=user.pk)


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)
