from django.contrib import admin
from django.db.models import Count

from .models import (Tag, Ingredient, Recipe, RecipeTag,
                     RecipeIngredient, Favorite,
                     ShoppingCart)


FAVORITE_RECIPE_REL = (Favorite._meta.get_field('recipe')
                       .remote_field.get_accessor_name())


class RecipeIngredientInline(admin.TabularInline):
    """Позволяет редактировать ингредиенты прямо в рецепте."""

    model = RecipeIngredient
    extra = 0
    autocomplete_fields = ('ingredient',)


class RecipeTagInline(admin.TabularInline):
    """Позволяет выбирать теги прямо в рецепте."""

    model = RecipeTag
    extra = 0
    autocomplete_fields = ('tag',)


class FavoritedFilter(admin.SimpleListFilter):
    """Фильтр "Есть в избранном"."""

    title = 'В избранном'
    parameter_name = 'in_favorites'

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return (queryset
                    .filter(**{f'{FAVORITE_RECIPE_REL}__isnull': False})
                    .distinct())
        else:
            return (queryset
                    .filter(**{f'{FAVORITE_RECIPE_REL}__isnull': True})
                    .distinct())
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorite_count', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('author', 'tags', FavoritedFilter)
    inlines = (RecipeIngredientInline, RecipeTagInline)
    autocomplete_fields = ('author',)
    date_hierarchy = 'pub_date'
    ordering = ('-pub_date',)
    list_select_related = ('author',)

    def get_queryset(self, request):
        """Добавляет аннотацию числа добавлений в избранное."""
        queryset = super().get_queryset(request)
        return (queryset
                .annotate(_fav_count=Count(FAVORITE_RECIPE_REL,
                                           distinct=True)))

    @admin.display(description='В избранном', ordering='_fav_count')
    def favorite_count(self, recipe):
        return recipe._fav_count


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    autocomplete_fields = ('user', 'recipe')
