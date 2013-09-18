from django.db.models.signals import pre_save
from catalogue.models import ProductInstance
from django.dispatch import receiver
from django.core.mail import send_mass_mail

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
    The Toy Tree Team.
    """
    from_email = "fixme@toytree.com"
    send_mass_mail([(subject, message, from_email, [n.email]) for n in notifications], fail_silently=True)

    # delete the notifications
    for n in notifications:
        n.delete()