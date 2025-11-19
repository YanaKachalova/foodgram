from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает:
    - смотреть всем (GET/HEAD/OPTIONS)
    - а изменять или удалять рецепт - только автору
    """

    def has_object_permission(self, request, view, obj):
        # Просмотр разрешён всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Изменение / удаление — только автору
        return obj.author == request.user
