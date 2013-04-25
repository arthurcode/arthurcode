"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from utils.templatetags import form_tags
from string import replace


# utils for testing forms

class FormTest(TestCase):

    def get_label_name(self, label):
        label_span = label.find('span', 'label')
        self.assertIsNotNone(label_span)
        text = label_span.text
        if form_tags.REQUIRED_TEXT in text:
            return replace(text, form_tags.REQUIRED_TEXT, '').strip()
        else:
            return replace(text, form_tags.OPTIONAL_TEXT, '').strip()

    def is_required(self, label):
        label_span = label.find('span', 'label')
        self.assertIsNotNone(label_span)
        return form_tags.REQUIRED_TEXT in label_span.text

    def get_help_text(self, label):
        help_span = label.find('span', 'help-text')
        if not help_span:
            return None
        return help_span.text.strip()

    def get_error_text(self, label):
        error_span = label.find('span', 'error')
        if not error_span:
            return None
        return error_span.text.strip()

    def get_label(self, field):
        return field.find('label')

    def get_field(self, form, input_id=None, label=None):
        self.assertTrue(input_id or label)  # need one or the other
        if input_id:
            input = form.find('input', {'id': input_id})
            if not input:
                return None
            return input.find_parent('div', 'field')
        if label:
            fields = form.find_all('div', 'field')
            for field in fields:
                label_element = self.get_label(field)
                if label == self.get_label_name(label_element):
                    return field
        return None

    def assert_help_text_is(self, field, text):
        self.assertEqual(text, self.get_help_text(self.get_label(field)))

    def assert_error_is(self, field, error):
        self.assertEqual(error, self.get_error_text(self.get_label(field)))

    def assert_is_required(self, field):
        self.assertTrue(self.is_required(self.get_label(field)))

    def assert_is_optional(self, field):
        self.assertFalse(self.is_required(self.get_label(field)))

    def assert_has_num_fields(self, form, num_fields):
        fields = form.find_all('div', 'field')
        self.assertEqual(num_fields, len(fields))

    def assert_general_error(self, form, error):
        parent = form.parent
        self.assertIsNotNone(parent)
        error_list = parent.find('ul', 'errorlist')
        self.assertIsNotNone(error_list)
        self.assertIn(error, error_list.text)

    def assert_error(self, field, error):
        self.assertEqual(error, self.get_error_text(self.get_label(field)))

    def assert_field_error(self, form, field_name, error):
        field = self.get_field(form, input_id=field_name)
        if not field:
            field = self.get_field(form, label=field_name)
        self.assertIsNotNone(field)
        self.assert_error(field, error)