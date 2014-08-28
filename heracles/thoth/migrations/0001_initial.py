# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import thoth.workflows
import django_xworkflows.models
from django.conf import settings
import thoth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(default=b'', blank=True)),
                ('state', thoth.models.StateField(default=b'pending_approval', max_length=16, workflow=thoth.workflows.BookingWorkflow(), choices=[(b'pending_approval', 'Pending Approval'), (b'approved', 'Approved'), (b'completed', 'Complete'), (b'cancelled', 'Cancelled')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(django_xworkflows.models.WorkflowEnabled, models.Model),
        ),
        migrations.CreateModel(
            name='BookingPart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('notes', models.TextField(default=b'', blank=True)),
                ('state', thoth.models.StateField(default=b'pending_approval', max_length=17, workflow=thoth.workflows.BookingPartWorkflow(), choices=[(b'pending_approval', 'Pending Approval'), (b'approved', 'Approved'), (b'equipment_out', 'In Use'), (b'equipment_checked', 'Equipment Checked'), (b'completed', 'Complete'), (b'cancelled', 'Cancelled')])),
                ('booking', models.ForeignKey(to='thoth.Booking')),
            ],
            options={
            },
            bases=(django_xworkflows.models.WorkflowEnabled, models.Model),
        ),
        migrations.CreateModel(
            name='Lendable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('slug', models.SlugField()),
                ('description', models.TextField()),
                ('warning_message', models.TextField(blank=True)),
                ('unavailable_message', models.TextField(blank=True)),
                ('available', models.BooleanField(default=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('inventory_id', models.CharField(max_length=64)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LendablesOwner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField()),
                ('owning_group', models.ForeignKey(to='auth.Group')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LendableType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', models.SlugField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bookingpart',
            name='lendable',
            field=models.ForeignKey(to='thoth.Lendable'),
            preserve_default=True,
        ),
    ]
