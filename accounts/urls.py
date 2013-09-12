from django.conf.urls import patterns, url
from accounts.views import login_or_create_account, view_orders, view_personal, view_wishlists, view_reviews,\
    create_public_profile, change_email, change_password, change_password_done, logout, reset_password, \
    reset_password_done, reset_password_confirm, reset_password_complete, edit_contact_info, edit_public_profile, \
    add_shipping_address, add_billing_address, delete_shipping_address, delete_billing_address, create_account, \
    edit_shipping_address, edit_billing_address

urlpatterns = patterns('',
                       url(r'^login/$', login_or_create_account, name="login_or_create_account"),
                       url(r'^create-account/$', create_account, name="create_account"),
                       url(r'^logout/$', logout, name="logout"),
                       url(r'^create-public-profile', create_public_profile, name="create_public_profile"),
                       url(r'^edit-public-profile', edit_public_profile, name="edit_public_profile"),
                       url(r'^orders/$', view_orders, name="account_orders"),
                       url(r'^personal/$', view_personal, name="account_personal"),
                       url(r'^wishlists/$', view_wishlists, name="account_wishlists"),
                       url(r'^reviews/$', view_reviews, name="account_reviews"),
                       url(r'^change-email/$', change_email, name="account_change_email"),
                       url(r'^change-password/$', change_password, name="account_change_password"),
                       url(r'^change-password-done/$', change_password_done, name="account_change_password_done"),
                       url(r'^reset-password/$', reset_password, name="account_reset_password"),
                       url(r'^reset-password-done/$', reset_password_done, name="account_reset_password_done"),
                       url(r'^reset-password-confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', reset_password_confirm, name="account_reset_password_confirm"),
                       url(r'^reset-password-complete/$', reset_password_complete, name="account_reset_password_complete"),
                       url(r'^edit-contact-info/$', edit_contact_info, name="account_edit_contact_info"),
                       url(r'^add-shipping-address/$', add_shipping_address, name="add_shipping_address"),
                       url(r'^add-billing-address/$', add_billing_address, name="add_billing_address"),
                       url(r'^delete-shipping-address/(\d+)$', delete_shipping_address, name="delete_shipping_address"),
                       url(r'^delete-billing-address/(\d+)$', delete_billing_address, name="delete_billing_address"),
                       url(r'^edit-shipping-address/(\d+)$', edit_shipping_address, name="edit_shipping_address"),
                       url(r'^edit-billing-address/(\d+)$', edit_billing_address, name="edit_billing_address"),
                       )

