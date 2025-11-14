from rest_framework import viewsets, mixins, status, permissions, filters as drf_filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse

from apps.recipes.models import (
                                 Tag,
                                 Ingredient,
                                 Recipe,
                                 Favorite,
                                 ShoppingCart,
                                 RecipeIngredient
                                 )
from .serializers import (
                          TagSerializer,
                          IngredientSerializer,
                          RecipeReadSerializer,
                          RecipeWriteSerializer,
                          RecipeShortSerializer
                          )
from .filters import RecipeFilter, IngredientFilter


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
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = [DjangoFilterBackend, drf_filters.OrderingFilter]
    filterset_class = RecipeFilter
    ordering_fields = ["pub_date"]

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return RecipeWriteSerializer
        return RecipeReadSerializer


    def perform_create(self, serializer):
        serializer.save()


    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite',
        url_name='favorite',
    )
    def favorite(self, request, pk=None):
        """Добавление или удаление рецепта в избранное."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        favorite_qs = Favorite.objects.filter(user=user, recipe=recipe)
        if not favorite_qs.exists():
            return Response(
                {'detail': 'Рецепта нет в избранном.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            favorite_qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта в/из лист(а) закупок."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже в списке покупок.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        cart_qs = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not cart_qs.exists():
            return Response(
                {'detail': 'Рецепта нет в списке покупок.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            cart_qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок по корзине пользователя. """
        user = request.user

        # Все рецепты, которые пользователь добавил в корзину
        recipes_in_cart = Recipe.objects.filter(in_carts__user=user)
        if not recipes_in_cart.exists():
            return Response(
                {'detail': 'Список покупок пуст.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipe_ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=recipes_in_cart)
            .select_related('ingredient')
        )

        shopping_dict = {}
        for recipe_ingredient in recipe_ingredients:
            name = recipe_ingredient.ingredient.name
            unit = recipe_ingredient.ingredient.measurement_unit
            amount = recipe_ingredient.amount
            key = (name, unit)
            shopping_dict[key] = shopping_dict.get(key, 0) + amount

        lines = ['Список покупок:']
        for (name, unit), amount in shopping_dict.items():
            lines.append(f'{name} ({unit}) — {amount}')

        content = '\n'.join(lines)
        response = HttpResponse(
            content,
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_cart.txt"'
        )
        return response
