from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .models import Follow
from apps.api.serializers import (AvatarSerializer,
                                  UserReadSerializer,
                                  FollowReadSerializer,
                                  FollowCreateSerializer)


User = get_user_model()


class MeView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserReadSerializer

    def get_object(self):
        return self.request.user


class AvatarUpdateView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def put(self, request):
        serializer = self.get_serializer(instance=request.user,
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        serializer = self.get_serializer(instance=request.user,
                                         data=request.data,
                                         partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request):
        user = request.user
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        serializer = FollowCreateSerializer(
            data={'author': author.id},
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        follow = serializer.save()
        read_serializer = FollowReadSerializer(
            follow,
            context={'request': request},
        )
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, author_id):
        author = get_object_or_404(User, id=author_id)
        deleted, _ = request.user.following.filter(author=author).delete()
        if not deleted:
            raise ValidationError('Подписки не было.')
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = FollowReadSerializer

    def get_queryset(self):
        return (Follow.objects
                .filter(user=self.request.user)
                .select_related('author')
                )
