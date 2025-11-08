from django.contrib import admin
from django.db.models import Count
from .models import (Tag, Ingredient, Recipe, RecipeTag,
                     RecipeIngredient, Favorite,
                     ShoppingCart)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'color', 'slug')
    search_fields = ('name', 'slug')
    list_filter = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    ordering = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra_line = 1
    autocomplete_fields = ('ingredient',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'favorite_count', 'pub_date')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_fav=Count('in_favorites'))

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return getattr(obj, '_fav', 0)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created',)


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe', 'created')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('created',)


@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'tag')


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe__name', 'ingredient__name')
