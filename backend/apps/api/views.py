import io
from rest_framework import (viewsets,
                            mixins,
                            status,
                            permissions,
                            filters as drf_filters)
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db.models import Exists, OuterRef, BooleanField, Value
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.urls import reverse

from apps.recipes.models import (Tag,
                                 Ingredient,
                                 Recipe,
                                 Favorite,
                                 ShoppingCart,
                                 RecipeIngredient)
from .serializers import (TagSerializer,
                          IngredientSerializer,
                          RecipeReadSerializer,
                          RecipeWriteSerializer,
                          RecipeShortSerializer,
                          FavoriteSerializer,
                          ShoppingCartSerializer)
from .filters import RecipeFilter, IngredientFilter


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    return Response({'status': 'ok'})


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class IngredientViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter)
    filterset_class = RecipeFilter
    ordering_fields = ('pub_date',)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        user = self.request.user

        if user.is_authenticated:
            favorites_subquery = Favorite.objects.filter(
                user=user,
                recipe=OuterRef('pk'),
            )
            cart_subquery = ShoppingCart.objects.filter(
                user=user,
                recipe=OuterRef('pk'),
            )
            queryset = queryset.annotate(
                is_favorited=Exists(favorites_subquery),
                is_in_shopping_cart=Exists(cart_subquery),
            )
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()),
            )
        return queryset

    def get_serializer_class(self):
        if self.action in {
            'favorite',
            'remove_favorite',
            'shopping_cart',
            'delete_from_shopping_cart',
        }:
            return RecipeShortSerializer

        if self.request.method in ('POST', 'PUT', 'PATCH'):
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
        """Добавление рецепта в избранное и его удаление."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={'recipe': recipe.id},
                context={'request': request},)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            out_serializer = self.get_serializer(recipe)
            return Response(out_serializer.data,
                            status=status.HTTP_201_CREATED)

        deleted_count, _ = Favorite.objects.filter(
            user=user,
            recipe=recipe,).delete()
        if deleted_count == 0:
            raise NotFound('Рецепта нет в избранном.')

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,),
        url_path='shopping_cart',
        url_name='shopping_cart',
    )
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в список покупок и его удаление."""
        recipe = self.get_object()
        user = request.user

        if request.method == 'POST':
            context = self.get_serializer_context()
            serializer = ShoppingCartSerializer(
                data={'recipe': recipe.id},
                context=context,)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            out_serializer = self.get_serializer(recipe)
            return Response(out_serializer.data,
                            status=status.HTTP_201_CREATED)

        cart_qs = ShoppingCart.objects.filter(user=user, recipe=recipe)
        if not cart_qs.exists():
            raise NotFound('Рецепта нет в списке покупок.')
        cart_qs.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
    )
    def download_shopping_cart(self, request):
        """Выгрузка списка покупок пользователя."""
        user = request.user
        recipes_in_cart = Recipe.objects.filter(in_carts__user=user)

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
            ingredient_key = (name, unit)
            shopping_dict[ingredient_key] = (
                shopping_dict.get(ingredient_key, 0)
                + amount)

        lines = ['Список покупок:'] + [
            f'{name} ({unit}) — {amount}'
            for (name, unit), amount in shopping_dict.items()
        ]

        content = '\n'.join(lines)
        file_stream = io.BytesIO(content.encode('utf-8'))
        return FileResponse(
            file_stream,
            as_attachment=True,
            filename='shopping_cart.txt',
            content_type='text/plain; charset=utf-8',
        )

    @action(
        detail=True,
        permission_classes=[AllowAny],
        url_path='get-link',
        url_name='get_link',
    )
    def get_short_link(self, request, pk=None):
        """Возвращает короткую ссылку на страницу рецепта."""
        recipe = self.get_object()
        short_path = reverse('recipe-short-link', args=[recipe.pk])
        short_link = request.build_absolute_uri(short_path)
        return Response({'short-link': short_link})
