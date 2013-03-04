from models import MPTTComment
from forms import MPTTCommentForm

# For more information read the django docs on customizing the commenting framework:
# https://docs.djangoproject.com/en/dev/ref/contrib/comments/custom/

def get_model():
    return MPTTComment


def get_form():
    return MPTTCommentForm