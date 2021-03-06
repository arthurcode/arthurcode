from django.conf.urls import patterns, url

urlpatterns = patterns('comments.views',
    url(r'^post/$', 'comment.post_comment',       name='comments-post-comment'),
    url(r'^posted/$', 'comment.comment_done',       name='comments-comment-done'),
    url(r'^flag/(\d+)/$',    'moderation.flag',             name='comments-flag'),
    url(r'^flagged/$',       'moderation.flag_done',        name='comments-flag-done'),
    url(r'^remove/(\d+)/$',  'moderation.remove',           name='comments-remove'),
    url(r'^removed/$',       'moderation.remove_done',      name='comments-remove-done'),
    url(r'^approve/(\d+)/$', 'moderation.approve',          name='comments-approve'),
    url(r'^approved/$',      'moderation.approve_done',     name='comments-approve-done'),
    url(r'^mark-spam/(\d+)/$', 'moderation.mark_as_spam',   name='comments-mark-spam'),
    url(r'^marked-spam/$',   'moderation.mark_as_spam_done',name='comments-mark-spam-done'),
)

urlpatterns += patterns('',
    url(r'^cr/(\d+)/(.+)/$', 'django.contrib.contenttypes.views.shortcut', name='comments-url-redirect'),
)
