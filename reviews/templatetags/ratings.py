from django.template import Library

register = Library()

@register.inclusion_tag('_rating.html')
def rating(rating):
    """
    Given a rating between 1 and 5 (decimal values are allowed) returns a 'rating' html div containing the star
    representation of the number, together with some text for screen reader users.
    """
    if not rating:
        # the product has not been rated yet
        return {
            'rating': None,
            'stars': ['0']*5
        }

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
