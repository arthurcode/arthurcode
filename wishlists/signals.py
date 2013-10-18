from django.dispatch import receiver
from orders.signals import signal_order_cancelled
from models import WishListItem

@receiver(signal_order_cancelled)
def order_cancelled(sender, **kwargs):
    """
    Make sure any wish list items that were on the cancelled order are no longer marked as 'purchased'.
    """
    for item in sender.items.all():
        for wl_item in WishListItem.objects.filter(order_item=item):
            wl_item.order_item = None
            wl_item.full_clean()
            wl_item.save()

