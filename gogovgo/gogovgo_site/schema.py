from __future__ import division
import math
from datetime import timedelta

import graphene
from cloudinary.models import CloudinaryField
from cloudinary import CloudinaryImage
from graphene_django.converter import convert_django_field
from graphene_django.types import DjangoObjectType
from graphql import GraphQLError
from django_countries import countries

from django.utils import timezone
from django.contrib.auth.models import User
from django.db import IntegrityError

from gogovgo.gogovgo_site import models
from gogovgo.gogovgo_site.constants import SENTIMENT_NEGATIVE, SENTIMENT_POSITIVE
from gogovgo.gogovgo_site.constants import REVIEW_APPROVED, US_STATES
from gogovgo.scripts.geocode import get_county

from gogovgo.graphql.mutations import Contact
from gogovgo.graphql.mutations import Signup


@convert_django_field.register(CloudinaryField)
def my_convert_function(field, registry=None):
    return graphene.String()


class GovernmentDepartmentType(DjangoObjectType):
    class Meta:
        model = models.GovernmentDepartment


class PublicOfficeTitleType(DjangoObjectType):
    class Meta:
        model = models.PublicOfficeTitle


def connection_for_type(_type):
    class Connection(graphene.Connection):
        total_count = graphene.Int()

        class Meta:
            name = _type._meta.name + 'Connection'
            node = _type

        def resolve_total_count(self, args, context, info):
            return self.length

    return Connection


class UserType(DjangoObjectType):
    class Meta:
        model = User


UserType.Connection = connection_for_type(UserType)


class UserProfileType(DjangoObjectType):
    class Meta:
        model = models.UserProfile


UserProfileType.Connection = connection_for_type(UserProfileType)


class PollType(DjangoObjectType):
    class Meta:
        model = models.Poll


PollType.Connection = connection_for_type(PollType)


class PoliticianType(DjangoObjectType):
    hero_url = graphene.String()
    avatar_url = graphene.String()
    thumbnail_tag = graphene.String()
    approval_count = graphene.Int()
    disapproval_count = graphene.Int()

    class Meta:
        model = models.Politician

    def resolve_thumbnail_tag(self, *args):
        if self.avatar:
            src = CloudinaryImage(str(self.avatar)).build_url(width=263, height=225)
            return src
        else:
            return ""

    def resolve_hero_url(self, *args):
        if self.hero_banner:
            src = CloudinaryImage(str(self.hero_banner)).build_url()
            return src
        else:
            return ""

    def resolve_avatar_url(self, *args):
        if self.avatar:
            src = CloudinaryImage(str(self.avatar)).build_url()
            return src
        else:
            return ""

    def resolve_approval_count(self, *args):
        query = {
            'politician': self,
            'sentiment': SENTIMENT_POSITIVE,
            'status': REVIEW_APPROVED
        }
        return models.Review.objects.filter(**query).count()

    def resolve_disapproval_count(self, *args):
        query = {
            'politician': self,
            'sentiment': SENTIMENT_NEGATIVE,
            'status': REVIEW_APPROVED
        }
        return models.Review.objects.filter(**query).count()


PoliticianType.Connection = connection_for_type(PoliticianType)


class LocationHelper(object):

    @staticmethod
    def get_country(review):
        countries_dict = {short_name: long_name for short_name, long_name in countries}
        return countries_dict[review.country]

    @staticmethod
    def get_state(review):
        states = {short_name: long_name for short_name, long_name in US_STATES}
        return states[review.state]


class ReviewType(DjangoObjectType):
    tags = graphene.List(graphene.String)
    location = graphene.String()

    class Meta:
        model = models.Review

    def resolve_tags(self, *args):
        return [tag.value for tag in self.tags.all()]

    def resolve_location(self, *args):
        location = LocationHelper.get_country(review=self).replace(' of America', '')
        if self.country == 'US' and self.state:
            location += ', ' + LocationHelper.get_state(review=self)
        return location


ReviewType.Connection = connection_for_type(ReviewType)


class CabinetType(DjangoObjectType):
    class Meta:
        model = models.Cabinet


class Tag(graphene.InputObjectType):
    id = graphene.Int()
    name = graphene.String()


