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

        cls.urls = {
            'list': reverse_lazy('notes:list'),
            'add': reverse_lazy('notes:add'),
            'edit': reverse_lazy('notes:edit', kwargs={'slug': cls.note.slug}),
        }

    def test_note_visibility(self):
        """Доступность заметок для авторов и неавторов"""
        test_cases = (
            (self.author, True),
            (self.not_author, False),
        )
        for user, expected_result in test_cases:
            with self.subTest(user=user):
                self.client.force_login(user)
                response = self.client.get(self.urls['list'])
                object_list = response.context['object_list']
                note_visible = self.note in object_list
                self.assertIs(
                    note_visible, expected_result,
                    msg=f'Пользователь {user.username} должен \
                        {'видеть' if expected_result else 'не видеть'} заметку.'
                )

    def test_note_form_views(self):
        """Наличие формы на страницах создания и редактирования"""
        test_cases = (
            (self.author, self.urls['add']),
            (self.author, self.urls['edit']),
        )
        for user, url in test_cases:
            self.client.force_login(user)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            with self.subTest(user=user, url=url):
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
