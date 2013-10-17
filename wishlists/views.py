from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from accounts.decorators import non_lazy_login_required, public_profile_required
from forms import CreateWishListForm, RemoveFromWishList, AddWishListItemToCart, EditWishListForm, EditWishListItemNote
from django.http import HttpResponseRedirect, HttpResponseForbidden, Http404
from models import WishList, WishListItem
from django.core.urlresolvers import reverse
from django.core.signing import Signer
from cart.cartutils import add_wishlist_item_to_cart

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
    bound_form = None
    instance_id = None

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
        elif "edit-note" in data:
            form = EditWishListItemNote(request, data=data)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse('wishlist_view', args=[wishlist_id]))
            else:
                bound_form = form
                instance_id = data.get('instance_id', None)

    items = wishlist.items.all()
    for item in items:
        if bound_form and str(item.id) == instance_id:
            form = bound_form
        else:
            form = EditWishListItemNote(request, item)
        arg_name = 'note_form'
        setattr(item, arg_name, form)

    context = {
        'wishlist': wishlist,
        'items': items,
    }
    return render_to_response('wishlist.html', context, context_instance=RequestContext(request))


@non_lazy_login_required
def edit_wishlist(request, wishlist_id):
    wishlist = get_object_or_404(WishList, id=wishlist_id)
    if request.user != wishlist.user:
        return HttpResponseForbidden(u"You do not have permission to view this wish list.")

    if request.method == "POST":
        data = request.POST.copy()
        form = EditWishListForm(request, wishlist, data=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('wishlist_view', args=[wishlist_id]))

    else:
        form = EditWishListForm(request, wishlist)

    context = {
        'form': form,
        'wishlist': wishlist,
    }
    return render_to_response('edit_wishlist.html', context, context_instance=RequestContext(request))


def _get_wishlist_url(request, wishlist):
    signer = Signer()
    wishlist_url = reverse('wishlist_shop', args=[signer.sign(wishlist.id)])
    return request.build_absolute_uri(wishlist_url)


def shop_wishlist(request, token):
    #signer = Signer()
    #
    #try:
    #    wishlist_id = signer.unsign(token)
    #except BadSignature:
    #    raise Http404("Unrecognized Wish List")

    #wishlist = get_object_or_404(WishList, id=wishlist_id)

    # TODO: encrypt the token.  For now it is easier to test without encryption.
    wishlist = get_object_or_404(WishList, id=token)

    if request.method == "POST":
        data = request.POST.copy()
        item_id = data.get('instance_id', None)
        if item_id:
            wishlist_item = get_object_or_404(WishListItem, id=item_id)
            add_wishlist_item_to_cart(request, wishlist_item)
            return HttpResponseRedirect(reverse('show_cart'))

    context = {
        'wishlist': wishlist,
    }
    return render_to_response('shop_wishlist.html', context, context_instance=RequestContext(request))

