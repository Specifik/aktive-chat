from rest_framework import serializers
from .models import TranslationHistory, UsageRecord, SavedVoice

class TranslationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TranslationHistory
        exclude = ['user']
        read_only_fields = ['created_at']

class UsageRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageRecord
        exclude = ['user']
        read_only_fields = ['timestamp', 'cost']

class SavedVoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedVoice
        exclude = ['user']
        read_only_fields = ['created_at', 'last_used']