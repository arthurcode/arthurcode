from django.shortcuts import get_object_or_404, render_to_response
from orders.models import Order
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.views.decorators.http import require_GET


@require_GET
@login_required
def detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    receipt = False
    if not request.user.is_staff:
        # check that this regular user has permission to view this order summary
        if not order.user or not order.user == request.user:
            return HttpResponseForbidden(u"You do not have permission to view this order.")
        receipt = True

    profile = None
    if order.user:
        profile = order.user.get_customer_profile()

    context = {
        'order': order,
        'profile': profile,
        'receipt': receipt
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