from django.contrib import admin
from models import EmailListItem

class EmailListItemAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'date_added')


admin.site.register(EmailListItem, EmailListItemAdmin)
