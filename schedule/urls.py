from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

urlpatterns = [
    url(r'^predict/', 'schedule.views.predict'),
    url(r'^get_csv/', 'schedule.views.get_csv'),
    url(r'^', 'schedule.views.main'),
]
