from __future__ import absolute_import

from django import template
from django.conf import settings
import comments
from django.contrib.auth.decorators import login_required, permission_required
from comments import signals
from django.contrib.comments.views.utils import next_redirect, confirmation_view
from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.csrf import csrf_protect


@csrf_protect
@login_required
def flag(request, comment_id, next=None):
    """
    Flags a comment. Confirmation on GET, action on POST.

    Templates: `comments/flag.html`,
    Context:
        comment
            the flagged `comments.comment` object
    """
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    # Flag on POST
    if request.method == 'POST':
        perform_flag(request, comment)
        return next_redirect(request, next, flag_done, c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/flag.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )

@csrf_protect
@permission_required("comments.can_moderate")
def remove(request, comment_id, next=None):
    """
    Removes a comment. Confirmation on GET, action on POST. Requires the "can
    moderate comments" permission.

    Templates: `comments/delete.html`,
    Context:
        comment
            the flagged `comments.comment` object
    """
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    # Delete on POST
    if request.method == 'POST':
        # Flag the comment as deleted instead of actually deleting it.
        perform_remove(request, comment)
        return next_redirect(request, next, delete_done, c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/delete.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )

@csrf_protect
@permission_required("comments.can_moderate")
def approve(request, comment_id, next=None):
    """
    Approve a comment (that is, mark it as public and non-removed). Confirmation
    on GET, action on POST. Requires the "can moderate comments" permission.

    Templates: `comments/approve.html`,
    Context:
        comment
            the `comments.comment` object for approval
    """
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    # Delete on POST
    if request.method == 'POST':
        # Flag the comment as approved.
        perform_approve(request, comment)
        return next_redirect(request, next, approve_done, c=comment.pk)

    # Render a form on GET
    else:
        return render_to_response('comments/approve.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )

@csrf_protect
@permission_required("comments.can_moderate")
def mark_as_spam(request, comment_id, next=None):
    comment = get_object_or_404(comments.get_model(), pk=comment_id, site__pk=settings.SITE_ID)

    if request.method == 'POST':
        perform_mark_as_spam(request, comment)
        return next_redirect(request, next, mark_as_spam_done, c=comment.pk)

    else:
        return render_to_response('comments/mark_spam.html',
            {'comment': comment, "next": next},
            template.RequestContext(request)
        )

# The following functions actually perform the various flag/aprove/delete
# actions. They've been broken out into separate functions to that they
# may be called from admin actions.

def perform_flag(request, comment):
    """
    Actually perform the flagging of a comment from a request.
    """
    flag, created = comments.models.CommentFlag.objects.get_or_create(
        comment = comment,
        user    = request.user,
        flag    = comments.models.CommentFlag.SUGGEST_REMOVAL
    )
    signals.comment_was_flagged.send(
        sender  = comment.__class__,
        comment = comment,
        flag    = flag,
        created = created,
        request = request,
    )

def perform_remove(request, comment):
    flag, created = comments.models.CommentFlag.objects.get_or_create(
        comment = comment,
        user    = request.user,
        flag    = comments.models.CommentFlag.MODERATOR_DELETION
    )
    comment.is_removed = True
    comment.save()
    signals.comment_was_flagged.send(
        sender  = comment.__class__,
        comment = comment,
        flag    = flag,
        created = created,
        request = request,
    )


def perform_approve(request, comment):
    flag, created = comments.models.CommentFlag.objects.get_or_create(
        comment = comment,
        user    = request.user,
        flag    = comments.models.CommentFlag.MODERATOR_APPROVAL,
    )
    originally_spam = comment.is_spam
    comment.is_removed = False
    comment.is_public = True
    comment.is_spam = False
    comment.save()

    if originally_spam:
        signals.comment_was_marked_not_spam.send(
            sender = comment.__class__,
            comment = comment,
            request = request,
        )

    signals.comment_was_flagged.send(
        sender  = comment.__class__,
        comment = comment,
        flag    = flag,
        created = created,
        request = request,
    )


def perform_mark_as_spam(request, comment):
    """
    This manually performs the 'mark-as-spam' logic that the CommentModerator would have performed if
    it had detected that this comment was spam.
    """
    originally_spam = comment.is_spam

    comment.is_spam = True
    comment.is_public = False
    comment.save()

    if not originally_spam:
        signals.comment_was_marked_as_spam.send(
            sender = comment.__class__,
            comment = comment,
            request = request,
        )


# Confirmation views.

flag_done = confirmation_view(
    template = "comments/flagged.html",
    doc = 'Displays a "comment was flagged" success page.'
)
remove_done = confirmation_view(
    template = "comments/removed.html",
    doc = 'Displays a "comment was removed" success page.'
)
approve_done = confirmation_view(
    template = "comments/approved.html",
    doc = 'Displays a "comment was approved" success page.'
)

delete_done = confirmation_view(
    template="comments/deleted.html",
    doc = "Displays a 'comment was deleted' success page."
)

mark_as_spam_done = confirmation_view(
    template = "comments/marked_spam.html",
    doc = 'Displays a "comment was marked as spam" success page.'
)
