from django.contrib import admin
from .models import User, Subscription, UserSettings

#Simple admin for User model
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_active']
    search_fields = ['username', 'email']

#Register other models
admin.site.register(Subscription)
admin.site.register(UserSettings)