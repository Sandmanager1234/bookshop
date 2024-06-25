from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models import Case, When, Count, Avg, F

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer

class BookSerializerTestCase(TestCase):
    def test_ok(self):
        user = User.objects.create(username='test_username', first_name='Ivan', last_name='Sidorov')
        user2 = User.objects.create(username='test_username_2', first_name='Egor', last_name='Petrov')
        user3 = User.objects.create(username='test_username_3', first_name='Asya', last_name='Zayceva')
        book_1 = Book.objects.create(title='The book 1', price=100.00, author_name='Author 1', owner=user)
        book_2 = Book.objects.create(title='The book 2', price=200.00, author_name='Author 2')
        UserBookRelation.objects.create(user=user, book=book_2, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True, rate=4)
        UserBookRelation.objects.create(user=user3, book=book_2, like=True, rate=5)

        UserBookRelation.objects.create(user=user, book=book_1, like=True, rate=3)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True, rate=4)
        UserBookRelation.objects.create(user=user3, book=book_1, like=False)

        books = Book.objects.filter(id__in=[book_1.id, book_2.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username'),
            ).order_by('id')
        data = BooksSerializer(books, many=True).data
        expected_data = [
            {
                'id': book_1.id,
                'title': 'The book 1',
                'price': '100.00',
                'author_name': 'Author 1',
                # 'likes_count': 2,
                'annotated_likes': 2,
                'rating': '3.50',
                'owner_name': 'test_username',
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': 'Egor',
                        'last_name': 'Petrov'
                    },
                    {
                        'first_name': 'Asya',
                        'last_name': 'Zayceva'
                    }
                ],
            },
            {
                'id': book_2.id,
                'title': 'The book 2',
                'price': '200.00',
                'author_name': 'Author 2',
                # 'likes_count': 3,
                'annotated_likes': 3,
                'rating': '4.00',
                'owner_name': None,
                'readers': [
                    {
                        'first_name': 'Ivan',
                        'last_name': 'Sidorov'
                    },
                    {
                        'first_name': 'Egor',
                        'last_name': 'Petrov'
                    },
                    {
                        'first_name': 'Asya',
                        'last_name': 'Zayceva'
                    }
                ],
            }
        ]
        self.assertEqual(expected_data, data, [expected_data, data])