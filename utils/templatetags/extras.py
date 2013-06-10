
from django.template import Library, Node, resolve_variable
from django.utils.safestring import mark_safe
import locale
import urllib

register = Library()

class AddGetParameter(Node):
    def __init__(self, values):
        self.values = values

    def render(self, context):
        req = resolve_variable('request', context)
        params = req.GET.copy()
        for key, value in self.values.items():
            params[key] = value.resolve(context)
        return '?%s' %  params.urlencode()


@register.tag
def add_get(parser, token):
    """
    The tag generates a parameter string in form '?param1=val1&param2=val2'.
    The parameter list is generated by taking all parameters from current
    request.GET and optionally overriding them by providing parameters to the tag.

    This is a cleaned up version of http://djangosnippets.org/snippets/2105/. It
    solves a couple of issues, namely:
     * parameters are optional
     * parameters can have values from request, e.g. request.GET.foo
     * native parsing methods are used for better compatibility and readability
     * shorter tag name

    Usage: place this code in your appdir/templatetags/add_get_parameter.py
    In template:
    {% load add_get_parameter %}
    <a href="{% add_get param1='const' param2=variable_in_context %}">
    Link with modified params
    </a>

    It's required that you have 'django.core.context_processors.request' in
    TEMPLATE_CONTEXT_PROCESSORS

    Original version's URL: http://django.mar.lt/2010/07/add-get-parameter-tag.html
    """
    pairs = token.split_contents()[1:]
    values = {}
    for pair in pairs:
        s = pair.split('=', 1)
        values[s[0]] = parser.compile_filter(s[1])
    return AddGetParameter(values)

@register.inclusion_tag('_response.html', takes_context=True)
def query_string(context, add=None, remove=None):
    """
    Allows the addition and removal of query string parameters.

    _response.html is just {{ response }}

    Usage:
    http://www.url.com/{% query_string "param_to_add=value, param_to_add=value" "param_to_remove, params_to_remove" %}
    http://www.url.com/{% query_string "" "filter" %}filter={{new_filter}}
    http://www.url.com/{% query_string "sort=value" "sort" %}
    """
    # Written as an inclusion tag to simplify getting the context.
    add = string_to_dict(add)
    remove = string_to_list(remove)
    params = dict( context['request'].GET.items())
    response = get_query_string(params, add, remove)
    return {'response': response }


# lib/utils.py
def get_query_string(p, new_params=None, remove=None):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    if new_params is None: new_params = {}
    if remove is None: remove = []
    for r in remove:
        for k in p.keys():
            # the original code was if k.startswith(r), delete, which I DID NOT LIKE
            if k == r:
                del p[k]
    for k, v in new_params.items():
        if k in p and v is None:
            del p[k]
        elif v is not None:
            p[k] = v
    return mark_safe("?" + urllib.urlencode(p))


def string_to_dict(string):
    """
    Usage::

        {{ url|thumbnail:"width=10,height=20" }}
        {{ url|thumbnail:"width=10" }}
        {{ url|thumbnail:"height=20" }}
    """
    kwargs = {}
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            kw, val = arg.split('=', 1)
            kwargs[kw] = val
    return kwargs


def string_to_list(string):
    """
    Usage::

        {{ url|thumbnail:"width,height" }}
    """
    args = []
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            args.append(arg)
    return args

@register.filter(name='currency')
def currency(value):
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL, '')
    loc = locale.localeconv()
    return locale.currency(value, loc['currency_symbol'], grouping=True)