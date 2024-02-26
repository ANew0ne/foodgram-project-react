from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as UserAdminModel
from django.contrib.auth.models import Group

from users.models import Subscription

UserModel = get_user_model()

admin.site.empty_value_display = 'пусто'
admin.site.unregister(Group)


@admin.register(UserModel)
class UserAdmin(UserAdminModel):
    """Административный класс для управления пользователями."""

    list_display = (
        'username',
        'email',
        'is_active',
        'first_name',
        'last_name',
    )
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Административный класс для управления подписками."""

    list_display = (
        'user',
        'subscription'
    )
    search_fields = ('user',)
    empty_value_display = '-пусто-'
