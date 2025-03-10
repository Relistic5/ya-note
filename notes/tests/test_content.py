from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse_lazy

from notes.forms import NoteForm
from notes.models import Note


class NotesTestCase(TestCase):

    def setUp(self):
        self.author = User.objects.create_user(
            username='author', password='password')
        self.not_author = User.objects.create_user(
            username='not_author', password='password')
        self.note = Note.objects.create(
            title='Заголовок', text='Текст заметки',
            slug='author-note', author=self.author)

        self.client.login(username='author', password='password')

    def test_note_detail_in_context(self):
        """Заметка передается в контексте страницы"""
        response = self.client.get(reverse_lazy('notes:list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('object_list', response.context)
        self.assertIn(self.note, response.context['object_list'])

    def test_other_user_notes_not_in_list(self):
        """Заметка другого пользователя"""
        Note.objects.create(
            title='Другой пользователь', text='Текст заметки другого юзера',
            slug='not-author-note', author=self.not_author)
        response = self.client.get(reverse_lazy('notes:list'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(Note.objects.get(
            title='Другой пользователь'), response.context['object_list'])
        self.assertIn(self.note, response.context['object_list'])

    def test_create_note_form_is_passed(self):
        """Форма создания заметки передается на страницу"""
        response = self.client.get(reverse_lazy('notes:add'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_note_form_is_passed(self):
        """Форма редактирования заметки передается на страницу"""
        response = self.client.get(reverse_lazy(
            'notes:edit', args=[self.note.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], NoteForm)
