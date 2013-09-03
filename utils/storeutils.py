from catalogue.models import Product
from reviews.models import Review
from orders.models import OrderItem


def get_products_needing_review(request):
    """
    Returns the products that the logged-in user has purchased, but hasn't reviewed yet.
    """
    if not request.user.is_authenticated():
        return Product.objects.none()

    already_reviewed = Review.objects.filter(user=request.user).values_list('product__id', flat=True)
    ids = OrderItem.objects.filter(order__user=request.user).exclude(item__product__in=already_reviewed).values_list('item__product', flat=True).distinct()
    return Product.objects.filter(id__in=ids)

