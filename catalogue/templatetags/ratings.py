from utils.templatetags.extras import query_string, get_query_string
from django.template import Library
from django.core.urlresolvers import reverse
from catalogue import filters

register = Library()

@register.inclusion_tag('_rating.html')
def rating(rating):
    """
    Given a rating between 1 and 5 (decimal values are allowed) returns a 'rating' html div containing the star
    representation of the number, together with some text for screen reader users.
    """
    full_stars = int(rating)
    stars = ['4']*full_stars

    if full_stars < 5:
        partial_star = rating % 1
        if partial_star < 0.25:
            stars.append('0')      # empty star
        elif partial_star < 0.5:
            stars.append('1')      # 1/4 star
        elif partial_star < 0.75:
            stars.append('2')      # 1/2 star
        else:
            stars.append('3')      # 3/4 star

        for i in range(5 - len(stars)):
            stars.append('0')     # pad with empty stars

    return {
        'rating': rating,
        'stars': stars,
    }
