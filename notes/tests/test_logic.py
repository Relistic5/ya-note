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

        cls.form_data = {
            'title': 'Другая заметка',
            'text': 'Другой текст',
            'slug': 'note',
        }

        cls.create_url = reverse_lazy('notes:add')
        cls.edit_url = reverse_lazy('notes:edit', kwargs={'slug': 'note'})
        cls.delete_url = reverse_lazy('notes:delete', kwargs={'slug': 'note'})
        cls.success_url = reverse_lazy('notes:success')

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)

    def test_anonymous_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        response = self.client.post(self.create_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), 0, 'Заметка создана анонимом')

    def test_login_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        response = self.author_client.post(
            self.create_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Note.objects.count(), 1, 'Не удалось создать заметку')

        note = Note.objects.get()
        self.assertEqual(
            note.title, self.form_data['title'], 'Неверный Заголовок')
        self.assertEqual(
            note.text, self.form_data['text'], 'Неверный Текст')
        self.assertEqual(
            note.slug, self.form_data['slug'], 'Неверный Слаг')
        self.assertEqual(
            note.author, self.author, 'Неверный Автор')

    def test_empty_slug(self):
        """Проверка автоматической генерации слага"""
        expected_slug = slugify(self.form_data['title'])
        self.form_data.pop('slug')
        response = self.author_client.post(
            self.create_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(Note.objects.count(), 1)

        created_note = Note.objects.last()
        self.assertEqual(
            created_note.slug, expected_slug,
            'Слаг не соответствует ожидаемому')


class TestLogicWithNote(TestLogic):

    def setUp(self):
        """Заранее создаем note, кроме тестов, где она не нужна"""
        super().setUp()
        if self._testMethodName not in ['test_login_user_can_create_note',
                                        'test_anonymous_cannot_create_note',
                                        'test_empty_slug']:
            self.note = Note.objects.create(
                title='Название заметки',
                text='Текст заметки',
                slug='note',
                author=self.author
            )

    def test_author_can_edit_own_note(self):
        """Автор может редактировать свою заметку"""
        response_edit = self.author_client.post(
            self.edit_url, data=self.form_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.FOUND)

        self.note.refresh_from_db()
        self.assertEqual(
            self.note.title, self.form_data['title'], 'Заголовок не обновили')
        self.assertEqual(
            self.note.text, self.form_data['text'], 'Текст не обновили')
        self.assertEqual(
            self.note.slug, self.form_data['slug'], 'Слаг не обновили')

    def test_author_can_delete_own_note(self):
        """Автор может удалить свою заметку"""
        response_delete = self.author_client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.FOUND)
        self.assertEqual(
            Note.objects.count(), 0, 'Не удалось удалить заметку')

    def test_not_author_cannot_edit_note(self):
        """Неавтор не может редактировать заметку автора"""
        original_note = self.note
        response_edit = self.not_author_client.post(
            self.edit_url, data=self.form_data)
        self.assertEqual(response_edit.status_code, HTTPStatus.NOT_FOUND)
        updated_note = Note.objects.get(id=original_note.id)

        self.assertEqual(
            original_note.title, updated_note.title, 'Изменился Заголовок')
        self.assertEqual(
            original_note.text, updated_note.text, 'Изменился Текст')
        self.assertEqual(
            original_note.slug, updated_note.slug, 'Изменился Слаг')

    def test_not_author_cannot_delete_note(self):
        """Неавтор не может удалить заметку автора"""
        response_delete = self.not_author_client.post(self.delete_url)
        self.assertEqual(response_delete.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1, 'Удалена чужая заметка')

    def test_not_unique_slug(self):
        """Нельзя создать заметку со слагом, который уже существует"""
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(
            self.create_url, data=self.form_data)
        error_message = self.note.slug + WARNING
        self.assertContains(response, error_message)
        self.assertEqual(Note.objects.count(), 1)
