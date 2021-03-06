from django.conf.urls import patterns, url
from questions.views import ask_view, show_view, edit_view, delete_view, answer_view

urlpatterns = patterns('',
                    url(r'^ask/(?P<product_slug>[-\w]*)$', ask_view, name="ask_question"),
                    url(r'^show/(?P<id>\d+)', show_view, name="show_question"),
                    url(r'^edit/(?P<id>\d+)', edit_view, name="edit_question"),
                    url(r'^delete/(?P<id>\d+)', delete_view, name="delete_question"),
                    url(r'^answer/(?P<id>\d+)', answer_view, name="answer_question")
)


