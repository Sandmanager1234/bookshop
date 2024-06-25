from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Book, UserBookRelation


class BookReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')


class BooksSerializer(serializers.ModelSerializer):
    # likes_count = serializers.SerializerMethodField()
    annotated_likes = serializers.IntegerField(read_only=True)
    rating = serializers.DecimalField(read_only=True, max_digits=3, decimal_places=2)
    # owner_name = serializers.CharField(source='owner.username', default='', read_only=True)
    owner_name = serializers.CharField(read_only=True)
    readers = BookReaderSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'price', 'author_name', 'annotated_likes', 'rating', 'owner_name', 'readers']

    # def get_likes_count(self, instance):
        # return UserBookRelation.objects.filter(book=instance, like=True).count()


class UserBookRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBookRelation
        fields = ['book', 'like', 'in_bookmarks', 'rate', 'read']
