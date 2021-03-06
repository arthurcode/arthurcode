"""
Signals relating to comments.
"""
from django.dispatch import Signal

# Sent just before a comment will be posted (after it's been approved and
# moderated; this can be used to modify the comment (in place) with posting
# details or other such actions. If any receiver returns False the comment will be
# discarded and a 403 (not allowed) response. This signal is sent at more or less
# the same time (just before, actually) as the Comment object's pre-save signal,
# except that the HTTP request is sent along with this signal.
comment_will_be_posted = Signal(providing_args=["comment", "request"])

# Sent just after a comment was posted. See above for how this differs
# from the Comment object's post-save signal.
comment_was_posted = Signal(providing_args=["comment", "request"])

# Sent after a comment was "flagged" in some way. Check the flag to see if this
# was a user requesting removal of a comment, a moderator approving/removing a
# comment, or some other custom user flag.
comment_was_flagged = Signal(providing_args=["comment", "flag", "created", "request"])

# Sent after an administrator marks a comment as spam.  If an admin has to mark
# a comment as spam that means that it was missed by our spam filter.  Some
# comment moderators may be able to learn from this mistake, which is why we send
# the signal.
comment_was_marked_as_spam = Signal(providing_args=["comment", "request"])

# Sent after a comment that was initially marked as spam is marked as
# not-spam by an administrator.  Some comment moderators may be able to learn
# from this mistake, which is why we send the signal.
comment_was_marked_not_spam = Signal(providing_args=["comment", "request"])
