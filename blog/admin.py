from django.contrib import admin
from blog.models import Post, AuthorProfile
from django.forms.models import ModelForm


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


class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'title_slug': ('title',)}
    date_hierarchy = 'pub_date'
    readonly_fields = ('is_draft',)
    form = PostAdminForm


class AuthorProfileAdmin(admin.ModelAdmin):
    pass


admin.site.register(Post, PostAdmin)
admin.site.register(AuthorProfile, AuthorProfileAdmin)