from django.urls import path, include
from apps.api.views import health

urlpatterns = [
    path('health/', health),
    path('users/', include('apps.users.urls', namespace='users')),
    path('recipes/', include('apps.recipes.urls')),
]

