from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include
from apps.api.views import health


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.api.urls')),
]
