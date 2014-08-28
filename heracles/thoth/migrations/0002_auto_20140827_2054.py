# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('thoth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='lendable',
            name='owners',
            field=models.ManyToManyField(to='thoth.LendablesOwner'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='lendable',
            name='type',
            field=models.ForeignKey(default=0, to='thoth.LendableType'),
            preserve_default=False,
        ),
    ]
