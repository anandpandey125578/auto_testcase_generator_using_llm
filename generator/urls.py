from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("review/", views.review, name="review"),
    path("review/download/", views.download_csv, name="download_csv"),
    path("generate/", views.generate, name="generate"),
    path("output/", views.output, name="output"),
    path("output/download/", views.download_code, name="download_code"),
]
