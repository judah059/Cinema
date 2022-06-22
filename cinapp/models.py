import datetime
from rest_framework import serializers
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token


CITY_CHOICES = (
    ('KV', 'Киев'),
    ('DN', 'Днепр'),
    ('ZP', 'Запорожье'),
    ('NI', 'Николаев'),
    ('CH', 'Херсон'),
    ('CHA', 'Харьков'),
    ('CHE', 'Хмельницкий'),
    ('JI', 'Житомир'),
    ('KR', 'Кривой Рог'),
    ('MP', 'Мариуполь'),
    ('RO', 'Ровное'),
    ('CHER', 'Чернигов'),
    ('LV', 'Львов'),
    ('PL', 'Полтава'),
    ('OD', 'Одесса'),
    ('LC', 'Луцк'),
    ('CHRS', 'Черкасы'),
    ('SM', 'Сумы'),
    ('VI', 'Вишневое'),
    ('IF', 'Ивано-Франковск'),
    ('BR', 'Бердянск'),
    ('VN', 'Виница'),
    ('SD', 'Северодонецк'),
    ('NK', 'Новая Каховка'),
    ('PG', 'Павлоград'),
    ('KR', 'Краматорск'),
    ('KRE', 'Кременчуг'),
    ('PK', 'Покровск'),
    ('BCH', 'Буча'),
)


class MyUser(AbstractUser):
    is_reviewer = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    city = models.CharField(max_length=300, choices=CITY_CHOICES)
    # stripe_id = null // Не понимаю зач, но сказали сделать


class Hall(models.Model):
    name = models.CharField(max_length=60)
    size = models.IntegerField()

    def delete(self, using=None, keep_parents=False):
        if Purchase.objects.filter(film_session__hall__name=self.name,
                                   film_session__end__gt=datetime.datetime.now()).exists():
            raise serializers.ValidationError('You can not delete this hall because session with this one was sold')
        return super().delete()


class Film(models.Model):
    CHOICE_GENRE = (
        ('1', 'horror'),
        ('2', 'comedy'),
        ('3', 'action'),
        ('4', 'thriller'),
        ('5', 'detective'),
        ('6', 'drama')
    )
    name = models.CharField(max_length=60)
    start_premier = models.DateField()
    end_premier = models.DateField()
    length = models.DurationField()
    genre = models.CharField(choices=CHOICE_GENRE, default='1', max_length=2)
    description = models.TextField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        if Purchase.objects.filter(film_session__film__id=self.id,
                                   film_session__film__end_premier__gt=datetime.datetime.now().date()).exists():
            raise serializers.ValidationError('You can not delete this film because session with this one was sold')
        return super().delete()


class FilmSession(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='sessions')
    hall = models.ForeignKey(Hall, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    hall_size = models.IntegerField(default=10)

    def delete(self, using=None, keep_parents=False):
        if Purchase.objects.filter(film_session=self.id,
                                   film_session__end__gt=datetime.datetime.now()).exists():
            raise serializers.ValidationError('You can not delete this session because session with this one was sold')
        return super().delete()


class Purchase(models.Model):
    film_session = models.ForeignKey(FilmSession, on_delete=models.CASCADE)
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)


class CustomToken(Token):
    last_action = models.DateTimeField(auto_now_add=True)