class CreateReview(graphene.Mutation):
    class Input:
        politician_id = graphene.ID()
        sentiment = graphene.String()
        full_name = graphene.String()
        email_address = graphene.String()
        body = graphene.String()
        location = graphene.String()
        tags = graphene.List(Tag)

    ok = graphene.Boolean()
    review = graphene.Field(lambda: ReviewType)

    @staticmethod
    def mutate(root, args, context, info):
        user = None

        if all(key in args for key in ['full_name', 'email_address']):
            fullname = args.get('full_name', '')
            email_address = args.get('email_address', '').lower()
            split_name = fullname.split(' ')
            first_name = split_name[0]
            last_name = ' '.join(split_name[1:]) if len(split_name) > 1 else ''

            try:
                user = User.objects.get(email=email_address)
            except models.User.DoesNotExist:
                user = models.User.objects.create(
                    username=email_address,
                    email=email_address,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=False
                )

            del args['full_name']
            del args['email_address']

        location = args['location']
        state, country, postal_code = location.split(',')

        county = None
        if country == 'US':
            county = get_county(postal_code, state)
            if not country:
                raise GraphQLError('The postal code is invalid')

        try:
            review = models.Review(
                politician_id=args['politician_id'],
                user=user,
                state=state.strip() or None,
                county=county,
                postal_code=postal_code.strip() or None,
                country=country.strip(),
                sentiment=args['sentiment'],
                status=REVIEW_APPROVED,
            )
            review.body = args['body']
            review.save()
        except IntegrityError:
            raise GraphQLError('You have already submitted a review for this politician')

        ok = True
        return CreateReview(review=review, ok=ok)


class UpdateReview(graphene.Mutation):
    class Input:
        review_id = graphene.ID()
        up_vote = graphene.Boolean()

    ok = graphene.Boolean()
    review = graphene.Field(lambda: ReviewType)

    @staticmethod
    def mutate(root, args, context, info):
        review = models.Review.objects.get(pk=args['review_id'])
        if args['up_vote']:
            review.up_vote += 1
        else:
            review.down_vote += 1

        review.save()

        ok = True
        return CreateReview(review=review, ok=ok)


class ReportReview(graphene.Mutation):
    class Input:
        review_id = graphene.ID()

    review = graphene.Field(lambda: ReviewType)

    @staticmethod
    def mutate(root, args, context, info):
        try:
            review = models.Review.objects.get(pk=args['review_id'])
        except models.Review.DoesNotExist:
            raise GraphQLError('The review_id is incorrect')

        try:
            flag = models.FlaggedReview.objects.get(review=review)
        except models.FlaggedReview.DoesNotExist:
            flag = models.FlaggedReview(review=review, counter=0)

        limit = 32000  # rounded limit to nearest thousand for PositiveSmallIntegerField
        if not flag.is_safe and flag.counter < limit:
            flag.counter += 1
            flag.save()

        return CreateReview(review=review)


class Mutations(graphene.ObjectType):
    create_review = CreateReview.Field()
    update_review = UpdateReview.Field()
    report_review = ReportReview.Field()
    contact = Contact.Field()
    signup = Signup.Field()


