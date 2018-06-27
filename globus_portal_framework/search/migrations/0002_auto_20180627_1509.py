# Generated by Django 2.0.4 on 2018-06-27 15:09

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='minid',
            name='user',
        ),
        migrations.AddField(
            model_name='minid',
            name='users',
            field=models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='minid',
            name='description',
            field=models.CharField(max_length=128, null=True),
        ),
    ]