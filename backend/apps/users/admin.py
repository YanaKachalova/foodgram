from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Follow

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'username', 'email', "first_name", "last_name", 'is_staff', 'is_active')
    search_fields = ('username', 'email', "first_name", "last_name")
    list_filter = ('is_staff', 'is_active')

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'created')
    search_fields = ('user__username', 'author__username')
    list_filter = ('created',)