class ReviewPaginationHelper(object):
    """Helper class to get reviews for a politician as paginated Query"""

    #   show 20 reviews per page
    per_page = 20

    def __init__(self, *args, **kwargs):
        self._id = kwargs['id']
        self.page = kwargs['page'] or 1
        self.country = kwargs['country']
        self.state = kwargs['state']
        self.timelimit = kwargs['timelimit']
        self.reviews = {SENTIMENT_NEGATIVE: [], SENTIMENT_POSITIVE: []}

    def get_reviews(self):
        positive_reviews = self._get(sentiment=SENTIMENT_POSITIVE)
        negative_reviews = self._get(sentiment=SENTIMENT_NEGATIVE)
        total_pages = max(positive_reviews['totalPages'], negative_reviews['totalPages'])
        return {
            'page': self.page,
            'pages': total_pages,
            'hasMore': total_pages > self.page,
            'positive': positive_reviews['data'],
            'negative': negative_reviews['data'],
            'positive_tags': self.get_tags(sentiment=SENTIMENT_POSITIVE),
            'negative_tags': self.get_tags(sentiment=SENTIMENT_NEGATIVE)
        }

    def _get(self, sentiment):
        start = (self.page - 1) * self.per_page
        end = self.page * self.per_page

        query = {'politician_id': self._id, 'sentiment': sentiment, 'status': REVIEW_APPROVED}
        if self.country != 'all':
            query['country'] = self.country
        if self.country == 'US' and self.state != 'all':
            query['state'] = self.state
        if self.timelimit != 'all':
            limit = timezone.now().date() - timedelta(days=int(self.timelimit))
            query['created__gte'] = limit

        reviews = models.Review.objects.filter(**query)
        total_reviews = len(reviews)
        self.reviews[sentiment] = reviews

        total_pages = math.ceil(total_reviews / self.per_page)
        reviews = reviews.order_by('-up_vote').select_related('user')[start:end]
        return {'data': reviews, 'totalPages': total_pages}

    def get_tags(self, sentiment):
        """
        Get  tags for a politician

        Args:
            sentiment: Type of tags to selected i.e. positive or negative

        Returns: list of tags

        """
        reviews = self.reviews[sentiment]
        review_ids = [review.id for review in reviews]

        tags = models.Review.tags.through.objects.filter(review_id__in=review_ids)
        tags = tags.values_list('tag_id', flat=True)

        if self.country == 'all':
            tags = models.Tag.objects.filter(id__in=tags, active=True)
            tags = tags.order_by('-weight').values_list('value', 'weight')[:10]
        else:
            tags = models.TagWeight.objects.filter(tag_id__in=tags, tag__active=True,
                                                   country=self.country)
            if self.country == 'US' and self.state != 'all':
                tags = tags.filter(state=self.state)
            tags = tags.order_by('-weight')[:10]
            tags = ((tag.tag.value, tag.weight) for tag in tags)
        return tags


class ReviewsPaginatedType(graphene.ObjectType):
    page = graphene.Int()
    pages = graphene.Int()
    hasMore = graphene.Boolean()
    positive = graphene.List(ReviewType)
    negative = graphene.List(ReviewType)
    positive_tags = graphene.List(graphene.List(graphene.String))
    negative_tags = graphene.List(graphene.List(graphene.String))


class MapEntryData(graphene.ObjectType):
    code = graphene.String()
    name = graphene.String()
    value = graphene.Float()
    positive = graphene.Float()
    negative = graphene.Float()


class MapDataType(graphene.ObjectType):
    data = graphene.List(MapEntryData)


class MapHelper:

    @staticmethod
    def get_world_data(politician_id):
        reviews = models.Review.objects.filter(politician_id=politician_id, status=REVIEW_APPROVED)
        reviews = tuple(reviews.values_list('country', 'sentiment'))

        total_reviews = len(reviews)
        count = {}
        for country, sentiment in reviews:
            try:
                count[country][sentiment] += 1
            except KeyError:
                count[country] = {'positive': 0, 'negative': 0}
                count[country][sentiment] = 1

        countries_dict = {short_name: long_name for short_name, long_name in countries}
        data = []
        for country in count:
            _data = count[country]
            total = _data['positive'] + _data['negative']
            if not total:
                entry = MapEntryData(code=country, name=country, positive=0, negative=0, value=0.5)
            else:
                positive = round(_data['positive'] / total * 100, 2)
                negative = round(_data['negative'] / total * 100, 2)
                value = _data['positive'] / total
                entry = MapEntryData(code=country, name=country, value=value,
                                     positive=positive, negative=negative)
            data.append(entry)
        return data

    @staticmethod
    def get_us_data(politician_id):
        query = {'politician_id': politician_id, 'status': REVIEW_APPROVED, 'country': 'US'}
        reviews = models.Review.objects.filter(**query)
        reviews = tuple(reviews.values_list('state', 'sentiment'))

        total_reviews = len(reviews)
        count = {}

        for state, sentiment in reviews:
            try:
                count[state][sentiment] += 1
            except KeyError:
                count[state] = {'positive': 0, 'negative': 0}
                count[state][sentiment] = 1

        states = {short_name: long_name for short_name, long_name in US_STATES}

        data = []
        for state in states:
            _data = count.get(state, {'positive': 0, 'negative': 0})
            total = _data['positive'] + _data['negative']
            if not total:
                entry = MapEntryData(
                    code=state, name=states[state], positive=0, negative=0, value=0.5)
            else:
                positive = round(_data['positive'] / total * 100, 2)
                negative = round(_data['negative'] / total * 100, 2)
                value = _data['positive'] / total
                entry = MapEntryData(code=state, name=states[state], value=value,
                                     positive=positive, negative=negative)
            data.append(entry)
        return data

    @staticmethod
    def get_state_data(politician_id, state):
        query = {'politician_id': politician_id,
                 'status': REVIEW_APPROVED,
                 'country': 'US',
                 'state': state}
        reviews = models.Review.objects.filter(**query).exclude(county=None)
        reviews = tuple(reviews.values_list('county', 'sentiment'))

        total_reviews = len(reviews)
        count = {}
        for county, sentiment in reviews:
            try:
                count[county][sentiment] += 1
            except KeyError:
                count[county] = {'positive': 0, 'negative': 0}
                count[county][sentiment] = 1

        data = []
        for county in count:
            _data = count[county]
            total = _data['positive'] + _data['negative']
            if not total:
                entry = MapEntryData(code=county, name=county, positive=0, negative=0, value=0.5)
            else:
                positive = round(_data['positive'] / total * 100, 2)
                negative = round(_data['negative'] / total * 100, 2)
                value = _data['positive'] / total
                entry = MapEntryData(code=county, name=county, value=value,
                                     positive=positive, negative=negative)
            data.append(entry)
        return data


