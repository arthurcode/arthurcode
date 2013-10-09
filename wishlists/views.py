from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from accounts.decorators import non_lazy_login_required, public_profile_required
from forms import CreateWishListForm, RemoveFromWishList, AddWishListItemToCart
from django.http import HttpResponseRedirect, HttpResponseForbidden
from models import WishList
from django.core.urlresolvers import reverse

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
def view_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(WishList, id=wishlist_id)
    if request.user != wishlist.user:
        return HttpResponseForbidden(u"You do not have permission to view this wish list.")

    if request.method == "POST":
        data = request.POST.copy()
        if "remove" in data:
            form = RemoveFromWishList(request, data=data)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('wishlist_view', args=[wishlist_id]))
        elif "add-to-cart" in data:
            form = AddWishListItemToCart(request, data=data)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('show_cart'))

    context = {
        'wishlist': wishlist,
    }
    return render_to_response('wishlist.html', context, context_instance=RequestContext(request))