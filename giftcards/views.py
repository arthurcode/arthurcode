from django.shortcuts import render_to_response
from django.template import RequestContext


def home_view(request):
    return render_to_response('gc_home.html', {}, context_instance=RequestContext(request))


def check_balance_view(request):
    return render_to_response('gc_check_balance.html', {}, context_intsance=RequestContext(request))