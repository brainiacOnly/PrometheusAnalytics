from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

urlpatterns = [
    url(r'^login/$', 'loginsys.views.login'),
    url(r'^logout/$', 'loginsys.views.logout'),
    url(r'^register/$', 'loginsys.views.register'),
]
