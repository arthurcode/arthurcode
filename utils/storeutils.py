from catalogue.models import Product
from orders.models import OrderItem
from accounts.models import CustomerProfile


def get_products_needing_review(request):
    """
    Returns the products that the logged-in user has purchased, but hasn't reviewed yet.
    """
    if not request.user.is_authenticated():
        return Product.objects.none()

    try:
        profile = request.user.customer_profile
        already_reviewed = Product.objects.filter(reviews__user=request.user)  # product this user has already reviewed
        ids = OrderItem.objects.filter(order__customer=profile).exclude(product__in=already_reviewed).values_list('product', flat=True).distinct()
        return Product.objects.filter(id__in=ids)
    except CustomerProfile.DoesNotExist:
        # if they don't have a customer profile they haven't ordered anything!
        return Product.objects.none()

