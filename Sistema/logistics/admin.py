from django.contrib import admin
from .models import DailyOperation


@admin.register(DailyOperation)
class DailyOperationAdmin(admin.ModelAdmin):
    list_display = ('date', 'tour', 'driver', 'status')
    list_filter = ('date', 'status', 'tour')
    search_fields = ('tour__name', 'driver__email')
