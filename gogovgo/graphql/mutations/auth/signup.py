"""
GraphQL mutation to user signup
"""

import graphene
from graphql import GraphQLError

from django_countries import countries

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.contrib.auth import login


from gogovgo.gogovgo_site.models import UserProfile
from gogovgo.scripts.geocode import get_location_info


class LocationValidator:
    """Validation location"""

    def validate_location(self):
        if self.errors:
            return
        country, zipcode = self.cleaned_data['country'], self.cleaned_data['zipcode']
        if country != 'US':
            return

        location_data = get_location_info(zipcode)
        if not location_data:
            return self.errors.append('The zip code field is invalid.')

        self.cleaned_data.update(location_data)


class FormValidator:
    """Form validation"""

    def validate_form(self):
        self.validate_name()
        self.validate_email()
        self.validate_username()
        self.validate_password()
        self.validators_country()
        self.validate_zipcode()

    def validate_name(self):
        name = self.data.get('name', '').strip()
        if not name:
            return self.errors.append('The name field is required.')

        name_parts = name.split(' ')
        first_name = name_parts[0]
        last_name = ' '.join(name_parts[1:])

        self.cleaned_data['first_name'] = first_name
        self.cleaned_data['last_name'] = last_name

    def validate_email(self):
        email = self.data.get('email', '').strip().lower()
        if not email:
            return self.errors.append('The email field is required.')
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            self.errors.append('This email address is already in use.')

        try:
            validate_email(email)
        except ValidationError:
            self.errors.append('The email field is invalid.')
        else:
            self.cleaned_data['email'] = email

    def validate_username(self):
        username = self.data.get('username', '').strip()
        if not username:
            self.errors.append('The username field is required.')
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            self.cleaned_data['username'] = username
        else:
            self.errors.append('This username is already in use.')

    def validate_password(self):
        password = self.data.get('password', '')
        if not password:
            self.errors.append('The password field is required.')
        elif len(password) < 6:
            self.errors.append('The password must be atleast 6 characters long.')
        else:
            self.cleaned_data['password'] = password

    def validators_country(self):
        country = self.data.get('country', '').strip()
        if not country:
            return self.errors.append('The country must be selected.')

        valid_countries = (short for short, _ in countries)
        if country not in valid_countries:
            return self.errors.append('The country field is invalid.')

        self.cleaned_data['country'] = country

    def validate_zipcode(self):
        zipcode = self.data.get('zipcode', '').strip()
        country = self.data.get('country', '').strip()
        if country != 'US':
            return

        if not zipcode:
            return self.errors.append('The zipcode field is required.')
        if len(zipcode) != 5:
            return self.errors.append('The zipcode field must be 5 characters long.')

        cleaned_zipcode = ''.join((x for x in zipcode if x.isdigit()))
        if cleaned_zipcode != zipcode:
            return self.errors.append('The zipcode field is invalid.')

        self.cleaned_data['zipcode'] = zipcode


class Form(FormValidator, LocationValidator):
    """Form to user signup"""

    def __init__(self, data):
        self.data = data
        self.cleaned_data = {}
        self.errors = []

    def is_valid(self):
        self.validate_form()
        self.validate_location()
        return not self.errors

    def save(self):
        data = self.cleaned_data

        #   create user
        user = User(username=data['username'],
                    email=data['email'],
                    first_name=data['first_name'],
                    last_name=data['last_name'])
        user.set_password(data['password'])
        user.save()

        #   create userprofile
        UserProfile.objects.create(user=user,
                                   country=data['country'],
                                   state=data.get('state'),
                                   county=data.get('county'),
                                   zip_code=data.get('zipcode'),
                                   longitude=data.get('longitude'),
                                   latitude=data.get('latitude'))
        return user


class Signup(graphene.Mutation):
    """GraphQL mutation to user signup"""

    class Input:
        name = graphene.String()
        email = graphene.String()
        username = graphene.String()
        password = graphene.String()
        country = graphene.String()
        zipcode = graphene.String()

    created = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, args, context, info):
        form = Form(data=args)
        if not form.is_valid():
            return Signup(created=False, errors=form.errors)
        form.save()
        return Signup(created=True, errors=[])