class Query(graphene.AbstractType):
    users = graphene.List(UserType)
    userprofiles = graphene.List(UserProfileType)
    politician = graphene.Field(
        PoliticianType,
        id=graphene.ID(),
        url=graphene.String()
    )
    all_politicians = graphene.List(PoliticianType)
    cabinet_members = graphene.List(CabinetType)
    polls = graphene.List(PollType)
    public_office_title_types = graphene.List(
        PublicOfficeTitleType,
        country=graphene.String()
    )
    review = graphene.Field(ReviewType, id=graphene.ID())
    reviews = graphene.Field(ReviewsPaginatedType,
                             id=graphene.Int(),
                             page=graphene.Int(),
                             country=graphene.String(),
                             state=graphene.String(),
                             timelimit=graphene.String())
    mapdata = graphene.Field(MapDataType, id=graphene.Int(), maptype=graphene.String())

    def resolve_mapdata(self, args, context, info):
        map_type = args['maptype']
        max_value = 0
        if map_type == 'world':
            map_data = MapHelper.get_world_data(args['id'])
        elif map_type == 'us':
            map_data = MapHelper.get_us_data(args['id'])
        elif map_type.startswith('us-'):
            state = map_type.replace('us-', '').upper()
            map_data = MapHelper.get_state_data(args['id'], state)
        else:
            raise GraphQLError('Invalid map type')
        return MapDataType(data=map_data)

    @graphene.resolve_only_args
    def resolve_users(self):
        return User.objects.all()

    @graphene.resolve_only_args
    def resolve_userprofiles(self):
        # We can easily optimize query count in the resolve method
        return models.UserProfile.objects.select_related('user').all()

    @graphene.resolve_only_args
    def resolve_polls(self):
        return models.Poll.objects.all()

    @graphene.resolve_only_args
    def resolve_all_politicians(self):
        return models.Politician.objects.all()

    def resolve_politician(self, args, context, info):
        title_url = args.get('url')
        return models.Politician.objects.get(public_office_title__url=title_url)

    @graphene.resolve_only_args
    def resolve_public_office_title_types(self, **kwargs):
        country = kwargs.get('country')
        return models.PublicOfficeTitle.objects.filter(country=country).all()

    def resolve_reviews(self, args, context, info):
        helper = ReviewPaginationHelper(**args)
        reviews = helper.get_reviews()
        return ReviewsPaginatedType(**reviews)

    def resolve_review(self, args, context, info):
        id = args.get('id')
        return models.Review.objects.get(pk=id)

    @graphene.resolve_only_args
    def resolve_cabinet_members(self):
        return models.Cabinet.objects.all()
