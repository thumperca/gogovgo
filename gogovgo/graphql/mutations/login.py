"""
GraphQL mutation to user login
"""

import graphene
from graphql import GraphQLError

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.contrib.auth import login


class Validator:
    """Form validation"""

    def validate(self):
        self.validate_user()


    def validate_user(self):
        email = self.data.get('email', '')
        password = self.data.get('password', '')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return self.errors.append('Invalid login credentials')
        if not user.check_password(password):
            return self.errors.append('Invalid login credentials')


class Form(Validator):
    """Form to user signup"""

    def __init__(self, data):
        self.data = data
        self.cleaned_data = {}
        self.errors = []

    def is_valid(self):
        self.validate()
        return not self.errors


class Login(graphene.Mutation):
    """GraphQL mutation to user login"""

    class Input:
        email = graphene.String()
        password = graphene.String()

    login = graphene.Boolean()
    errors = graphene.List(graphene.String)

    @staticmethod
    def mutate(root, args, context, info):
        form = Form(data=args)
        if not form.is_valid():
            return Login(login=False, errors=form.errors)
        return Login(login=True, errors=[])