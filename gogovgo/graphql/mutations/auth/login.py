"""
GraphQL mutation to user login
"""

import graphene
from graphql import GraphQLError
from graphene_django.types import DjangoObjectType

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.models import User
from django.contrib.auth import login


class UserLoginProvider:
    """Logic to validate and login a user"""

    def __init__(self, data):
        self.data = data
        self.user = None

    def is_valid(self):
        self.validate_credentials()
        return True if self.user else False

    def validate_credentials(self):
        email = self.data.get('email', '')
        password = self.data.get('password', '')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            pass
        else:
            if user.check_password(password):
                self.user = user

    def login(self):
        return self.user


class AuthUserType(DjangoObjectType):
    class Meta:
        model = User

    token = graphene.String()

    def resolve_token(self, *args):
        return 'token_abc123'


class Login(graphene.Mutation):
    """GraphQL mutation to user login"""

    class Input:
        email = graphene.String()
        password = graphene.String()

    success = graphene.Boolean()
    user = graphene.Field(AuthUserType)

    @staticmethod
    def mutate(root, args, context, info):
        provider = UserLoginProvider(data=args)
        if not provider.is_valid():
            return Login(success=False, user=None)
        user = provider.login()
        return Login(success=True, user=user)
