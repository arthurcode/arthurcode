from django.shortcuts import get_object_or_404, render_to_response
from django.views.decorators.http import require_GET
from django.template import RequestContext
from accounts.decorators import non_lazy_login_required, public_profile_required
from forms import CreateWishListForm
from django.http import HttpResponseRedirect
from models import WishList

PRODUCT_INSTANCE_KEY = 'addProduct'

@non_lazy_login_required
def create_wishlist(request):
    if request.method == "POST":
        data = request.POST.copy()
        form = CreateWishListForm(request, data=data)
        if form.is_valid():
            wishlist = form.save()
            return HttpResponseRedirect(wishlist.get_absolute_url())
    else:
        instance_id = request.GET.get(PRODUCT_INSTANCE_KEY, None)
        initial = {}
        if instance_id:
            try:
                initial['instance_id'] = int(instance_id)
            except:
                pass
        form = CreateWishListForm(request, initial=initial)

    context = {
        'form': form,
    }
    return render_to_response('create_wishlist.html', context, context_instance=RequestContext(request))


@non_lazy_login_required
@require_GET
def view_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(WishList, id=wishlist_id)
    context = {
        'wishlist': wishlist,
    }
    return render_to_response('wishlist.html', context, context_instance=RequestContext(request))