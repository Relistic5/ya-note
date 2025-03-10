from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse_lazy

from notes.models import Note


class TestRoutes(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author', password='password')
        self.not_author = User.objects.create_user(
            username='not_author', password='password')
        self.client.login(
            username='author', password='password')

        self.note = Note.objects.create(
            title='Заголовок', text='Текст заметки',
            slug='test-note', author=self.author)

    def test_pages_availability_for_anonymous_user(self):
        """Доступность страниц анонимным пользователям"""
        urls = ['notes:home', 'users:login', 'users:signup']
        for name in urls:
            url = reverse_lazy(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """Доступность страниц авторизованным пользователям"""
        auth_urls = ['notes:list', 'notes:add', 'notes:success']
        for name in auth_urls:
            url = reverse_lazy(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """Доступ к страницам не-авторов заметок"""
        self.client.logout()
        self.client.login(username='not_author', password='password')

        urls = ['notes:list', 'notes:add', 'notes:success']
        for name in urls:
            url = reverse_lazy(name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_detail_redirect(self):
        """Редирект"""
        url = reverse_lazy('notes:detail', args=[self.note.slug])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
