# Generated by Django 2.2.6 on 2023-03-23 13:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_follow'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentAdmin',
            fields=[
                ('comment_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='posts.Comment')),
            ],
            bases=('posts.comment',),
        ),
        migrations.CreateModel(
            name='FollowAdmin',
            fields=[
                ('follow_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='posts.Follow')),
            ],
            bases=('posts.follow',),
        ),
    ]
