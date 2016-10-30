from django.conf.urls import url, include
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from medlemssys.api import views


router = DefaultRouter()
router.register(r'medlem', views.MedlemViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'innmelding', views.medlem_innmelding, name='api-innmelding'),
    url(r'token', obtain_auth_token),
]
