from django.urls import path

from .views import (MeView,
                    AvatarUpdateView,
                    SubscribeView,
                    SubscriptionsListView)


app_name = 'users'

urlpatterns = [
    path('me/',
         MeView.as_view(),
         name='me'),
    path('me/avatar/',
         AvatarUpdateView.as_view(),
         name='avatar'),
    path('<int:author_id>/subscribe/',
         SubscribeView.as_view(),
         name='subscribe'),
    path('subscriptions/',
         SubscriptionsListView.as_view(),
         name='subscriptions'),
]
