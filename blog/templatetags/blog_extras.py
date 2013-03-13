from django import template
import re

register = template.Library()


REQUIRED_TEXT = "(required)"
OPTIONAL_TEXT = "(optional)"
LABEL_PATTERN = re.compile(r"^<label(?P<attrs>[^>]*)>(?P<text>[^<]*)</label>$")

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


def field_label_tag(field):
    """
     Returns a label tag for the given form field.  The label tag will include the original label text wrapped in a
     span with class='label'.
     If there are errors on the field they will be included in the label wrapped in a span with class='error'.
     If the field is required a span with class='required-text' and text=(required) will be added to the label.
     If the field is not required a span with class='optional-text' and text=(optional) will be added to the label.
     These spans function as css styling hooks.
    """
    base_label = field.label_tag()
    match = re.match(LABEL_PATTERN, base_label)

    if not match:
        return base_label
    text = match.group('text')

    # wrap the base label in a 'label' span
    text = "<span class='label'>%s</span>" % text

    # add in the (required) or (optional) string
    if field.field.required:
        text += " <span class='required-text'>%s</span>" % REQUIRED_TEXT
    else:
        text += " <span class='optional-text'>%s</span>" % OPTIONAL_TEXT

    if field._errors():
        text += " <span class='error'>%s</span>" % field._errors().as_text()

    return "<label%s>%s</label>" % (match.group('attrs'), text)


register.simple_tag(comment_anchor)
register.simple_tag(comment_permalink)
register.simple_tag(field_label_tag)