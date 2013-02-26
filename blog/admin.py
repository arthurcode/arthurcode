from django.contrib import admin
from blog.models import Post, AuthorProfile


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'title_slug': ('title',)}
    date_hierarchy = 'pub_date'


class AuthorProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Post, PostAdmin)
admin.site.register(AuthorProfile, AuthorProfileAdmin)