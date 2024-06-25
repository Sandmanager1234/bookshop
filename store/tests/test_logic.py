from django.test import TestCase
from django.contrib.auth.models import User

from store.models import UserBookRelation, Book
from store.logic import set_rating


class SetRatingTestCase(TestCase):
    def setUp(self):
        user = User.objects.create(username='test_username', first_name='Ivan', last_name='Sidorov')
        user2 = User.objects.create(username='test_username_2', first_name='Egor', last_name='Petrov')
        user3 = User.objects.create(username='test_username_3', first_name='Asya', last_name='Zayceva')
        self.book_1 = Book.objects.create(title='The book 1', price=100.00, author_name='Author 1', owner=user)

        UserBookRelation.objects.create(user=user, book=self.book_1, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=self.book_1, like=True, rate=4)
        user_book_3 = UserBookRelation.objects.create(user=user3, book=self.book_1, like=False)
        user_book_3.rate = 4
        user_book_3.save()


    def test_ok_logic(self):
        set_rating(self.book_1)
        self.book_1.refresh_from_db()
        self.assertEqual('3.67', str(self.book_1.rating))