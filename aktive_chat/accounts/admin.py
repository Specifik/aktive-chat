from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Subscription, UserSettings

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'username', 'account_type', 'is_email_verified', 'is_staff')
    list_filter = ('account_type', 'is_email_verified', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Account Info', {'fields': ('account_type', 'is_email_verified', 'api_key')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Subscription)
admin.site.register(UserSettings)