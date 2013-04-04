from django.contrib import admin
from blog.models import Post, AuthorProfile
from django.forms.models import ModelForm
from django.contrib.admin.filters import SimpleListFilter


class PostAdminForm(ModelForm):
    class Meta:
        model = Post

    def save(self, commit=True):
        """
        Handling for the custom 'Publish' admin button
        """
        instance = super(PostAdminForm, self).save(commit=commit)

        if self.data.has_key('publish'):
            instance.publish()
        return instance


class AuthorFilter(SimpleListFilter):
    title = "author"
    parameter_name = "author"

    def lookups(self, request, model_admin):
        return [(a.id, a.pen_name) for a in AuthorProfile.objects.all()]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(author__id=self.value())


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'title_slug': ('title',)}
    date_hierarchy = 'pub_date'
    readonly_fields = ('is_draft',)
    form = PostAdminForm
    ordering = ('-pub_date',)
    search_fields = ('title', 'body', 'synopsis')
    list_display = ('title', 'author', 'pub_date', 'mod_date', 'is_draft', 'enable_comments')
    list_filter = ('pub_date', 'mod_date', 'is_draft', AuthorFilter)


class AuthorProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Post, PostAdmin)
admin.site.register(AuthorProfile, AuthorProfileAdmin)