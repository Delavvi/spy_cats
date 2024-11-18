from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MissionViewSet, SpyCatViewSet

router = DefaultRouter()
app_name = "spy_cats"

router.register(r'missions', MissionViewSet, basename='mission')
router.register(r'spycats', SpyCatViewSet, basename='spycat')

urlpatterns = [
    path('', include(router.urls)),
]