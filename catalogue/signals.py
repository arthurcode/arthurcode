from django.db.models.signals import pre_save
from catalogue.models import ProductInstance
from django.dispatch import receiver
from django.core.mail import send_mass_mail, mail_managers
from arthurcode.settings import EMAIL_NOTIFICATIONS

@receiver(pre_save, sender=ProductInstance)
def on_product_instance_save(sender, instance, **kwargs):
    saved_instance = ProductInstance.objects.filter(id=instance.id)

    if not saved_instance.exists():
        # a creation event
        return

    current_stock = saved_instance[0].quantity
    if current_stock <= 0 and instance.quantity:
        # the product has been re-stocked
        on_product_instance_restock(instance)
    elif current_stock and instance.quantity <= 0:
        # this product is now out of stock
        on_product_out_of_stock(instance)


def on_product_instance_restock(instance):
    notifications = instance.restock_notifications.all()
    if not notifications.exists():
        return

    # send the email
    # TODO: craft a proper email message
    subject = "Product Back in Stock"
    message = """
    The product you were interested in is back in stock!

    To purchase this item visit this url (TBD)
    Note that limited quantities of this product are available, and this email does not mean that we are saving stock
    specifically for you.

    Sincerely,
    The Brainstand Toys Team.
    """
    from_email = EMAIL_NOTIFICATIONS
    send_mass_mail([(subject, message, from_email, [n.email]) for n in notifications], fail_silently=True)

    # delete the notifications
    for n in notifications:
        n.delete()


def on_product_out_of_stock(instance):
    """
    Mail site management when a product goes out of stock
    """
    # TODO: craft a proper email message
    subject = "Product out of stock"
    message = "The product %s is now out of stock." % unicode(instance)
    mail_managers(subject, message)
