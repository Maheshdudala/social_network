# Generated by Django 5.1.1 on 2024-09-17 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_friendrequest_cooldown_expires_at_blockeduser'),
    ]

    operations = [
        migrations.AddField(
            model_name='friendrequest',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
