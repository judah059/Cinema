from django.contrib import admin
from .models import MyUser, Hall, Film, FilmSession, Purchase

admin.site.register(MyUser)
admin.site.register(Hall)
admin.site.register(Film)
admin.site.register(FilmSession)
admin.site.register(Purchase)

# Register your models here.
