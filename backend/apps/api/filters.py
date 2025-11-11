import django_filters as df

from apps.recipes.models import Recipe, Tag


class RecipeFilter(df.FilterSet):
    tags = df.CharFilter(method="filter_tags")
    author = df.NumberFilter(field_name="author__id")
    is_favorited = df.BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = df.BooleanFilter(method="filter_is_in_cart")

    class Meta:
        model = Recipe
        fields = ("author",)

    def filter_tags(self, queryset, name, value):
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return queryset
        return queryset.filter(tags__slug__in=slugs).distinct()

    def filter_is_favorited(self, qs, name, value):
        user = self.request.user
        if user.is_anonymous:
            return qs.none() if value else qs
        return qs.filter(in_favorites__user=user).distinct() if value else qs.exclude(in_favorites__user=user)

    def filter_is_in_cart(self, qs, name, value):
        user = self.request.user
        if user.is_anonymous:
            return qs.none() if value else qs
        return qs.filter(in_carts__user=user).distinct() if value else qs.exclude(in_carts__user=user)
