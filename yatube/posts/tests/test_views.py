import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms

from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание тестовой группы'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.author,
            group=cls.group,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем автора поста
        self.post_author = Client()
        self.post_author.force_login(self.author)
        cache.clear()

    def check_post(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)
            self.assertEqual(post.image, self.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        template_pages_names = [
            (
                'posts/index.html',
                reverse('posts:index')
            ),
            (
                'posts/group_list.html', reverse
                ('posts:group_list', kwargs={'slug': self.group.slug})
            ),
            (
                'posts/profile.html', reverse
                ('posts:profile', kwargs={'username': self.user.username})
            ),
            (
                'posts/post_detail.html', reverse
                ('posts:post_detail', kwargs={'post_id': self.post.pk})
            ),
            (
                'posts/create_post.html', reverse
                ('posts:post_edit', kwargs={'post_id': self.post.pk})
            ),
            (
                'posts/create_post.html', reverse
                ('posts:post_create')
            )
        ]
        for template, reverse_name in template_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контектом"""
        response = self.post_author.get(reverse('posts:index'))
        self.check_post(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        response = (self.post_author.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})))
        self.assertEqual(response.context['group'], self.group)
        self.check_post(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Шаблон profile.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.author}))
        self.assertEqual(response.context['user'], self.user)
        self.check_post(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.post_author.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}))
        self.assertEqual(response.context.get('post'), self.post)
        self.check_post(response.context['post'])

    def test_create_post_form(self):
        """Форма создания поста"""
        response = self.authorized_client.get(
            reverse(
                'posts:post_create'))
        forms_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in forms_fields.items():
            with self.subTest(expected=expected):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_form(self):
        response = self.post_author.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}))
        forms_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in forms_fields.items():
            with self.subTest(expected=expected):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_on_index_group_profile_pages(self):
        """Дополнительная проверка при создании поста"""
        responses_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug
            }),
            reverse('posts:profile', kwargs={
                'username': self.post.author
            })
        ]
        for i in responses_list:
            with self.subTest(i=i):
                response = self.post_author.get(i)
                post = response.context['page_obj'][0]
                self.assertEqual(post, self.post)
        # Проверяем что поста нет в другой группе
        another_group = Group.objects.create(
            title='Вторая тестовая группа',
            slug='second-test-slug',
            description='Тестовое описание второй тестовой группы'
        )
        response = self.post_author.get(
            reverse('posts:group_list', kwargs={
                'slug': another_group.slug
            })
        )
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание тестовой группы'
        )
        cls.NUMBER_OF_POSTS: int = 13
        cls.NUMBER_OF_POSTS_ON_FIRST_PAGE: int = 10
        cls.NUMBER_OF_POSTS_ON_SECOND_PAGE: int = 3
        posts = [
            Post(text=f'Пост намба {post}', group=cls.group,
                 author=cls.user,) for post in range(
                cls.NUMBER_OF_POSTS)
        ]
        Post.objects.bulk_create(posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_on_pages(self):
        """
        Проверка пагинации на страницах index, group_list, profile
        """
        reverse_list = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        ]
        for i in reverse_list:
            with self.subTest(i=i):
                response = self.authorized_client.get(i)
                self.assertEqual(len(response.context['page_obj']),
                                 self.NUMBER_OF_POSTS_ON_FIRST_PAGE)
                self.assertEqual(len(self.authorized_client.get(
                    i + '?page=2').context.get('page_obj')),
                    self.NUMBER_OF_POSTS_ON_SECOND_PAGE
                )


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='post_author'
        )
        cls.follower = User.objects.create(
            username='post_follower'
        )
        cls.post = Post.objects.create(
            text='Лайк, подписка, и всё тут',
            author=cls.author
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.follower_client = Client()
        self.follower_client.force_login(self.follower)

    def test_follow(self):
        """Проверка подписки на пользователя"""
        count_follow = Follow.objects.count()
        self.follower_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        follow = Follow.objects.filter(
            author=self.author,
            user=self.follower
        ).exists()
        self.assertTrue(follow)

    def test_unfollow(self):
        """Проверка отписки от пользователя"""
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_new_post_appers_in_subscribers(self):
        """
        Новая запись пользователя появляется в ленте только тех,
        кто на него подписан
        """
        post = Post.objects.create(
            author=self.author,
            text='ОНОТОЛЕ ОТАКЭ'
        )
        Follow.objects.create(
            user=self.follower,
            author=self.author
        )
        response = self.follower_client.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertIn(post, response.context['page_obj'].object_list)
        response = self.post_author.get(
            reverse(
                'posts:follow_index'
            )
        )
        self.assertNotIn(post, response.context['page_obj'].object_list)

    def test_double_subscription(self):
        """Нельзя подписаться два раза на одного автора."""
        self.follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        self.follower_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        count = Follow.objects.filter(author_id=self.author,
                                      user_id=self.follower
                                      ).count()
        self.assertEqual(count, 1)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.author
        )

    def setUp(self):
        self.post_author = Client()
        self.post_author.force_login(self.author)
        cache.clear()

    def test_cache_index_page(self):
        """Проверяем работу кэша"""
        new_post = Post.objects.create(
            text='Тестируем кэш',
            author=self.author
        )
        response_add = self.post_author.get(
            reverse('posts:index')).content
        new_post.delete()
        response_delete = self.post_author.get(
            reverse('posts:index')).content
        self.assertEqual(response_add, response_delete)
        cache.clear()
        response_cache_clear = self.post_author.get(
            reverse('posts:index')).content
        self.assertNotEqual(response_add,
                            response_cache_clear)
