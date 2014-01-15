from django.views.generic.base import TemplateView

PAGE_TITLE_FIELD = "page_title"

class AboutView(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        data = super(AboutView, self).get_context_data(**kwargs)
        data[PAGE_TITLE_FIELD] = "About"
        return data


class ContactView(TemplateView):
    template_name = "contact.html"

    def get_context_data(self, **kwargs):
        data = super(ContactView, self).get_context_data(**kwargs)
        data[PAGE_TITLE_FIELD] = "Contact"
        return data
