from django import template
from django.forms import CheckboxInput, RadioSelect
import re
from bs4 import BeautifulSoup
from django.forms.util import ErrorList

register = template.Library()


REQUIRED_TEXT = "(required)"
OPTIONAL_TEXT = "(optional)"
LABEL_PATTERN = re.compile(r"^<label(?P<attrs>[^>]*)>(?P<text>[^<]*)</label>$")


@register.simple_tag
def field_label_tag(field):
    """
     Returns a label tag for the given form field.  The label tag will include the original label text wrapped in a
     span with class='label'.
     If there are errors on the field they will be included in the label wrapped in a span with class='error'.
     If the field is required a span with class='required-text' and text=(required) will be added to the label span.
     If the field is not required a span with class='optional-text' and text=(optional) will be added to the label span.
     These spans function as css styling hooks.
    """
    base_label = field.label_tag()
    match = re.match(LABEL_PATTERN, base_label)

    if not match:
        return base_label
    text = match.group('text')

    # calculate the (required) or (optional) string
    if field.field.required:
        marker_text = "<span class='required-text'>%s</span>" % REQUIRED_TEXT
    else:
        marker_text = "<span class='optional-text'>%s</span>" % OPTIONAL_TEXT

    # wrap the base label in a 'label' span.  Inside the label span add a bit of marker text to indicate whether or
    # not the field is required or optional
    text = "<span class='label'>%s %s</span>" % (text, marker_text)

    if field.field.help_text:
        text += " <span class='help-text'>%s</span>" % unicode(field.field.help_text)

    if field._errors():
        text += " <span class='error'>%s</span>" % field._errors().as_text()

    return "<label%s>%s</label>" % (match.group('attrs'), text)


@register.simple_tag
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


@register.simple_tag
def field_class(field):
    """
    Returns "checkbox" for checkbox fields, "radio" for radio selects and "text" for all other fields.
    """
    widget_class = field.field.widget.__class__.__name__
    if widget_class == CheckboxInput().__class__.__name__:
        return "checkbox"
    elif widget_class == RadioSelect().__class__.__name__:
        return "radio"
    return "text"


@register.filter(name="is_checkbox")
def is_checkbox(field):
    return field_class(field) == "checkbox"


@register.filter(name="is_radio")
def is_radio(field):
    return field_class(field) == "radio"


@register.inclusion_tag("_field.html")
def field(field):
    return {'field': field}


@register.inclusion_tag("_form_errors.html")
def form_errors(form, unique=False):
    """
    Outputs any errors in this form as an unordered list.  The general errors are found at the beginning of the list.
    By default this function prints out the general errors as well as the field-specific errors.  To suppress the
    field-specific errors (may be desirable for very short forms) pass unique=True.
    """
    error_list = []
    # put the most general errors at the beginning of the list
    if form.errors:
        if '__all__' in form.errors:
            general_errors = form.errors['__all__']
            if isinstance(general_errors, ErrorList):
                for e in general_errors:
                    error_list.append(unicode(e))
            else:
                error_list.append(unicode(general_errors))
        if not unique:
            for k,errors in form.errors.items():
                if k == '__all__':
                    continue
                field_name = form.fields[k].label or k
                field_name = field_name.capitalize()
                if isinstance(errors, ErrorList):
                    for e in errors:
                        error_list.append("%s: %s" % (field_name, unicode(e)))
                else:
                    error_list.append("%s: %s" % (field_name, unicode(errors)))
    return {'error_list': error_list}

@register.inclusion_tag("_readonly_field.html")
def readonly_field(field):
    return {'field': field}