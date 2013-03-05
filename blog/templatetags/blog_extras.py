from django import template

register = template.Library()


def comment_anchor(comment):
    """
    Returns the anchor text for the blog comment in the form c<comment-id>
    """
    return "c%d" % comment.id


def comment_permalink(comment):
    """
    Returns a permanent link to the given blog comment.  The permanent link is assumed to be the absolute url of the
    post, plus the comment anchor text.
    """
    parent_url = comment.content_object.get_absolute_url()
    return "%s/#%s" % (parent_url, comment_anchor(comment))


register.simple_tag(comment_anchor)
register.simple_tag(comment_permalink)