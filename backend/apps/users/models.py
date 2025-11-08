from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q, UniqueConstraint


class User(AbstractUser):
    email = models.EmailField('email address', unique=True)
    username = models.CharField(
        max_length=50,
        unique=True,
        validators=[RegexValidator(r'^[\w.@+-]+$', 'Недопустимые символы в юзернейме')],
    )
    # Добавить аватар в спринте 2

    class Meta:
        ordering = ('id',)

    def __str__(self):
        return self.get_username()


class Follow(models.Model):
    user = models.ForeignKey(
        User, related_name='follower', on_delete=models.CASCADE, verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User, related_name='following', on_delete=models.CASCADE, verbose_name='Автор'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=('user', 'author'), name='unique_follow'),
            models.CheckConstraint(check=~Q(user=models.F('author')), name='no_self_follow'),
        ]
        ordering = ('-created',)

    def __str__(self):
        return f'{self.user} → {self.author}'
