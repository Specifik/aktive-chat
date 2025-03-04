from django.contrib import admin
from .models import UsageRecord, SavedVoice, TranslationHistory

@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'service_type', 'timestamp', 'character_count', 'cost')
    list_filter = ('service_type', 'timestamp')
    search_fields = ('user__email', 'service_type')

@admin.register(SavedVoice)
class SavedVoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'provider', 'language', 'is_cloned')
    list_filter = ('provider', 'language', 'is_cloned')
    search_fields = ('name', 'user__email')

@admin.register(TranslationHistory)
class TranslationHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'source_language', 'target_language', 'created_at', 'favorited')
    list_filter = ('source_language', 'target_language', 'favorited', 'created_at')
    search_fields = ('user__email', 'original_text', 'translated_text')