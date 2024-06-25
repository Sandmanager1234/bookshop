from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg, F, Prefetch
from rest_framework.viewsets import ModelViewSet, mixins, GenericViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend


from .models import Book, UserBookRelation
from .permissions import IsOwnerOrStaffOrReadOnly
from .serializers import BooksSerializer, UserBookRelationSerializer


class BookViewSet(ModelViewSet):
    queryset = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1))),
            owner_name=F('owner__username')
        ).prefetch_related(Prefetch('readers', queryset=User.objects.all().only('first_name', 'last_name'))).order_by('id')
    serializer_class = BooksSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter, )
    filterset_fields = ['price']
    search_fields = ['title', 'author_name']
    ordering_fields = ['price', 'author_name']
    permission_classes = [IsOwnerOrStaffOrReadOnly]

    def perform_create(self, serializer):
        serializer.validated_data['owner'] = self.request.user
        serializer.save()


class UserBooksRelationView(mixins.UpdateModelMixin,
                            GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = UserBookRelation.objects.all()
    serializer_class = UserBookRelationSerializer
    lookup_field = 'book'

    def get_object(self):
        obj, _ = UserBookRelation.objects.get_or_create(user=self.request.user,
                                                        book_id=self.kwargs['book'])
        return obj


def auth(request):
    return render(request, 'oauth.html')


