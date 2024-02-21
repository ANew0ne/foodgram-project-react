from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


EMAIL_MAX_LENGTH = 254
STRING_MAX_LENGTH = 150


class FoodgramUser(AbstractUser):
    """Модель пользователя."""

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=EMAIL_MAX_LENGTH,
        unique=True
    )
    username = models.CharField(
        'Юзернейм',
        max_length=STRING_MAX_LENGTH,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    password = models.CharField('Пароль', max_length=STRING_MAX_LENGTH)
    first_name = models.CharField('Имя', max_length=STRING_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=STRING_MAX_LENGTH)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('date_joined', 'username')


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик'
    )
    subscription = models.ForeignKey(
        FoodgramUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписки'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscription'],
                name='unique_user_subscription'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('subscription')),
                name='prevent_self_subscription'
            )
        ]

    def __str__(self):
        return (
            f'{self.user.username} на {self.subscription.username}'
        )
