"""
GraphQL mutation to user signup
"""

import graphene
from graphql import GraphQLError

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User

from gogovgo.gogovgo_site.models import UserProfile


class Validator:
    """Form validation"""

    def validate(self):
        self.validate_name()
        self.validate_email()
        self.validate_username()
        self.validate_password()
        self.validators_country()
        self.validate_zipcode()

    def validate_name(self):
        name = self.data.get('name', '').strip()
        if not name:
            self.errors.append('The name field is required.')
        else:
            self.cleaned_data['name'] = name

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
            self.errors.append('The country must be selected.')
        else:
            self.cleaned_data['country'] = country

    def validate_zipcode(self):
        zipcode = self.data.get('zipcode', '').strip()
        country = self.data.get('country', '').strip()
        if country == 'United States of America':
            if not zipcode:
                self.errors.append('The zipcode field is required.')
            else:
                self.cleaned_data['zipcode'] = zipcode



class Form(Validator):
    """Form to user signup"""

    def __init__(self, data):
        self.data = data
        self.cleaned_data = {}
        self.errors = []

    def is_valid(self):
        self.validate()
        return not self.errors

    def save(self):
        pass



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
        # return Signup(created=True, errors=['created'])
        form.save()
        return Signup(created=True, errors=[])
