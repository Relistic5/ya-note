from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse_lazy
from pytils.translit import slugify

from notes.forms import WARNING, NoteForm
from notes.models import Note

User = get_user_model()


class TestLogic(TestCase):

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
        cls.create_url = reverse_lazy(
            'notes:add')
        cls.edit_url = reverse_lazy(
            'notes:edit', kwargs={'slug': cls.note.slug})
        cls.delete_url = reverse_lazy(
            'notes:delete', kwargs={'slug': cls.note.slug})
        cls.success_url = reverse_lazy(
            'notes:success')
        cls.update_data = {
            'title': 'Измененное название',
            'text': 'Измененный текст'
        }
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
        }

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        response = self.client.post(self.create_url, data=self.update_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    # def SetUp(self):
    #     """Авторизуем обоих пользователей"""
    #     super().setUp()
    #     self.client.force_login(self.author)
    #     self.client.force_login(self.not_author)

    def test_logged_in_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        self.client.force_login(self.author)
        response = self.client.post(
            self.create_url, data=self.update_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(Note.objects.filter(
            title=self.update_data['title']).exists())

    def test_author_can_edit_own_note(self):
        """Автор может редактировать свою заметку"""
        self.client.force_login(self.author)
        response_edit = self.client.post(self.edit_url, data=self.update_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.update_data['title'])
        self.assertEqual(self.note.text, self.update_data['text'])

    def test_author_can_delete_own_note(self):
        """Автор может удалить свою заметку"""
        self.client.force_login(self.author)
        response_delete = self.client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.FOUND)
        with self.assertRaises(Note.DoesNotExist):
            Note.objects.get(slug=self.note.slug)

    def test_not_author_cannot_edit_note(self):
        """Неавтор не может редактировать заметку автора"""
        self.client.force_login(self.not_author)
        response_edit = self.client.post(self.edit_url, data=self.update_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertNotEqual(self.note.title, self.update_data['title'])
        self.assertNotEqual(self.note.text, self.update_data['text'])

    def test_not_author_cannot_delete_note(self):
        """Неавтор не может удалить заметку автора"""
        self.client.force_login(self.not_author)
        response_delete = self.client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.NOT_FOUND)
        self.assertTrue(Note.objects.filter(slug=self.note.slug).exists())

    def test_not_unique_slug(self):
        """Нельзя создать заметку со слагом, который уже существует"""
        self.form_data['slug'] = self.note.slug
        form = NoteForm(data=self.form_data)
        self.assertFalse(form.is_valid())
        error_message = form.errors['slug'][0]
        self.assertTrue(error_message.endswith(WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Проверка автоматической генерации слага"""
        self.client.force_login(self.author)
        expected_slug = slugify(self.form_data['title'])
        Note.objects.filter().delete()
        response = self.client.post(
            self.create_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.get(
            slug=expected_slug).slug, expected_slug)
