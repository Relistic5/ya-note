from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


class NoteTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', password='testpassword')
        self.anonymous_user = User.objects.create_user(
            username='anon', password='anonpassword')

    def test_authenticated_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('notes:add'), {
            'title': 'Заголовок',
            'text': 'Текст заметки',
            'slug': 'test-note'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.first().title, 'Заголовок')

    def test_anonymous_user_cannot_create_note(self):
        """Анонимный пользователь не может создать заметку"""
        response = self.client.post(reverse('notes:add'), {
            'title': 'Заголовок',
            'text': 'Текст заметки',
            'slug': 'test-note'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Note.objects.count(), 0)

    def test_slug_uniqueness(self):
        """Невозможно создать две заметки с одинаковым slug"""
        self.client.login(username='testuser', password='testpassword')
        Note.objects.create(
            title='Первая заметка',
            text='Текст первой заметки',
            slug='unique-slug',
            author=self.user
        )
        response = self.client.post(reverse('notes:add'), {
            'title': 'Вторая заметка',
            'text': 'Текст второй заметки',
            'slug': 'unique-slug'
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        self.assertFalse(response.context['form'].is_valid())
        self.assertIn('slug', response.context['form'].errors)
        self.assertEqual(Note.objects.count(), 1)

    def test_slug_auto_generation_if_empty(self):
        """Автоматическое формирование slug"""
        self.client.login(username='testuser', password='testpassword')
        response = self.client.post(reverse('notes:add'), {
            'title': 'Заголовок без slug',
            'text': 'Текст заметки',
            'slug': ''
        })
        self.assertEqual(response.status_code, 302)
        note = Note.objects.first()
        self.assertIsNotNone(note.slug)
        self.assertEqual(note.slug, 'zagolovok-bez-slug')

    def test_user_can_edit_own_note(self):
        """Пользователь может редактировать свою заметку."""
        self.client.login(username='testuser', password='testpassword')
        note = Note.objects.create(
            title='Заголовок', text='Текст заметки',
            slug='edit-slug', author=self.user)
        response = self.client.post(reverse(
            'notes:edit', args=[note.slug]), {
            'title': 'Обновлённый заголовок',
            'text': 'Обновлённый текст заметки',
            'slug': 'edit-slug'
        })
        self.assertEqual(response.status_code, 302)
        note.refresh_from_db()
        self.assertEqual(note.title, 'Обновлённый заголовок')

    def test_user_cannot_edit_another_users_note(self):
        """Пользователь не может редактировать заметку другого пользователя."""
        self.client.login(
            username='testuser', password='testpassword')
        other_user = User.objects.create_user(
            username='otheruser', password='otherpassword')
        note = Note.objects.create(
            title='Чужая заметка', text='Текст чужой заметки',
            slug='other-slug', author=other_user)

        response = self.client.post(reverse(
            'notes:edit', args=[note.slug]), {
            'title': 'Не твое - не трогай',
            'text': 'Текст заметки',
            'slug': 'other-slug'
        })
        self.assertEqual(response.status_code, 404)

    def test_user_can_delete_own_note(self):
        """Пользователь может удалить свою заметку."""
        self.client.login(username='testuser', password='testpassword')
        note = Note.objects.create(
            title='Заголовок', text='Текст заметки',
            slug='delete-slug', author=self.user)
        response = self.client.post(reverse(
            'notes:delete', args=[note.slug]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cannot_delete_another_users_note(self):
        """Пользователь не может удалить заметку другого пользователя."""
        self.client.login(username='testuser', password='testpassword')
        other_user = User.objects.create_user(
            username='otheruser', password='otherpassword')
        note = Note.objects.create(
            title='Чужая заметка', text='Текст чужой заметки',
            slug='other-delete-slug', author=other_user)

        response = self.client.post(reverse(
            'notes:delete', args=[note.slug]))
        self.assertEqual(response.status_code, 404)