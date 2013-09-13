from django.shortcuts import get_object_or_404, render_to_response
from orders.models import Order
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_GET
from accounts.decorators import non_lazy_login_required


@require_GET
@non_lazy_login_required()
def detail_view(request, order_id):
    """
    This is the customer's view of their order.  This is not meant to be an admin view.
    """
    order = get_object_or_404(Order, id=order_id)
    # check that this regular user has permission to view this order summary
    if not order.user or not order.user == request.user:
        return HttpResponseForbidden(u"You do not have permission to view this order.")

    context = {
        'order': order,
    }
    return render_to_response('order_detail.html', context, context_instance=RequestContext(request))


@login_required
def cancel_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if not request.user.is_staff:
        if not order.user or not order.user == request.user:
            return HttpResponseForbidden(u"You do not have permission to cancel this order.")

    if request.method == "POST":
        if "confirm" in request.POST:
            order.cancel()
        return HttpResponseRedirect(order.get_absolute_url())
    else:
        context = {
            'order': order,
        }
        return render_to_response('order_cancel.html', context, context_instance=RequestContext(request))