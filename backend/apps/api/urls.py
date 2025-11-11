from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import health, TagViewSet, IngredientViewSet, RecipeViewSet


router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path('health/', health),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('', include(router.urls)),
]

