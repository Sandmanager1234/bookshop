import json

from django.urls import reverse
from django.db.models import Case, When, Count, Avg, F
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from store.models import Book, UserBookRelation
from store.serializers import BooksSerializer

class BooksApiTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username_2')
        self.user3 = User.objects.create(username='test_username_3', is_staff=True)
        self.book_1 = Book.objects.create(title='The book 1', price=100.00, author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(title='The book 2', price=200.00, author_name='Author 2')
        self.book_3 = Book.objects.create(title='The book 3 Author 1', price=50.00, author_name='Author 3')
        UserBookRelation.objects.create(user=self.user, book=self.book_3, like=True, rate=3)
        self.all_books = Book.objects.all()

    def test_get(self):
        url = reverse('book-list')
        response = self.client.get(url)
        serializer_data = BooksSerializer(self.all_books.annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
            ).order_by('id'), many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data, [serializer_data, response.data])


    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'price': 200})
        books = Book.objects.filter(id__in=[self.book_2.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
            )
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data)


    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
            ).order_by('id')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data, [serializer_data, response.data])


    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'price'})
        books = self.all_books.annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
            ).order_by('price')
        serializer_data = BooksSerializer(books, many=True).data
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(serializer_data, response.data, )
    

    def test_create(self):
        book_counter = self.all_books.count()
        url = reverse('book-list')
        data = {
            'title': 'Python 3',
            'price': 150,
            'author_name': 'Mark Summerland',
            # 'annotated_likes': 0,
        }
        self.client.force_login(self.user)
        json_data = json.dumps(data)
        response = self.client.post(url, data=json_data,
                                        content_type='application/json')
        
        self.assertEqual(status.HTTP_201_CREATED, response.status_code, response.data)
        self.assertEqual(book_counter + 1, Book.objects.all().count())
        self.assertEqual(self.user, Book.objects.last().owner)


    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id, ))
        data = {
            'title': self.book_1.title,
            'price': 150,
            'author_name': self.book_1.author_name
        }
        self.client.force_login(self.user)
        json_data = json.dumps(data)
        response = self.client.put(url, data=json_data,
                                        content_type='application/json')
        
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(150, self.book_1.price)


    def test_delete(self):
        book_counter = self.all_books.count()
        url = reverse('book-detail', args=(self.book_1.id, ))
        self.client.force_login(self.user)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(book_counter - 1, Book.objects.all().count())


    def test_update_not_owner(self):
        url = reverse('book-detail', args=(self.book_1.id, ))
        data = {
            'title': self.book_1.title,
            'price': 150,
            'author_name': self.book_1.author_name
        }
        self.client.force_login(self.user2)
        json_data = json.dumps(data)
        response = self.client.put(url, data=json_data,
                                        content_type='application/json')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.book_1.refresh_from_db()
        self.assertEqual(100, self.book_1.price)
    

    def test_delete_not_owner(self):
        book_counter = self.all_books.count()
        url = reverse('book-detail', args=(self.book_1.id, ))
        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code, response.data)
        self.assertEqual(book_counter, Book.objects.all().count())
    

    def test_update_not_owner_but_staff(self):
        url = reverse('book-detail', args=(self.book_1.id, ))
        data = {
            'title': self.book_1.title,
            'price': 150,
            'author_name': self.book_1.author_name
        }
        self.client.force_login(self.user3)
        json_data = json.dumps(data)
        response = self.client.put(url, data=json_data,
                                        content_type='application/json')
        self.assertEqual(status.HTTP_200_OK, response.status_code, response.data)
        self.book_1.refresh_from_db()
        self.assertEqual(150, self.book_1.price)

    
    def test_delete_not_owner_but_staff(self):
        book_counter = self.all_books.count()
        url = reverse('book-detail', args=(22, ))
        self.client.force_login(self.user3)
        response = self.client.delete(url)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEqual(book_counter - 1, Book.objects.all().count())


class BooksRelationApiTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username_2')
        self.user3 = User.objects.create(username='test_username_3', is_staff=True)
        self.book_1 = Book.objects.create(title='The book 1', price=100.00,
                                          author_name='Author 1', owner=self.user)
        self.book_2 = Book.objects.create(title='The book 2', price=200.00, 
                                          author_name='Author 2')


    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {
            'like': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                        content_type='application/json')
        realtion = UserBookRelation.objects.get(user=self.user,
                                                  book=self.book_1)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(realtion.like)
        data = {
            'in_bookmarks': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                    content_type='application/json')
        realtion = UserBookRelation.objects.get(user=self.user,
                                                  book=self.book_1)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(realtion.in_bookmarks)


    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {
            'rate': 3,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                        content_type='application/json')
        realtion = UserBookRelation.objects.get(user=self.user,
                                                  book=self.book_1)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(3, realtion.rate)

    
    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {
            'rate': 7,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                        content_type='application/json')
        realtion = UserBookRelation.objects.get(user=self.user,
                                                  book=self.book_1)
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code, response.data)
        self.assertEqual(None, realtion.rate)


    def test_read(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        self.client.force_login(self.user)
        data = {
            'read': True,
        }
        json_data = json.dumps(data)
        response = self.client.patch(url, data=json_data,
                                        content_type='application/json')
        realtion = UserBookRelation.objects.get(user=self.user,
                                                  book=self.book_1)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertTrue(realtion.read)
