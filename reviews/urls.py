from django.conf.urls import patterns, url
from reviews.views import create_review, flag, admin_delete, edit_review, delete_review, view_review, approve, \
    withdraw_approval

urlpatterns = patterns('',
                    url(r'^flag/(?P<id>\d+)$', flag, name="flag_review"),
                    url(r'^admin-delete/(?P<id>\d+)$', admin_delete, name="admin_delete_review"),
                    url(r'^view/(?P<product_slug>[-\w]*)', view_review, name="your_review"),
                    url(r'^create/(?P<product_slug>[-\w]*)$', create_review, name="create_product_review"),
                    url(r'^edit/(?P<product_slug>[-\w]*)$', edit_review, name="edit_product_review"),
                    url(r'^delete/(?P<product_slug>[-\w]*)$', delete_review, name="delete_product_review"),
                    url(r'^approve/(?P<id>\d+)$', approve, name="approve_product_review"),
                    url(r'^withdraw-approval/(?P<id>\d+)', withdraw_approval, name="withdraw_approval_product_review")
)


    #
    # url(r'^post/$', 'comment.post_comment',       name='comments-post-comment'),
    # url(r'^posted/$', 'comment.comment_done',       name='comments-comment-done'),
    # url(r'^flag/(\d+)/$',    'moderation.flag',             name='comments-flag'),
    # url(r'^flagged/$',       'moderation.flag_done',        name='comments-flag-done'),
    # url(r'^delete/(\d+)/$',  'moderation.delete',           name='comments-delete'),
    # url(r'^deleted/$',       'moderation.delete_done',      name='comments-delete-done'),
    # url(r'^approve/(\d+)/$', 'moderation.approve',          name='comments-approve'),
    # url(r'^approved/$',      'moderation.approve_done',     name='comments-approve-done'),
    # url(r'^mark-spam/(\d+)/$', 'moderation.mark_as_spam',   name='comments-mark-spam'),
    # url(r'^marked-spam/$',   'moderation.mark_as_spam_done',name='comments-mark-spam-done'),
