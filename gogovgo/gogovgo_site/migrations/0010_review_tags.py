# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-02-27 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gogovgo_site', '0009_auto_20180227_0442'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='tags',
            field=models.ManyToManyField(to='gogovgo_site.Tag'),
        ),
    ]