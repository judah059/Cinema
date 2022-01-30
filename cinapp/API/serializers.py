import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.serializers import ModelSerializer
from cinapp.models import Film, Hall, MyUser, FilmSession, Purchase
from rest_framework import serializers

UserModel = get_user_model()


class MyUserGetSerializer(ModelSerializer):
    class Meta:
        model = MyUser
        fields = ('username', 'wallet')


class MyUserPostSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = UserModel.objects.create_user(username=validated_data['username'], password=validated_data['password'])
        return user

    class Meta:
        model = UserModel
        fields = ('username', 'password')


class FilmSerializer(ModelSerializer):
    class Meta:
        model = Film
        fields = '__all__'

    def validate(self, attrs):
        min_length = datetime.timedelta(minutes=30, hours=1)
        max_length = datetime.timedelta(hours=4)
        if attrs['length'] < min_length:
            raise serializers.ValidationError('Film length must be greater than 01:30:00')
        if attrs['length'] > max_length:
            raise serializers.ValidationError('Film length must be lower than 04:00:00')
        if attrs['start_premier'] > attrs['end_premier']:
            raise serializers.ValidationError('Your premier date is wrong')
        if Film.objects.filter(name__iexact=attrs['name'], start_premier=attrs['start_premier'],
                               end_premier=attrs['end_premier'], length=attrs['length'],
                               genre=attrs['genre']).exists():
            raise serializers.ValidationError('You already have added this film')
        return attrs


class HallSerializer(ModelSerializer):
    class Meta:
        model = Hall
        fields = '__all__'

    def validate(self, attrs):
        if attrs['size'] <= 0:
            raise serializers.ValidationError('Size of the hall must be greater than zero')
        try:
            if Hall.objects.filter(~Q(id=self.instance.pk), name__iexact=attrs['name']).exists():
                raise serializers.ValidationError('There already has been hall with this name')
        except AttributeError:
            if Hall.objects.filter(name__iexact=attrs['name']).exists():
                raise serializers.ValidationError('There already has been hall with this name')
        if Purchase.objects.filter(film_session__hall__name__iexact=attrs['name']).exists():
            raise serializers.ValidationError('You can not edit this hall because tickets with this one was sold')
        return attrs


class FilmSessionGetSerializer(ModelSerializer):
    film = FilmSerializer()
    hall = HallSerializer()

    class Meta:
        model = FilmSession
        fields = '__all__'


class FilmSessionPostPutPatchSerializer(ModelSerializer):
    class Meta:
        model = FilmSession
        fields = ('film', 'hall', 'start', 'end', 'price')

    def validate(self, attrs):
        q1 = Q(start__gt=attrs['start'])
        q2 = Q(start__gte=attrs['end'])
        q3 = Q(end__lte=attrs['start'])
        film = attrs['film']
        delta = attrs['end'] - attrs['start']
        if delta > (film.length + datetime.timedelta(minutes=20)) or delta < film.length:
            raise serializers.ValidationError('Your session time is incorrect ')
        if attrs['start'] >= attrs['end']:
            raise serializers.ValidationError('Something is wrong with your session')
        if attrs['start'].date() < film.start_premier:
            raise serializers.ValidationError('The start of session does not consist with premier')
        if attrs['end'].date() > film.end_premier:
            raise serializers.ValidationError('The end of session does not consist with premier')
        if attrs['price'] <= 0:
            raise serializers.ValidationError('Enter a correct price!')
        try:
            if Purchase.objects.filter(film_session__id=self.instance.pk).exists():
                raise serializers.ValidationError(
                    'You can not edit this session because tickets with this one was sold')
            else:
                if FilmSession.objects.filter(~((q1 & q2) | q3), ~Q(id=self.instance.pk), hall=attrs['hall']).exists():
                    raise serializers.ValidationError('This time in that hall is booked, please choose another '
                                                      'hall or time')
        except AttributeError:
            if FilmSession.objects.filter(~((q1 & q2) | q3), hall=attrs['hall']).exists():
                raise serializers.ValidationError(
                    'This time in that hall is booked, please choose another hall or time')
        return attrs


class PurchaseGetSerializer(ModelSerializer):
    film_session = FilmSessionGetSerializer()
    user = MyUserGetSerializer()

    class Meta:
        model = Purchase
        fields = '__all__'


class PurchasePostSerializer(ModelSerializer):
    class Meta:
        model = Purchase
        fields = ('film_session', 'count')

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        film_session = attrs['film_session']
        sum_ = film_session.price * attrs['count']
        if FilmSession.objects.filter(start__lt=datetime.datetime.now(), id=film_session.id):
            raise serializers.ValidationError('You can not buy ticket for this session because this one has already started')
        if attrs['count'] <= 0:
            raise serializers.ValidationError('You should select one more tickets')
        if attrs['count'] > film_session.hall_size:
            raise serializers.ValidationError('Sorry, not enough tickets')
        if sum_ > self.context['request'].user.wallet:
            raise serializers.ValidationError('Not enough money')
        return attrs
