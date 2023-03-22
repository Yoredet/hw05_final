from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Comment, Follow, Group, Post, User

NUMBER_OF_POSTS: int = 10


def get_paginator(request, posts, NUMBER_OF_POSTS):
    pag = Paginator(posts, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    page_obj = pag.get_page(page_number)
    return page_obj


@cache_page(20)
def index(request):
    posts = Post.objects.select_related('author').all()
    context = {
        'page_obj': get_paginator(request, posts, NUMBER_OF_POSTS),
    }
    return render(request, 'posts/index.html', context)


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'page_obj': get_paginator(request, posts, NUMBER_OF_POSTS),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    if request.user.is_authenticated and Follow.objects.filter(
            author=author, user=request.user).exists():
        following = True
    else:
        following = False
    followers = Follow.objects.filter(author__username=username).count()
    context = {
        'author': author,
        'page_obj': get_paginator(request, posts, NUMBER_OF_POSTS),
        'following': following,
        'followers': followers,
        'user': request.user,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    is_edit = False
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if not form.is_valid():
        context = {
            'form': form,
            'is_edit': is_edit
        }
        return render(request, 'posts/create_post.html', context)
    post = form.save(commit=False)
    post.author = request.user
    post.pub_date = datetime.now()
    post.save()
    return redirect('posts:profile', username=post.author)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post)
    if request.method == "POST":
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.pub_date = datetime.now()
            post.save()
            return redirect('posts:post_detail', post_id)
    else:
        form = PostForm(instance=post)
    context = {
        'form': form,
        'is_edit': is_edit
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': get_paginator(request, posts, NUMBER_OF_POSTS)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(
            user=user,
            author=author,
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follower = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username
    )
    follower.delete()
    return redirect('posts:profile', username)
