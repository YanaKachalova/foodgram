from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from apps.api.views import health


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/users/', include('apps.users.urls', namespace='users')),
]
