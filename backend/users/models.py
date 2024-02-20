from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


EMAIL_MAX_LENGTH = 254
STRING_MAX_LENGTH = 150


class CustomUser(AbstractUser):
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
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=('Имя пользователя может содержать '
                         'только буквы, цифры, _, . , @ и -')
            )
        ]
    )
    password = models.CharField('Пароль', max_length=STRING_MAX_LENGTH)
    first_name = models.CharField('Имя', max_length=STRING_MAX_LENGTH)
    last_name = models.CharField('Фамилия', max_length=STRING_MAX_LENGTH)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('date_joined',)


class Subscription(models.Model):
    """Модель подписок."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Подписчик'
    )
    subscription = models.ForeignKey(
        CustomUser,
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
