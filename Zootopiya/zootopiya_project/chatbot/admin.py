from django.contrib import admin
from .models import QuestionAnswer


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer')
    search_fields = ('question',)
    list_filter = ('question',)
