# Generated by Django 3.2.3 on 2024-02-19 14:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='subscriptions',
            new_name='subscription',
        ),
    ]