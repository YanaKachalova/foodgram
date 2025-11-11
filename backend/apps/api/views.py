from rest_framework import viewsets, mixins, permissions, filters as drf_filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend

from apps.recipes.models import Tag, Ingredient, Recipe
from .serializers import TagSerializer, IngredientSerializer, RecipeReadSerializer, RecipeWriteSerializer
from .filters import RecipeFilter


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok'})


class SafeMethodsOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or request.user and request.user.is_authenticated


class TagViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = None
    filter_backends = [drf_filters.SearchFilter]
    search_fields = ["^name"]


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags",
        Prefetch("ri")
    )
    permission_classes = (SafeMethodsOnly,)
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = RecipeFilter
    ordering_fields = ["created"]
    pagination_class = None

    def get_serializer_class(self):
        if self.request and self.request.method in ("POST", "PUT", "PATCH"):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save()
