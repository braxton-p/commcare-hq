# Generated by Django 2.2.27 on 2022-02-28 10:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('oauth_integrations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LiveGoogleSheetSchedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('export_config_id', models.CharField(db_index=True, max_length=250)),
                ('is_active', models.BooleanField(default=True)),
                ('start_time', models.IntegerField(default=200)),
                ('google_sheet_id', models.CharField(max_length=250)),
            ],
        ),
    ]
