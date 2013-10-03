from django.db import models
from catalogue.models import ProductInstance
from django.contrib.auth.models import User
from utils.validators import not_blank
from django.core.urlresolvers import reverse


class WishList(models.Model):
    NAME_MAX_LENGTH = 50
    DESCRIPTION_MAX_LENGTH = 200

    user = models.ForeignKey(User)
    created_at = models.DateField(auto_now_add=True)
    name = models.CharField(max_length=NAME_MAX_LENGTH, validators=[not_blank])
    description = models.CharField(max_length=DESCRIPTION_MAX_LENGTH, blank=True, null=True)

    class Meta:
        unique_together = ('user', 'name')

    def get_absolute_url(self):
        return reverse('wishlist_view', args=[self.id])


class WishListItem(models.Model):
    NOTE_MAX_LENGTH = 75

    wish_list = models.ForeignKey(WishList, related_name="items")
    instance = models.ForeignKey(ProductInstance)
    note = models.CharField(max_length=NOTE_MAX_LENGTH)
    created_at = models.DateField(auto_now_add=True)
    rank = models.PositiveIntegerField(help_text="The rank of this item relative to the others in the list")
