from http import HTTPStatus

from django.test import TestCase, Client
from posts.models import Group, Post, User


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись',
            author=cls.author,
            group=cls.group,
        )
        cls.url_template_public = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
        }
        cls.urls_template_private = {
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.user = User.objects.create(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        # Создаем автора
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_public_ursl_exists_for_guest(self):
        """Проверяем доступность публичных адресов гостевой учеткой"""
        for url in self.url_template_public.keys():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_urls_exists_for_quest(self):
        """Проверяем редиректы приватных адресов гостевой учеткой"""
        for url in self.urls_template_private.keys():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertRedirects(response,
                                     f'/auth/login/?next={url}')

    def test_private_urls_authorized_user(self):
        """Проверяем доступность приватных адресов залогиненной учеткой"""
        for url in self.urls_template_private.keys():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_public_urls_used_correct_template(self):
        """Проверяем соответствие шаблонов для публичных адресов"""
        for url, template in self.url_template_public.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_used_correct_template(self):
        """Проверяем соответствие шаблонов для приватных адресов"""
        for url, template in self.urls_template_private.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_page_not_exists_for_no_author(self):
        """
        Проверяем доступность страницы редактирования поста из под другой
        учетной записи
        """
        URL = f'/posts/{self.post.pk}/edit/'
        # Для автора
        response = self.post_author.get(URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        # Для авторизованного пользователя
        response = self.authorized_client.get(URL)
        self.assertRedirects(response, f'/posts/{self.post.pk}/')
        # Для неавторизованного пользователя
        response = self.guest_client.get(URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_not_exists(self):
        """
        Проверяем несуществующую страницу
        """
        URL = '/unexisting_page/'
        response = self.guest_client.get(URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
  