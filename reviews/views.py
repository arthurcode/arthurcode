from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponseForbidden
from catalogue.models import Product
from reviews.forms import AddReviewForm, EditReviewForm, FlagReviewForm, AdminDeleteReviewForm
from reviews.models import Review
from utils.storeutils import get_products_needing_review
from reviews.signals import review_deleted
from lazysignup.decorators import allow_lazy_user
from accounts.decorators import non_lazy_login_required, public_profile_required

@non_lazy_login_required()
@public_profile_required()
def create_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        Review.objects.get(product=product, user=request.user)
        # A review already exists, forward them to the edit url
        return HttpResponseRedirect(edit_review_url(product))
    except Review.DoesNotExist:
        pass

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AddReviewForm(request, product, data=post_data)
        if form.is_valid():
            review = form.create_review()
            return HttpResponseRedirect(review.after_create_url())
    else:
        form = AddReviewForm(request, product)

    context = {
        'product': product,
        'needing_review': get_products_needing_review(request).exclude(id=product.id),
        'form': form,
    }
    return render_to_response("product_review.html", context, context_instance=RequestContext(request))


@non_lazy_login_required()
@public_profile_required()
def edit_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    try:
        review = Review.objects.select_related('user__public_profile', 'product').get(product=product, user=request.user)
    except Review.DoesNotExist:
        # there is no review to edit, forward them to the create-review url
        return HttpResponseRedirect(create_review_url(product))

    if request.method == "POST":
        post_data = request.POST.copy()
        if "delete" in post_data:
            if not request.user == review.user:
                return HttpResponseForbidden(u'You do not have permission to delete this review.')
            review.delete()
            review_deleted.send(sender=review)
            return HttpResponseRedirect(review.after_delete_url())
        form = EditReviewForm(request, review, data=post_data)
        if form.is_valid():
            form.edit_review()
            return HttpResponseRedirect(review.after_edit_url())
    else:
        form = EditReviewForm(request, review)

    context = {
        'form': form,
        'product': product,
        'review': review,
        'needing_review': get_products_needing_review(request).exclude(id=product.id)
    }
    return render_to_response("edit_review.html", context, context_instance=RequestContext(request))



def create_review_url(product):
    return reverse('create_product_review', kwargs={'product_slug': product.slug})


def edit_review_url(product):
    return reverse('edit_product_review', kwargs={'product_slug': product.slug})


@allow_lazy_user
def flag(request, id):
    """
    Flags the given review for removal.
    """
    review = get_object_or_404(Review, id=id)

    if request.method == "POST":
        post_data = request.POST.copy()
        if 'yes' in post_data:
            form = FlagReviewForm(request, review, data=post_data)
            if form.is_valid():
                form.do_flag()
                return HttpResponseRedirect(review.get_absolute_url())
        else:
            return HttpResponseRedirect(review.get_absolute_url())
    else:
        form = FlagReviewForm(request, review)

    context = {
        'review': review,
        'form': form,
    }
    return render_to_response("flag_review.html", context, context_instance=RequestContext(request))


@staff_member_required
def admin_delete(request, id):
    """
    A staff member can use this view to delete an inappropriate review.
    """
    review = get_object_or_404(Review, id=id)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = AdminDeleteReviewForm(request, review, data=post_data)
        if form.is_valid():
            form.delete_review()
            return HttpResponseRedirect(review.product.get_absolute_url())
    else:
        form = AdminDeleteReviewForm(request, review)

    context = {
        'review': review,
        'form': form,
    }
    return render_to_response("admin_delete_review.html", context, context_instance=RequestContext(request))

