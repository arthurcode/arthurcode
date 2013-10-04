from django.db import models
from catalogue.models import ProductInstance
from django.contrib.auth.models import User
from utils.validators import not_blank
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Max


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

    def add_product(self, product_instance, note=None):
        max_rank = self.items.all().aggregate(Max('rank')).get('rank__max', None) or 0
        rank = max_rank + 1
        item = WishListItem(wish_list=self, instance=product_instance, note=note, rank=rank)
        item.full_clean()
        item.save()
        return item


class WishListItem(models.Model):
    NOTE_MAX_LENGTH = 75

    wish_list = models.ForeignKey(WishList, related_name="items")
    instance = models.ForeignKey(ProductInstance)
    note = models.CharField(max_length=NOTE_MAX_LENGTH, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    rank = models.PositiveIntegerField(help_text="The rank of this item relative to the others in the list")