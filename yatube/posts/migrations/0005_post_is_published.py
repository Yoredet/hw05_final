# Generated by Django 2.2.19 on 2023-02-08 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_auto_20230209_0004'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='Публикация'),
        ),
    ]
