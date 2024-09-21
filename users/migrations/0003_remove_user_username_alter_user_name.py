# Generated by Django 5.1.1 on 2024-09-17 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='username',
        ),
        migrations.AlterField(
            model_name='user',
            name='name',
            field=models.CharField(default='Anonymous User', max_length=255),
        ),
    ]
