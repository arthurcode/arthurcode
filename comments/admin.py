from django.contrib import admin
from comments.models import MPTTComment, CommentFlag
from django.utils.translation import ugettext_lazy as _, ungettext
from comments import get_model
from comments.views.moderation import perform_flag, perform_approve, perform_delete, perform_mark_as_spam

# TODO: put this code in a better place since it's specific to Blog's models
from django.contrib.admin import SimpleListFilter
from blog.models import Post


class PostFilter(SimpleListFilter):
    """
    Allow admin users to filter comments based on the blog post they were added to.
    """
    title = _('post')
    parameter_name = 'post'

    def lookups(self, request, model_admin):
        return [(p.id, _(p.title)) for p in Post.objects.order_by('-pub_date')]

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(object_pk=self.value())


class HasCommentFlagFilter(SimpleListFilter):
    # the following three fields should be specified by the subclass
    flag = None
    title = "placeholder"
    parameter_name = "placeholder"

    def lookups(self, request, model_admin):
        return (
            ('True', 'Yes'),
            ('False', 'No'),
        )

    def queryset(self, request, queryset):
        if not self.value():
            return queryset

        flagged_comments = CommentFlag.objects \
            .filter(flag=self.flag) \
            .values('comment__pk') \
            .distinct('comment__pk')

        if self.value() == "True":
            return queryset.filter(pk__in=flagged_comments)
        else:
            return queryset.exclude(pk__in=flagged_comments)


class IsFlaggedForRemovalFilter(HasCommentFlagFilter):
    title = _('is flagged for removal')
    parameter_name = 'flagged'
    flag = CommentFlag.SUGGEST_REMOVAL


class IsApprovedFilter(HasCommentFlagFilter):
    title = _('is approved')
    parameter_name ='approved'
    flag = CommentFlag.MODERATOR_APPROVAL


class CommentsAdmin(admin.ModelAdmin):
    fieldsets = (
        (None,
         {'fields': ('content_type', 'object_pk', 'site')}
        ),
        (_('Content'),
         {'fields': ('user', 'user_name', 'user_email', 'user_url', 'comment', 'email_on_reply')}
        ),
        (_('Metadata'),
         {'fields': ('submit_date', 'ip_address', 'is_public', 'is_removed', 'is_spam', 'parent')}
        ),
    )

    list_display = ('name', 'content_type', 'object_pk', 'ip_address', 'submit_date', 'is_public', 'is_removed', 'is_spam',
                    'is_approved', 'is_flagged_for_removal',)
    list_filter = ('submit_date', 'site', 'is_public', 'is_removed', 'is_spam', PostFilter, IsFlaggedForRemovalFilter,
                   IsApprovedFilter,)
    date_hierarchy = 'submit_date'
    ordering = ('-submit_date',)
    raw_id_fields = ('user',)
    search_fields = ('comment', 'user__username', 'user_name', 'user_email', 'user_url', 'ip_address')
    actions = ["flag_comments", "approve_comments", "remove_comments", "mark_as_spam"]
    readonly_fields = ('is_spam',)

    def get_actions(self, request):
        actions = super(CommentsAdmin, self).get_actions(request)
        # Only superusers should be able to delete the comments from the DB.
        if not request.user.is_superuser and 'delete_selected' in actions:
            actions.pop('delete_selected')
        if not request.user.has_perm('comments.can_moderate'):
            if 'approve_comments' in actions:
                actions.pop('approve_comments')
            if 'remove_comments' in actions:
                actions.pop('remove_comments')
            if 'mark_as_spam' in actions:
                actions.pop('mark_as_spam')
        return actions

    def flag_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_flag,
                        lambda n: ungettext('flagged', 'flagged', n))
    flag_comments.short_description = _("Flag selected comments")

    def approve_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_approve,
                        lambda n: ungettext('approved', 'approved', n))
    approve_comments.short_description = _("Approve selected comments")

    def remove_comments(self, request, queryset):
        self._bulk_flag(request, queryset, perform_delete,
                        lambda n: ungettext('removed', 'removed', n))
    remove_comments.short_description = _("Remove selected comments")

    def mark_as_spam(self, request, queryset):
        self._bulk_flag(request, queryset, perform_mark_as_spam,
                        lambda n: ungettext('marked as spam', 'marked as spam', n))
    mark_as_spam.short_description = _("Mark comments as spam")

    def _bulk_flag(self, request, queryset, action, done_message):
        """
        Flag, approve, or remove some comments from an admin action. Actually
        calls the `action` argument to perform the heavy lifting.
        """
        n_comments = 0
        for comment in queryset:
            action(request, comment)
            n_comments += 1

        msg = ungettext(u'1 comment was successfully %(action)s.',
                        u'%(count)s comments were successfully %(action)s.',
                        n_comments)
        self.message_user(request, msg % {'count': n_comments, 'action': done_message(n_comments)})

    def save_model(self, request, obj, form, change):
        """
        Custom handling for the admin 'action' buttons I manually added to the model change_form view.
        Hopefully hacks like this won't be necessary in future versions of django:
        https://code.djangoproject.com/ticket/12090
        """
        super(CommentsAdmin, self).save_model(request, obj, form, change)

        if 'approve' in form.data:
            perform_approve(request, obj)
        elif 'spam' in form.data:
            perform_mark_as_spam(request, obj)

# Only register the default admin if the model is the built-in comment model
# (this won't be true if there's a custom comment app).
if get_model() is MPTTComment:
    admin.site.register(MPTTComment, CommentsAdmin)
