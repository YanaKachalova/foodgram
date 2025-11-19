from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (health,
                    TagViewSet,
                    IngredientViewSet,
                    RecipeViewSet,
                    RecipeShortLinkRedirectView,
                    MeView,
                    AvatarUpdateView,
                    SubscribeView,
                    SubscriptionsListView,)


router = DefaultRouter()
router.register("tags", TagViewSet, basename="tags")
router.register("ingredients", IngredientViewSet, basename="ingredients")
router.register("recipes", RecipeViewSet, basename="recipes")

urlpatterns = [
    path('health/', health),
    path('users/me/', MeView.as_view(), name='me'),
    path('users/me/avatar/', AvatarUpdateView.as_view(), name='avatar'),
    path('users/<int:author_id>/subscribe/',
         SubscribeView.as_view(),
         name='subscribe'),
    path('users/subscriptions/',
         SubscriptionsListView.as_view(),
         name='subscriptions'),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('s/<int:pk>/',
         RecipeShortLinkRedirectView.as_view(),
         name='recipe-short-link'),
    path('', include(router.urls)),
]
