from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Неавтор')

        cls.note = Note.objects.create(
            title='Название заметки',
            text='Текст заметки',
            slug='note',
            author=cls.author
        )

        cls.urls = {
            'home': reverse_lazy('notes:home'),
            'signup': reverse_lazy('users:signup'),
            'login': reverse_lazy('users:login'),
            'logout': reverse_lazy('users:logout'),
            'list': reverse_lazy('notes:list'),
            'add': reverse_lazy('notes:add'),
            'success': reverse_lazy('notes:success'),
            'edit': reverse_lazy('notes:edit', args=[cls.note.slug]),
            'delete': reverse_lazy('notes:delete', args=[cls.note.slug]),
            'detail': reverse_lazy('notes:detail', args=[cls.note.slug]),
        }

        cls.author_client = cls.client_class()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = cls.client_class()
        cls.not_author_client.force_login(cls.not_author)

    def test_pages_availability(self):
        """Страницы (index, регистрация, вход) доступны всем"""
        urls = ['home', 'signup', 'login']
        for url_key in urls:
            with self.subTest(url=url_key):
                response = self.client.get(self.urls[url_key])
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_user(self):
        """Редирект анонимных пользователей"""
        urls = ['list', 'add', 'edit', 'delete', 'detail']
        for url_key in urls:
            with self.subTest(url=url_key):
                response = self.client.get(self.urls[url_key])
                self.assertRedirects(
                    response,
                    f'{self.urls["login"]}?next={self.urls[url_key]}')

    def test_authenticated_user_access(self):
        """Аутентифицированному пользователю доступны
        страницы списка заметок и добавления заметок
        """
        urls = ['list', 'add', 'success']
        for url_key in urls:
            with self.subTest(url=url_key):
                response = self.author_client.get(self.urls[url_key])
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_to_note_pages(self):
        """Доступ к заметкам, страницам редактирования и
        удаления для авторов и неавторов
        """
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.not_author_client, HTTPStatus.NOT_FOUND),
        )
        urls = ['edit', 'delete', 'detail']
        for client, expected_status in users_statuses:
            with self.subTest(client=client):
                for url_key in urls:
                    with self.subTest(url=f'{url_key} проверка доступа'):
                        response = client.get(self.urls[url_key])
                        self.assertEqual(response.status_code, expected_status)
