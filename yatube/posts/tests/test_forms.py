import shutil
import tempfile
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Comment, Group, Post
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание тестовой группы'
        )
        cls.author = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
            group=cls.group
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Проверка создания поста авторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
                image='posts/small.gif'
            ).exists()
        )

    def test_create_post_without_login(self):
        """Проверка создания поста неавторизованным пользователем"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовая запись',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_authorized_user(self):
        """Проверка редактирования поста"""
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            response.context.get('post').pk,
            self.post.pk)
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированный текст',
                group=self.group.id
            )
        )

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизованным юзверем"""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Комментарий к посту'}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        print(response.context['comments'][0])
        self.assertEqual(response.context['comments'][0],
                         Comment.objects.latest('id'))
        self.assertRedirects(response, reverse(
            'posts:post_detail', args={self.post.pk}
        ))

    def test_non_authorized_user_create_comment(self):
        """Проверка создания комментария неавторизованным юзером"""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Комментарий к посту'}
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse(
                'posts:add_comment', kwargs={'post_id': self.post.pk}
            )
        )
