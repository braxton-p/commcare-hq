# Generated by Django 2.2.24 on 2021-11-24 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('motech', '0009_auto_20211122_2011'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connectionsettings',
            name='auth_type',
            field=models.CharField(
                blank=True,
                choices=[(None, 'None'), ('basic', 'HTTP Basic'), ('digest', 'HTTP Digest'),
                         ('bearer', 'Bearer Token'), ('oauth1', 'OAuth1'),
                         ('oauth2_pwd', 'OAuth 2.0 Password Grant'), ('oauth2_client', 'OAuth 2.0 Client Grant')],
                max_length=16,
                null=True
            ),
        ),
    ]