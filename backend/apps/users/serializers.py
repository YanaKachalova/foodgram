# from djoser.serializers import UserCreateSerializer as
# BaseUserCreateSerializer
# from djoser.serializers import UserSerializer as BaseUserSerializer
# from rest_framework import serializers

# from apps.api.fields import Base64ImageField
# from .models import User, Follow


# class UserReadSerializer(BaseUserSerializer):
#     is_subscribed = serializers.SerializerMethodField()

#     class Meta(BaseUserSerializer.Meta):
#         model = User
#         fields = ('id',
#                   'email',
#                   'username',
#                   'first_name',
#                   'last_name',
#                   'avatar',
#                   'is_subscribed')

#     def get_is_subscribed(self, author):
#         request = self.context.get('request')
#         user = getattr(request, 'user', None)
#         if user and user.is_authenticated:
#             return author.following.filter(user_id=user.pk).exists()
#         return False


# class UserCreateSerializer(BaseUserCreateSerializer):
#     class Meta(BaseUserCreateSerializer.Meta):
#         model = User
#         fields = ('email',
#                   'username',
#                   'password',
#                   'first_name',
#                   'last_name')


# class AvatarSerializer(serializers.ModelSerializer):
#     avatar = Base64ImageField(required=False, allow_null=True)

#     class Meta:
#         model = User
#         fields = ('avatar',)


# class FollowReadSerializer(serializers.ModelSerializer):
#     id = serializers.ReadOnlyField(source='author.id')
#     email = serializers.ReadOnlyField(source='author.email')
#     username = serializers.ReadOnlyField(source='author.username')
#     first_name = serializers.ReadOnlyField(source='author.first_name')
#     last_name = serializers.ReadOnlyField(source='author.last_name')
#     avatar = serializers.ImageField(source='author.avatar', read_only=True)
#     recipes = serializers.SerializerMethodField()
#     recipes_count = serializers.IntegerField(
#         source='author.recipes.count',
#         read_only=True,
#     )

#     class Meta:
#         model = Follow
#         fields = ('id',
#                   'email',
#                   'username',
#                   'first_name',
#                   'last_name',
#                   'avatar',
#                   'recipes',
#                   'recipes_count',
#                   )

#     def get_recipes(self, obj):
#         from apps.api.serializers import RecipeShortSerializer
#         request = self.context.get('request')
#         recipes_limit = None
#         if request is not None:
#             recipes_limit = request.query_params.get('recipes_limit')

#         queryset = obj.author.recipes.all()
#         if recipes_limit is not None:
#             try:
#                 queryset = queryset[:int(recipes_limit)]
#             except (TypeError, ValueError):
#                 pass

#         return RecipeShortSerializer(queryset, many=True).data
