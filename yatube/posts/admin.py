from django.contrib import admin
from .models import Comment, Follow, Post, Group


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group',
        'is_published'
    )
    list_display_links = (
        'pk',
        'text'
    )
    list_editable = (
        'group',
        'is_published'
    )
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title',
                    'description')


@admin.register
class CommentAdmin(Comment):
    list_display = (
        'post',
        'author',
        'text',
        'created'
    )
    list_filter = (
        'text',
        'created',
        'author'
    )
    search_fields = (
        'post',
        'author',
        'text'
    )


@admin.register
class FollowAdmin(Follow):
    list_display = (
        'user',
        'author',
    )
    list_filter = (
        'user',
        'author',
    )
    search_fields = (
        'user',
        'author'
    )
