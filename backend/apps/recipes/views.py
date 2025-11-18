from urllib.parse import urljoin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from .models import Recipe


class RecipeShortLinkRedirectView(View):
    """Редирект с короткой ссылки на страницу рецепта."""

    def get(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk)
        return redirect(request.build_absolute_uri(f'/recipes/{recipe.pk}/'))
