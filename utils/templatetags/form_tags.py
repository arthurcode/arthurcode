from django import template
from django.forms import CheckboxInput
import re
from bs4 import BeautifulSoup

register = template.Library()


REQUIRED_TEXT = "(required)"
OPTIONAL_TEXT = "(optional)"
LABEL_PATTERN = re.compile(r"^<label(?P<attrs>[^>]*)>(?P<text>[^<]*)</label>$")


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


def aria_required_field(field):
    """
     Add 'required' and 'aria-required' attributes to the html of required fields.
     See http://john.foliot.ca/required-inputs/ for background on why
     I'm adding these attributes.
    """
    if not field.field.required:
        return unicode(field)
    soup = BeautifulSoup(unicode(field))
    element = soup.contents[0]
    element.attrs.update({'required': '', 'aria-required': 'true'})
    return unicode(soup)

def field_class(field):
    """
    Returns "checkbox" for checkbox fields and "text" for all other fields.
    """
    if field.field.widget.__class__.__name__ == CheckboxInput().__class__.__name__:
        return "checkbox"
    return "text"


@register.filter(name="is_checkbox")
def is_checkbox(field):
    return field_class(field) == "checkbox"


@register.inclusion_tag("_field.html")
def field(field):
    return {'field': field}

register.simple_tag(field_label_tag)
register.simple_tag(aria_required_field)
register.simple_tag(field_class)