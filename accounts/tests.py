"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client
from bs4 import BeautifulSoup
from blog.tests import Counter
from utils.tests import FormTest
from django.contrib.auth.models import User
from accounts import forms
from mock import patch, Mock

COUNTER = Counter()


class LoginViewTest(FormTest):

    def setUp(self):
        self.c = Client()

    def testUnboundView(self):
        url = reverse('login_or_create_account')
        self.assertEquals('/accounts/login/', url)  # default login URL
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)

        # there should be two forms, one to login, and one to create a new account
        soup = BeautifulSoup(response.content)
        forms = soup.find_all('form')
        self.assertEqual(2, len(forms))

        login_form = forms[0]
        self.assert_has_num_fields(login_form, 2)

        email_field = self.get_field(login_form, label="Email")
        self.assert_is_required(email_field)
        self.assert_help_text_is(email_field, None)
        self.assert_error_is(email_field, None)

        password_field = self.get_field(login_form, label="Password")
        self.assert_is_required(password_field)
        self.assert_help_text_is(password_field, None)
        self.assert_error_is(password_field, None)
        button = login_form.find('button')
        self.assertEqual("Log In", button.text)

        create_account_form = forms[1]
        self.assert_has_num_fields(create_account_form, 5)

        first_name_field = self.get_field(create_account_form, label='First name')
        self.assert_is_required(first_name_field)
        self.assert_help_text_is(first_name_field, None)
        self.assert_error_is(first_name_field, None)

        last_name_field = self.get_field(create_account_form, label='Last name')
        self.assert_is_required(last_name_field)
        self.assert_help_text_is(last_name_field, None)
        self.assert_error_is(last_name_field, None)

        email_field = self.get_field(create_account_form, label='Email')
        self.assert_is_required(email_field)
        self.assert_help_text_is(email_field, None)
        self.assert_error_is(email_field, None)

        password1_field = self.get_field(create_account_form, label='Password')
        self.assert_is_required(password1_field)
        self.assert_help_text_is(password1_field, None)
        self.assert_error_is(password1_field, None)

        password2_field = self.get_field(create_account_form, label='Password confirmation')
        self.assert_is_required(password2_field)
        self.assert_help_text_is(password2_field, 'Enter the same password as above, for verification.')
        self.assert_error_is(password2_field, None)
        button = create_account_form.find('button')
        self.assertEqual("Create Account", button.text)


