from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from cinapp.API.resources import CustomAuthToken, FilmModelViewSet, HallModelViewSet, FilmSessionModelViewSet, \
    PurchaseModelViewSet, ApiRegistration
from cinapp.views import FilmSessionListView, Login, Logout, Registration, FilmListView, FilmCreateView, HallListView, \
    HallCreateView, FilmSessionCreateView, FilmSessionDetailView, PurchaseListView, HallUpdateView, \
    FilmSessionUpdateView


router = SimpleRouter()
router.register('film', FilmModelViewSet)
router.register('hall', HallModelViewSet)
router.register('session', FilmSessionModelViewSet)
router.register('purchase', PurchaseModelViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', FilmSessionListView.as_view(), name='sessions'),
    path('login/', Login.as_view(), name='login'),
    path('registartion/', Registration.as_view(), name='registration'),
    path('logout/', Logout.as_view(), name='logout'),
    path('hall/create/', HallCreateView.as_view(), name='hall-create'),
    path('hall/', HallListView.as_view(), name='hall'),
    path('film/create/', FilmCreateView.as_view(), name='film-create'),
    path('film/', FilmListView.as_view(), name='film'),
    path('sessions/create/', FilmSessionCreateView.as_view(), name='sessions-create'),
    path('detail/<int:pk>/', FilmSessionDetailView.as_view(), name='sessions-detail'),
    path('purchase/', PurchaseListView.as_view(), name='purchase'),
    path('hall/update/<int:pk>/', HallUpdateView.as_view(), name='update-hall'),
    path('session/update/<int:pk>/', FilmSessionUpdateView.as_view(), name='update-session'),
    path('api-token-auth/', CustomAuthToken.as_view()),
    path('api/', include(router.urls)),
    path('api-registration/', ApiRegistration.as_view()),

]
