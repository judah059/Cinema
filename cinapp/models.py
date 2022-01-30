import datetime
from rest_framework import serializers
from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.authtoken.models import Token


class MyUser(AbstractUser):
    wallet = models.DecimalField(max_digits=12, decimal_places=2, default=1000)


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
