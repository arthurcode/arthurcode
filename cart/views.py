from django.shortcuts import render_to_response
from django.template import RequestContext


def show_cart(request):
    return render_to_response('cart.html', {}, context_instance=RequestContext(request))