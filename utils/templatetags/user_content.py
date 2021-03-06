"""
Contains template tags related to displaying user contributed content, such as reviews, questions, and comments.
"""

from django.template import Library, Variable
register = Library()

@register.inclusion_tag('_review.html', takes_context=True)
def review(context, review):
    return {
        'content': review,
        'request': Variable('request').resolve(context)
    }


@register.inclusion_tag('_question.html', takes_context=True)
def question(context, question):
    return {
        'content': question,
        'request': Variable('request').resolve(context)
    }


@register.inclusion_tag('_answer.html', takes_context=True)
def answer(context, answer):
    return {
        'content': answer,
        'request': Variable('request').resolve(context)
    }
