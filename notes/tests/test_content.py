from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.not_author = User.objects.create(username='Неавтор')
        cls.note = Note.objects.create(
            title='Название заметки',
            text='Текст заметки',
            slug='note',
            author=cls.author)

    def test_note_visibility(self):
        """Доступность заметок для авторов и неавторов"""
        test_cases = (
            (self.author, True),
            (self.not_author, False),
        )
        for client, expected_result in test_cases:
            with self.subTest(client=client):
                self.client.force_login(client)
                response = self.client.get(reverse_lazy('notes:list'))
                object_list = response.context['object_list']

                # Проверяем, присутствует ли заметка в object_list
                note_exists = any(
                    note.slug == self.note.slug for note in object_list)

                self.assertIs(
                    note_exists,
                    expected_result,
                    msg=f'Пользователь'
                        f' {client.username} должен'
                        f' {'видеть' if expected_result else 'не видеть'}'
                        f' заметку.'
                )

    def check_form_view(self, url):
        """Для проверки наличия формы на странице"""
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_note_form_views(self):
        """Наличие формы на страницах создания и редактирования"""
        test_cases = (
            (self.author, reverse_lazy(
                'notes:add')),
            (self.author, reverse_lazy(
                'notes:edit', kwargs={'slug': self.note.slug})),
        )
        for user, url in test_cases:
            self.client.force_login(user)
            self.check_form_view(url)
