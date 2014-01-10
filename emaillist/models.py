from django.db import models
from django.contrib.auth.models import User


class EmailListItem(models.Model):
    """
    Together these records make up an email list.  At the moment I'm making the simplifying assumption that I will
    only have one email marketing list.
    """
    email = models.EmailField(unique=True)
    date_added = models.DateField(auto_now_add=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)

    @property
    def name(self):
        """
        May return a first name, a blank string, or None.
        """
        if self.first_name:
            return self.first_name

        # we haven't stored a first name; see if this name is linked to an account
        try:
            user = User.objects.get(email=self.email)
            return user.first_name
        except User.DoesNotExist:
            return None