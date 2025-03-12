from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
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

        cls.urls = {
            'list': reverse_lazy('notes:list'),
            'add': reverse_lazy('notes:add'),
            'edit': reverse_lazy('notes:edit', kwargs={'slug': cls.note.slug}),
        }

        cls.client_author = Client()
        cls.client_author.force_login(cls.author)

        cls.client_not_author = Client()
        cls.client_not_author.force_login(cls.not_author)

    def test_note_visibility(self):
        """Доступность заметок для авторов и неавторов"""
        test_cases = [
            (self.client_author, True),
            (self.client_not_author, False)
        ]
        for client, expected_result in test_cases:
            with self.subTest(client=client):
                response = client.get(self.urls['list'])
                object_list = response.context['object_list']
                note_visible = self.note in object_list
                self.assertIs(
                    note_visible, expected_result,
                    msg=f'Пользователь {client} должен \
                        {"видеть" if expected_result else "не видеть"} \
                        заметку.'
                )

    def test_note_form_views(self):
        """Наличие формы на страницах создания и редактирования"""
        test_cases = [
            (self.client_author, self.urls['add']),
            (self.client_author, self.urls['edit']),
        ]
        for client, url in test_cases:
            with self.subTest(client=client, url=url):
                response = client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
