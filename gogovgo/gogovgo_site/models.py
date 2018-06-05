# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models
from django_extensions.db.models import TimeStampedModel
from cloudinary.models import CloudinaryField

from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from gogovgo.gogovgo_site.managers import ReviewManager
from gogovgo.gogovgo_site.constants import (
    GENDER_FEMALE,
    GENDER_MALE,
    GENDER_UNKNOWN,
    OFFICE_TYPE_FEDERAL,
    OFFICE_TYPE_STATE,
    REVIEW_APPROVED,
    REVIEW_PENDING,
    SENTIMENT_POSITIVE,
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    US_STATES
)

SENTIMENT_CHOICES = (
    (SENTIMENT_POSITIVE, SENTIMENT_POSITIVE),
    (SENTIMENT_NEGATIVE, SENTIMENT_NEGATIVE),
    (SENTIMENT_NEUTRAL, SENTIMENT_NEUTRAL)
)


class UserProfile(TimeStampedModel):
    GENDER_CHOICES = (
        (GENDER_MALE, GENDER_MALE),
        (GENDER_FEMALE, GENDER_FEMALE),
        (GENDER_UNKNOWN, GENDER_UNKNOWN)
    )
    user = models.OneToOneField(User, unique=True, db_constraint=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    gender = models.CharField(choices=GENDER_CHOICES, default=GENDER_UNKNOWN, max_length=16)
    country = models.CharField(max_length=2, null=True)
    state = models.CharField(max_length=2, null=True)
    zip_code = models.CharField(max_length=8, null=True)
    county = models.CharField(max_length=100, null=True)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    class Meta:
        app_label = 'gogovgo_site'


class GovernmentDepartment(TimeStampedModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return '%s' % self.name


class PublicOfficeTitle(TimeStampedModel):
    OFFICE_TYPE_CHOICES = (
        (OFFICE_TYPE_FEDERAL, OFFICE_TYPE_FEDERAL),
        (OFFICE_TYPE_STATE, OFFICE_TYPE_STATE)
    )

    url = models.SlugField(max_length=100)
    display_name = models.CharField(max_length=255)
    office_type = models.CharField(choices=OFFICE_TYPE_CHOICES,
                                   default=OFFICE_TYPE_FEDERAL, max_length=64)
    department = models.ForeignKey(GovernmentDepartment, on_delete=models.DO_NOTHING)
    city = models.CharField(null=True, blank=True, max_length=255)
    country = CountryField(default='US')

    def __str__(self):
        return '%s' % self.display_name


class Politician(TimeStampedModel):
    country = CountryField(default='US')
    public_office_title = models.ForeignKey(PublicOfficeTitle, on_delete=models.DO_NOTHING)
    first_name = models.CharField(blank=True, max_length=255)
    last_name = models.CharField(blank=True, max_length=255)
    political_party = models.CharField(blank=True, max_length=255)
    approval_rating = models.IntegerField(default=50)
    bio = models.TextField(blank=True)
    job_description = models.TextField(blank=True)
    hero_banner = CloudinaryField("hero_banner", default="")
    avatar = CloudinaryField("avatar")
    website = models.CharField(blank=True, max_length=255)
    phone_number = PhoneNumberField(blank=True)
    mailing_address = models.TextField(blank=True)

    def __str__(self):
        return '%s %s' % (self.first_name, self.last_name)

    @property
    def profile_url(self):
        return self.public_office_title.url

    @property
    def full_name(self):
        return self.first_name + " " + self.last_name


class Cabinet(TimeStampedModel):
    member = models.ForeignKey(Politician, related_name='leader')
    leader = models.ForeignKey(Politician, related_name='staff')

    def __str__(self):
        return '%s - %s' % (
            self.member.first_name + self.member.last_name,
            self.leader.first_name + self.leader.last_name
        )

    class Meta:
        app_label = 'gogovgo_site'


class Poll(TimeStampedModel):
    ACTION_CHOICES = (
        ('approve', 'Approve'),
        ('disapprove', 'Disapprove'),
        ('not_specified', 'Not Specified')
    )
    question = models.TextField()
    action = models.CharField(choices=ACTION_CHOICES, default='not_specified', max_length=128)

    def __str__(self):
        return '%s' % self.question

    class Meta:
        app_label = 'gogovgo_site'


class Tag(TimeStampedModel):
    politician = models.ForeignKey(Politician)
    value = models.CharField(max_length=100)
    weight = models.IntegerField(default=1)
    active = models.BooleanField(default=True)
    sentiment = models.CharField(choices=SENTIMENT_CHOICES,
                                 default=SENTIMENT_NEUTRAL, max_length=64)

    def __str__(self):
        return '%s' % self.value

    class Meta:
        app_label = 'gogovgo_site'
        verbose_name = 'Tag'


class TagWeight(models.Model):
    """Model to save individual weights for tags for a specific country and/or state"""
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    country = models.CharField(max_length=2)
    state = models.CharField(max_length=2, null=True)
    weight = models.IntegerField(default=1)


class HashTagsMixin(object):
    """
    Functionality to extract hash tags and approved them as review is approved
    """

    def __init__(self, *args, **kwargs):
        """Save initial data for comparison when saving the review in DB"""
        super(HashTagsMixin, self).__init__(*args, **kwargs)
        self._is_approved = self.status == REVIEW_APPROVED
        self._body = self.body

    def save(self, *args, **kwargs):
        """Extends logic when saving the review to DB"""
        # disable_auto_approve = kwargs.pop('disable_auto_approve', False)

        #   approved tags if review was approved
        if not self._is_approved and self.status == REVIEW_APPROVED:
            self.tags.all().update(active=True)

        #   save in DB
        response = super(HashTagsMixin, self).save(*args, **kwargs)

        #   tag extraction or deletion
        # approve = not disable_auto_approve and self.status == REVIEW_APPROVED
        # self.process_tags(approve=approve)
        self.process_tags(approve=True)

        return response

    def process_tags(self, approve):
        """
        Logic to process tag in the review

        Args:
            approve/boolean: Whether to approved new reviews or not

        Returns: Nothin!

        """
        old_tags = self.get_tags(self._body)
        new_tags = self.get_tags(self.body)
        if old_tags == new_tags:
            return

        tags_added = [tag for tag in new_tags if tag not in old_tags]
        tags_removed = [tag for tag in old_tags if tag not in new_tags]

        if tags_added:
            self.add_tags(tags_added, approve)

        if tags_removed:
            self.remove_tags(tags_removed)

    @staticmethod
    def get_tags(text):
        """
        Extract tags from text

        Args:
            text/string: Review's body text

        Returns: set array of reviews in text

        """
        if not text:
            return []
        text = text.replace('\r\n', ' ').replace('\n', ' ')
        tags = []
        for word in text.split(' '):
            if word.startswith('#'):
                tags.append(word[1:])
        return set(sorted(tags))

    def get_weights(self, tags):
        tag_ids = (tag.pk for tag in tags)
        weights = TagWeight.objects.filter(tag_id__in=tag_ids, country=self.country,
                                           state=self.state if self.country == 'US' else None)
        return {weight.tag_id: weight for weight in weights}

    def add_tags(self, tags, approve=False):
        """
        Handle addition of new tags to review

        The new tag are added to DB
        If the tag already exists in DB, it's weight is incremented

        Args:
            tags/list: new tags found in review
            approved/bool: Whether to approved new tag entries in DB or not

        Returns: Nothin!

        """
        db_tags = Tag.objects.filter(politician=self.politician,
                                     sentiment=self.sentiment,
                                     value__in=tags)
        weights = self.get_weights(db_tags)
        db_tags = {tag.value: tag for tag in db_tags}

        #   logic to add new tag or increment weight if tag already exists
        for _tag in tags:
            #   add or update tag
            try:
                tag = db_tags[_tag]
            except KeyError:
                query = {'politician': self.politician, 'value': _tag,
                         'sentiment': self.sentiment, 'active': approve}
                tag = Tag.objects.create(**query)
            else:
                tag.weight += 1
                tag.save()

            #   add or update tag weight
            try:
                weight = weights[tag.id]
            except KeyError:
                TagWeight.objects.create(tag=tag, country=self.country,
                                         state=self.state if self.country == 'US' else None)
            else:
                weight.weight += 1
                weight.save()

            self.tags.add(tag)

    def remove_tags(self, tags):
        """
        Handle removal of tags from review

        The weight of tag is decreased.
        If the tag is not being used anywhere else, it's deleted from Db

        Args:
            tags/list: tags that were removed from review

        Returns: Nothin!

        """
        query = {'politician': self.politician, 'sentiment': self.sentiment, 'value__in': tags}
        db_tags = Tag.objects.filter(**query)
        weights = self.get_weights(db_tags)
        for tag in db_tags:
            #   decrement weight
            #   delete if weight falls to zero
            _id = int(tag.pk)
            tag.weight -= 1
            if tag.weight > 0:
                tag.save()
            else:
                tag.delete()

            #   decrement individual weight
            try:
                weight = weights[_id]
            except KeyError:
                continue
            weight.weight -= 1
            if weight.weight > 0:
                weight.save()
            else:
                weight.delete()


class Review(HashTagsMixin, TimeStampedModel):
    REVIEW_STATUS_CHOICES = (
        (REVIEW_PENDING, REVIEW_PENDING),
        (REVIEW_APPROVED, REVIEW_APPROVED)
    )

    user = models.ForeignKey(
        User, models.SET_NULL,
        blank=True,
        null=True,
        db_constraint=False
    )
    politician = models.ForeignKey(Politician, db_constraint=False, related_name='reviews')
    sentiment = models.CharField(choices=SENTIMENT_CHOICES,
                                 default=SENTIMENT_NEUTRAL, max_length=64)
    city = models.CharField(null=True, blank=True, max_length=255)
    postal_code = models.CharField(max_length=8, null=True)
    county = models.CharField(max_length=100, null=True)
    state = models.CharField(choices=US_STATES, default='CA', max_length=120, null=True)
    country = CountryField(default='US')
    body = models.TextField(null=True)
    tags = models.ManyToManyField(Tag)
    status = models.CharField(choices=REVIEW_STATUS_CHOICES, default=REVIEW_PENDING, max_length=32)
    nlp_sentiment = models.CharField(choices=SENTIMENT_CHOICES,
                                     default=SENTIMENT_NEUTRAL, max_length=64)
    up_vote = models.IntegerField(default=0)
    down_vote = models.IntegerField(default=0)

    objects = ReviewManager()
    all = models.Manager()

    class Meta:
        ordering = ['-created']
        unique_together = ('user', 'politician')
        app_label = 'gogovgo_site'

    def __str__(self):
        return '{}: {}'.format(self.politician.full_name, self.pk)


class FlaggedReview(TimeStampedModel):
    review = models.OneToOneField(Review, primary_key=True)
    counter = models.PositiveSmallIntegerField(default=1)
    is_safe = models.BooleanField(default=False)

    class Meta:
        ordering = ['is_safe', '-counter']
        app_label = 'gogovgo_site'