class CreateAccountTest(FormTest):

    def setUp(self):
        self.c = Client()

    def testFirstNameErrors(self):
        self.assert_form_error('id_first_name', '* This field is required.', self.c, first_name='')

        # Grrr, do not allow blank first names!
        self.assert_form_error('id_first_name', '* This field cannot be blank.', self.c, first_name='   ')

    def testFirstNameWithSpaces(self):
        # I think some people may have a first name with two or more words
        response = create_account(self.c, first_name="Mr. Kitty")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'my_account.html')
        user = User.objects.get(first_name="Mr. Kitty")
        self.assertIsNotNone(user)

    def testLastNameErrors(self):
        self.assert_form_error('id_last_name', '* This field is required.', self.c, last_name='')
        self.assert_form_error('id_last_name', '* This field cannot be blank.', self.c, last_name='  ')

    def testLastNameWithSpaces(self):
        # crazy Dutch last names
        response = create_account(self.c, last_name="Van Der Goot")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'my_account.html')
        user = User.objects.get(last_name='Van Der Goot')
        self.assertIsNotNone(user)

    def testEmailErrors(self):
        # poorly formatted email address
        self.assert_form_error('Email', '* Enter a valid e-mail address.', self.c, email="garbage address")

        # left blank
        self.assert_form_error('Email', '* This field is required.', self.c, email="")

    def testPasswordErrors(self):
        # TODO implement this test once I impose password restrictions.
        # at the moment almost anything goes
        pass

    def testPasswordConfirmationErrors(self):
        self.assert_form_error('id_password2', "* The two password fields didn't match.",
                               self.c, password1="pass1", password2="pass2")

    def testSuccess(self):
        response = create_account(self.c, first_name="Foo", last_name="Bar", email="someguy@foo.com",
                                  password1="pass1", password2="pass1")
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'my_account.html')
        user = User.objects.get(email='someguy@foo.com')
        self.assertEqual('Foo', user.first_name)
        self.assertEqual('Bar', user.last_name)
        self.assertEqual(forms.username_from_email(user.email), user.username)

        # log out and attempt to log back in
        self.c.logout()
        success = self.c.login(username=user.username, password="pass1")
        self.assertTrue(success)

    def testUsernameAlreadyExists(self):
        email = 'notsounique@email.com'
        create_account(self.c, email=email)
        self.assert_form_error('Email', '* A user with this email address already exists.', self.c, email=email)

    @patch('accounts.forms.username_from_email', Mock(side_effect=["username", "username"]))
    def testHashCollision(self):
        create_account(self.c, email="email1@foo.com")
        user = User.objects.get(email="email1@foo.com")
        self.assertEqual("username", user.username)  # assert that the mock is working
        self.assert_form_error('Email', "* Sorry, we were unable to generate a unique username from this email address. "
                                        "You will need to register with a different email address.", self.c,
                               email="email2@foo.com")

    def get_create_form(self, response):
        return BeautifulSoup(response.content).find('div', 'create-account').find('form')

    def assert_form_error(self, field, error, client, **kwargs):
        response = create_account(client, **kwargs)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login_or_create_account.html')
        form = self.get_create_form(response)
        self.assert_field_error(form, field, error)


class CustomerLogInTest(FormTest):

    def setUp(self):
        self.c = Client()

    def testEmailErrors(self):
        # poorly formatted email address
        self.assert_form_error('Email', '* Enter a valid e-mail address.', self.c, email="garbage address", password="pass")

        # left blank
        self.assert_form_error('Email', '* This field is required.', self.c, email="", password="pass")

    def testPasswordErrors(self):
        self.assert_form_error('Password', '* This field is required.', self.c, email="me@example.net", password="")

    def testBadCredentials(self):
        self.assert_form_error(None, 'Incorrect email/password combination. Note that both fields are case sensitive.',
                               self.c, email="foo@bar.com", password="somepassword")

    def testSuccess(self):
        create_account(self.c, email='rhyan@whois.com', password1='whois', password2='whois')
        response = log_in(self.c, email='rhyan@whois.com', password='whois')
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'my_account.html')

    def get_login_form(self, response):
        soup = BeautifulSoup(response.content)
        return soup.find('div', 'login').find('form')

    def assert_form_error(self, field, error, client, **kwargs):
        response = log_in(client, **kwargs)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login_or_create_account.html')
        form = self.get_login_form(response)
        self.assertIsNotNone(form)
        if field:
            self.assert_field_error(form, field, error)
        else:
            self.assert_general_error(form, error)


def log_in(client, **kwargs):
    data = make_login_post_data(**kwargs)
    return client.post(reverse('login_or_create_account'), data, follow=True)

def create_account(client, **kwargs):
    data = make_create_post_data(**kwargs)
    return client.post(reverse('login_or_create_account'), data, follow=True)

def make_login_post_data(**kwargs):
    return {
        'email': kwargs.pop('email'),
        'password': kwargs.pop('password'),
        'login': ''
    }

def make_create_post_data(**kwargs):
    first_name = kwargs.pop('first_name', 'Rhyan')
    last_name = kwargs.pop('last_name', 'Arthur')
    email = kwargs.pop('email', 'someone%d@fake.com' % COUNTER.next())
    password1 = kwargs.pop('password1', 'password')
    password2 = kwargs.pop('password2', 'password')
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'password1': password1,
        'password2': password2,
        'create': ''
    }
    return data
