__author__ = 'rhyanarthur'

from django.contrib import admin
from comments.models import MPTTComment


class CommentAdmin(admin.ModelAdmin):
    pass


admin.site.register(MPTTComment, CommentAdmin)
