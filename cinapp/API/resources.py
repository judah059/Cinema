import datetime
from cinapp.API.permissions import IsAdminOrReadOnly
from django.db import transaction
from rest_framework.authtoken.views import ObtainAuthToken
from cinapp.API.serializers import FilmSerializer, HallSerializer, FilmSessionGetSerializer, \
    FilmSessionPostPutPatchSerializer, PurchaseGetSerializer, PurchasePostSerializer, MyUserPostSerializer
from cinapp.models import CustomToken, Film, Hall, FilmSession, Purchase
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import permissions
from rest_framework.generics import CreateAPIView
from django.contrib.auth import get_user_model

UserModel = get_user_model()


class ApiRegistration(CreateAPIView):
    model = UserModel
    permission_classes = [permissions.AllowAny]
    serializer_class = MyUserPostSerializer


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = CustomToken.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'wallet': user.wallet,
            'token_last_action': token.last_action
        })


class FilmModelViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.ListModelMixin,
                       mixins.DestroyModelMixin,
                       GenericViewSet):
    queryset = Film.objects.all()
    serializer_class = FilmSerializer
    permission_classes = [IsAdminOrReadOnly]


class HallModelViewSet(ModelViewSet):
    queryset = Hall.objects.all()
    serializer_class = HallSerializer
    permission_classes = [IsAdminOrReadOnly]

    def perform_update(self, serializer):
        name = serializer.validated_data['name']
        size = serializer.validated_data['size']
        if FilmSession.objects.filter(hall__name=name).exists():
            FilmSession.objects.filter(hall__name=name).update(hall_size=size)
            serializer.save()
        serializer.save()


class FilmSessionModelViewSet(ModelViewSet):
    queryset = FilmSession.objects.all()
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return FilmSessionPostPutPatchSerializer
        else:
            return FilmSessionGetSerializer

    def perform_create(self, serializer):
        hall = serializer.validated_data['hall']
        hall_size = hall.size
        serializer.save(hall_size=hall_size)

    def perform_update(self, serializer):
        hall = serializer.validated_data['hall']
        hall_size = hall.size
        serializer.save(hall_size=hall_size)

    def get_queryset(self):
        qs = super().get_queryset()
        start = self.request.GET.get('start')
        end = self.request.GET.get('end')
        hall = self.request.GET.get('hall')
        today = datetime.date.today()
        try:
            start_in_datetime = datetime.datetime.strptime(start, "%H:%M:%S")
            start_in_time = start_in_datetime.time()
            end_in_datetime = datetime.datetime.strptime(end, "%H:%M:%S")
            end_in_time = end_in_datetime.time()
            today_start = datetime.datetime.combine(today, start_in_time)
            today_end = datetime.datetime.combine(today, end_in_time)
            if start and end and hall:
                return qs.filter(start__range=[today_start, today_end], hall__name__iexact=hall)
            if start and end:
                return qs.filter(start__range=[today_start, today_end])
        except ValueError:
            return None
        except TypeError:
            if hall:
                return qs.filter(start__contains=today, hall__name__iexact=hall)
        return qs.all()


class PurchaseModelViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.ListModelMixin,
                           GenericViewSet):
    queryset = Purchase.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method != 'GET':
            return PurchasePostSerializer
        else:
            return PurchaseGetSerializer

    def perform_create(self, serializer):
        my_user = self.request.user
        film_session = serializer.validated_data['film_session']
        count_ = serializer.validated_data['count']
        sum_ = count_ * film_session.price
        film_session.hall_size = film_session.hall_size - count_
        my_user.wallet = my_user.wallet - sum_
        with transaction.atomic():
            film_session.save()
            my_user.save()
            serializer.save(user=my_user)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs.all()
        else:
            return qs.filter(user=self.request.user)
