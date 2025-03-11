from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    home_url = 'notes:home'
    signup_url = 'users:signup'
    login_url = 'users:login'
    list_url = 'notes:list'
    add_url = 'notes:add'
    success_url = 'notes:success'
    edit_url = 'notes:edit'
    delete_url = 'notes:delete'
    detail_url = 'notes:detail'

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

    def test_pages_availability(self):
        """Страницы(index, регистрация, вход и выход) доступны всем"""
        urls = (
            self.home_url,
            self.signup_url,
            self.login_url,
            # 'users:logout',
        )
        for name in urls:
            with self.subTest(name=name):
                response = self.client.get(reverse_lazy(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_user(self):
        """Редирект анонимных пользователей"""
        urls = (
            (self.list_url, ()),
            (self.add_url, ()),
            (self.edit_url, (self.note.slug,)),
            (self.delete_url, (self.note.slug,)),
            (self.detail_url, (self.note.slug,)),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse_lazy(name, args=args)
                response = self.client.get(url)
                self.assertRedirects(
                    response, f"{reverse_lazy(self.login_url)}?next={url}")

    def test_authenticated_user_access(self):
        """Аутентифицированному пользователю доступны
        страницы списка заметок и добавления заметок
        """
        self.client.force_login(self.author)
        urls = (
            self.list_url,
            self.add_url,
            self.success_url,
        )
        for name in urls:
            with self.subTest(name=name):
                response = self.client.get(reverse_lazy(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_access_to_note_pages(self):
        """Доступ к заметкам, страницам редактирования и
        удаления для авторов и неавторов
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.not_author, HTTPStatus.NOT_FOUND),
        )
        urls = (
            (self.edit_url, self.note.slug),
            (self.delete_url, self.note.slug),
            (self.detail_url, self.note.slug),
        )
        for user, expected_status in users_statuses:
            with self.subTest(user=user.username):
                self.client.force_login(user)
                for name, slug in urls:
                    with self.subTest(name=f"{name} проверка доступа"):
                        url = reverse_lazy(name, args=[slug])
                        response = self.client.get(url)
                        self.assertEqual(response.status_code, expected_status)