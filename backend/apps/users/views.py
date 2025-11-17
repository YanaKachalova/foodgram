from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, Follow
from apps.api.serializers import (AvatarSerializer,
                                  UserReadSerializer,
                                  FollowReadSerializer)


class MeView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserReadSerializer

    def get_object(self):
        return self.request.user


class AvatarUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = AvatarSerializer(instance=request.user,
                                      data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        serializer = AvatarSerializer(instance=request.user,
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        author = get_object_or_404(User, id=id)
        if author == request.user:
            return Response({'errors': 'Нельзя подписаться на себя!'},
                            status=400)
        follow_object, created = Follow.objects.get_or_create(
            user=request.user,
            author=author)
        if not created:
            return Response({'errors': 'Уже подписаны.'}, status=400)
        serializer = FollowReadSerializer(follow_object,
                                          context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, id):
        author = get_object_or_404(User, id=id)
        deleted, _ = Follow.objects.filter(user=request.user,
                                           author=author).delete()
        if not deleted:
            return Response({'errors': 'Подписки не было.'}, status=400)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionsListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowReadSerializer

    def get_queryset(self):
        return (Follow.objects
                .filter(user=self.request.user)
                .select_related('author')
                )
