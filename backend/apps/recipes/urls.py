from django.urls import path

from . import views


app_name = 'recipes'

# Заглушка
urlpatterns = [
    path('ping/', views.ping, name='ping'),
]

