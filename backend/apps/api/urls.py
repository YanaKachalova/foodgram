from django.urls import path, include
from apps.api.views import health

urlpatterns = [
    path('health/', health),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/', include('apps.users.urls', namespace='users')),
    path('recipes/', include('apps.recipes.urls')),
]

