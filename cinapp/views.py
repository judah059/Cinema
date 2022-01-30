import datetime

from django.db import transaction
from django.db.models import Sum
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, TemplateView
from django.views.generic.edit import FormMixin
from cinapp.forms import MyUserCreationForm, AddFilmForm, FilterForm, AddPurchaseForm, \
    FilmSessionForm, HallForm
from .models import Hall, Purchase, Film, FilmSession


class Login(LoginView):
    template_name = 'login.html'


class Registration(CreateView):
    form_class = MyUserCreationForm
    template_name = 'registration.html'
    success_url = '/login/'


class Logout(LogoutView):
    next_page = '/'
    login_url = '/login/'


class FilmCreateView(UserPassesTestMixin, CreateView):
    form_class = AddFilmForm
    http_method_names = ['post']
    template_name = 'film.html'
    success_url = '/'

    def test_func(self):
        return self.request.user.is_superuser


class HallCreateView(UserPassesTestMixin, CreateView):
    form_class = HallForm
    http_method_names = ['post']
    template_name = 'hall.html'
    success_url = '/'

    def test_func(self):
        return self.request.user.is_superuser


class FilmListView(ListView):
    model = Film
    template_name = 'film.html'
    paginate_by = 20
    extra_context = {'form': AddFilmForm()}


class HallListView(ListView):
    model = Hall
    template_name = 'hall.html'
    extra_context = {'form': HallForm()}


class FilmSessionCreateView(UserPassesTestMixin, CreateView):
    form_class = FilmSessionForm
    http_method_names = ['post']
    template_name = 'sessions.html'
    success_url = '/'

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        obj = form.save(commit=False)
        hall = form.cleaned_data['hall']
        obj.hall_size = hall.size
        obj.save()
        return super().form_valid(form=form)


class FilmSessionListView(ListView):
    model = FilmSession
    template_name = 'sessions.html'
    paginate_by = 10
    extra_context = {'form': FilmSessionForm, 'period_form': FilterForm}

    def get_queryset(self):
        qs = super().get_queryset()
        period = self.request.GET.get('period')
        ordering = self.request.GET.get('ordering')
        today = datetime.date.today()
        tomorrow = datetime.timedelta(days=1) + today
        if period == '1' and ordering == '1':
            return qs.order_by('price')
        elif period == '1' and ordering == '2':
            return qs.order_by('start')
        elif period == '1' and ordering is None:
            return qs.all()
        if period == '2' and ordering == '1':
            return qs.filter(start__contains=today).order_by('price')
        elif period == '2' and ordering == '2':
            return qs.filter(start__contains=today).order_by('start')
        elif period == '2' and ordering is None:
            return qs.filter(start__contains=today)
        if period == '3' and ordering == '1':
            return qs.filter(start__contains=tomorrow).order_by('price')
        elif period == '3' and ordering == '2':
            return qs.filter(start__contains=tomorrow).order_by('start')
        elif period == '3' and ordering is None:
            return qs.filter(start__contains=tomorrow)
        return qs.all()


class FilmSessionDetailView(FormMixin, DetailView):
    model = FilmSession
    template_name = 'detailSession.html'
    pk_url_kwarg = 'pk'
    form_class = AddPurchaseForm

    def get_success_url(self):
        return reverse('sessions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kw = super(FilmSessionDetailView, self).get_form_kwargs()
        kw['request'] = self.request
        return kw

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        session_id = self.request.POST.get('filmSession')
        obj.film_session = FilmSession.objects.get(id=int(session_id))
        obj.film_session.hall_size = obj.film_session.hall_size - obj.count
        sum_ = obj.count * obj.film_session.price
        obj.user.wallet = obj.user.wallet - sum_
        with transaction.atomic():
            obj.user.save()
            obj.film_session.save()
            obj.save()
        return super().form_valid(form=form)


class PurchaseListView(UserPassesTestMixin, ListView):
    model = Purchase
    template_name = 'purchase.html'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['total_exp'] = Purchase.objects.filter(user=self.request.user).aggregate(te=Sum('film_session__price'))
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.is_superuser:
            return qs.all()
        else:
            return qs.filter(user=self.request.user)


class HallUpdateView(UserPassesTestMixin, UpdateView):
    model = Hall
    form_class = HallForm
    template_name = 'updateHall.html'
    success_url = '/'

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        obj = form.save(commit=False)
        FilmSession.objects.filter(hall__id=obj.id).update(hall_size=obj.size)
        obj.save()
        return super().form_valid(form=form)


class FilmSessionUpdateView(UpdateView):
    model = FilmSession
    form_class = FilmSessionForm
    template_name = 'updateSession.html'
    success_url = '/'

    def form_valid(self, form):
        obj = form.save(commit=False)
        size = obj.hall.size
        obj.hall_size = size
        obj.save()
        return super().form_valid(form=form)
