import datetime

import pytz
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import ModelForm
from .models import MyUser, Film, FilmSession, Purchase, Hall


class MyUserCreationForm(UserCreationForm):
    class Meta:
        model = MyUser
        fields = ('username',)


class AddFilmForm(ModelForm):
    class Meta:
        model = Film
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        start_premier = cleaned_data.get('start_premier')
        end_premier = cleaned_data.get('end_premier')
        name = cleaned_data.get('name')
        length = cleaned_data.get('length')
        genre = cleaned_data.get('genre')
        min_length = datetime.timedelta(minutes=30, hours=1)
        max_length = datetime.timedelta(hours=4)
        if start_premier is None:
            self.add_error('start_premier', 'Incorrect date')
        elif end_premier is None:
            self.add_error('end_premier', 'Incorrect date')
        else:
            if length < min_length:
                self.add_error('length', 'Film length must be greater than 01:30:00')
            if length > max_length:
                self.add_error('length', 'Film length must be lower than 04:00:00')
            if start_premier > end_premier:
                self.add_error('start_premier', 'Your premier date is wrong')
            if Film.objects.filter(name__iexact=name, start_premier=start_premier, end_premier=end_premier, length=length,
                                   genre=genre).exists():
                self.add_error('name', 'You already have added this film')


class HallForm(ModelForm):
    class Meta:
        model = Hall
        fields = '__all__'

    def clean_size(self):
        size = self.cleaned_data.get('size')
        if size <= 0:
            raise ValidationError('Size must be greater than zero')
        return size

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        if Purchase.objects.filter(film_session__hall__id=self.instance.pk).exists():
            self.add_error('name', 'You can not edit this hall because tickets with this one was sold')
        if Hall.objects.filter(~Q(id=self.instance.pk), name__iexact=name).exists():
            self.add_error('name', 'There already has been hall with this name')


class FilmSessionForm(ModelForm):
    class Meta:
        model = FilmSession
        fields = ['film', 'hall', 'start', 'end', 'price']

    def clean(self):
        cleaned_data = super().clean()
        hall = cleaned_data.get('hall')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        film = cleaned_data.get('film')
        price = cleaned_data.get('price')
        q3 = Q(start__gt=start)
        q4 = Q(start__gte=end)
        q5 = Q(end__lte=start)
        if Purchase.objects.filter(film_session__id=self.instance.pk).exists():
            self.add_error('film', 'You can not edit this session because tickets with this one was sold')
        else:
            if start is None:
                self.add_error('start', 'incorrect date')
            elif end is None:
                self.add_error('end', 'Incorrect date')
            else:
                delta = end - start
                if delta > (film.length + datetime.timedelta(minutes=20)) or delta < film.length:
                    self.add_error('film', 'Your session time is incorrect ')
                if price <= 0:
                    self.add_error('price', 'Enter a correct price!')
                if FilmSession.objects.filter(~((q3 & q4) | q5), ~Q(id=self.instance.pk), hall=hall).exists():
                    self.add_error('hall', 'This time in that hall is booked, please choose another hall or time')
                if start >= end:
                    self.add_error('start', 'Something is wrong with your session')
                if start.date() < film.start_premier:
                    self.add_error('start', 'The start of session does not consist with premier')
                if end.date() > film.end_premier:
                    self.add_error('end', 'The end of session does not consist with premier')


class AddPurchaseForm(ModelForm):
    class Meta:
        model = Purchase
        fields = ['count']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super(AddPurchaseForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        count = cleaned_data.get('count')
        session_id = self.request.POST.get('filmSession')
        film_session = FilmSession.objects.get(id=session_id)
        user_ = self.request.user
        sum_ = count * film_session.price
        now = datetime.datetime.now()
        now_loc = pytz.utc.localize(now)
        if film_session.start < now_loc:
            self.add_error('count', 'You can not buy ticket for this session because this one has already started')
        if count > film_session.hall_size:
            self.add_error('count', 'Sorry, not enough tickets')
        if sum_ > user_.wallet:
            self.add_error('count', 'money money fucking money')
        if count <= 0:
            self.add_error('count', 'Please select one or more tickets')


class FilterForm(forms.Form):
    DATE_CHOICES = (
        (1, 'all'),
        (2, 'today'),
        (3, 'tomorrow')
    )
    ORDER_CHOICES = (
        (1, 'by price'),
        (2, 'by start time')
    )
    period = forms.ChoiceField(label='period', choices=DATE_CHOICES)
    ordering = forms.ChoiceField(choices=ORDER_CHOICES, widget=forms.RadioSelect, required=False)
