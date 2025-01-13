from django.urls import path
from django.conf import settings
from . import views
from django.conf.urls.static import static
urlpatterns = [
    path("drone_image/", views.drone_image, name="index"),
    path("drone_video/", views.drone_video, name="index"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)