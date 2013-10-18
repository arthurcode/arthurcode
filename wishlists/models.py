from django.db import models
from catalogue.models import ProductInstance
from django.contrib.auth.models import User
from utils.validators import not_blank
from django.core.urlresolvers import reverse
from cart.models import CartItem
from orders.models import OrderItem


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
        item = WishListItem(wish_list=self, instance=product_instance, note=note)
        item.full_clean()
        item.save()
        return item

    def get_shop_url(self):
        # TODO: use encryption eventually
        return reverse("wishlist_shop", args=[self.id])

    def get_purchased_items(self):
        return self.items.exclude(order_item__isnull=True)


class WishListItem(models.Model):
    NOTE_MAX_LENGTH = 75

    wish_list = models.ForeignKey(WishList, related_name="items")
    instance = models.ForeignKey(ProductInstance)
    note = models.CharField(max_length=NOTE_MAX_LENGTH, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)
    order_item = models.ForeignKey(OrderItem, null=True, blank=True,
                                   help_text=u"The purchasing order item, if applicable.")


class WishListItemToCartItem(models.Model):
    """
    A class to link wish list items to cart items.  Both wish list items and cart items are highly transient, so this
    should be thought of as a highly transient class.  It should be deleted as soon as the related wish list item or
    cart item is deleted. TODO: confirm that this is the case.
    """
    wishlist_item = models.ForeignKey(WishListItem)
    cart_item = models.ForeignKey(CartItem, related_name="wishlist_links")
