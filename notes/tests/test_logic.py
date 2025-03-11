from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse_lazy
from pytils.translit import slugify

from notes.forms import WARNING
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
        cls.update_data = {
            'title': 'Измененное название',
            'text': 'Измененный текст',
        }
        cls.form_data = {
            'title': 'Новая заметка',
            'text': 'Текст новой заметки',
        }

        cls.create_url = reverse_lazy('notes:add')
        cls.edit_url = reverse_lazy(
            'notes:edit', kwargs={'slug': cls.note.slug})
        cls.delete_url = reverse_lazy(
            'notes:delete', kwargs={'slug': cls.note.slug})
        cls.success_url = reverse_lazy(
            'notes:success')

        cls.anonymous_client = Client()

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        initial_count = Note.objects.count()
        response = self.anonymous_client.post(
            self.create_url, data=self.update_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            Note.objects.count(), initial_count, 'Что-то пошло не так')

    def test_logged_in_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        initial_count = Note.objects.count()
        response = self.author_client.post(
            self.create_url, data=self.update_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            Note.objects.count(), initial_count + 1, 'Что-то пошло не так')

        note = Note.objects.get(title=self.update_data['title'])
        self.assertEqual(
            note.title, self.update_data['title'], 'Что-то с заголовком')
        self.assertEqual(
            note.text, self.update_data['text'], 'Что-то с текстом')
        if 'slug' in self.update_data:
            self.assertEqual(
                note.slug, self.update_data['slug'], 'Что-то со слагом')

    def test_author_can_edit_own_note(self):
        """Автор может редактировать свою заметку"""
        response_edit = self.author_client.post(
            self.edit_url, data=self.update_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.FOUND)

        self.note.refresh_from_db()
        self.assertEqual(
            self.note.title, self.update_data['title'], 'Загоовок не обновили')
        self.assertEqual(
            self.note.text, self.update_data['text'], 'Текст не обновили')
        if 'slug' in self.update_data:
            self.assertEqual(
                self.note.slug, self.update_data['slug'], 'Слаг не обновили')

    def test_author_can_delete_own_note(self):
        """Автор может удалить свою заметку"""
        initial_count = Note.objects.count()
        response_delete = self.author_client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.FOUND)

        current_count = Note.objects.count()
        self.assertEqual(
            current_count, initial_count - 1, 'Что-то пошло не так')

    def test_not_author_cannot_edit_note(self):
        """Неавтор не может редактировать заметку автора"""
        original_note = Note.objects.get(id=self.note.id)
        response_edit = self.not_author_client.post(
            self.edit_url, data=self.update_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.NOT_FOUND)

        updated_note = Note.objects.get(id=self.note.id)
        self.assertEqual(
            original_note.title, updated_note.title, 'Изменился Заголовок')
        self.assertEqual(
            original_note.text, updated_note.text, 'Изменился Текст')
        self.assertEqual(
            original_note.slug, updated_note.slug, 'Изменился Слаг')

    def test_not_author_cannot_delete_note(self):
        """Неавтор не может удалить заметку автора"""
        initial_count = Note.objects.count()
        response_delete = self.not_author_client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), initial_count)

    def test_not_unique_slug(self):
        """Нельзя создать заметку со слагом, который уже существует"""
        self.author_client.force_login(self.author)

        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(
            self.create_url, data=self.form_data)

        form = response.context.get('form')
        error_message = self.note.slug + WARNING
        self.assertFormError(form, 'slug', error_message)

        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Проверка автоматической генерации слага"""
        self.author_client.force_login(self.author)
        Note.objects.filter().delete()

        expected_slug = slugify(self.form_data['title'])
        response = self.author_client.post(
            self.create_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)

        created_note = Note.objects.first()
        self.assertIsNotNone(created_note, 'Заметка не найдена')
        self.assertEqual(created_note.slug, expected_slug)
