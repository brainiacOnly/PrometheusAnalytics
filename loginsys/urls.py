from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

urlpatterns = [
    url(r'^login/$', 'loginsys.views.login'),
    url(r'^logout/$', 'loginsys.views.logout'),
    url(r'^register/$', 'loginsys.views.register'),
    url(r'^allow_user/(?P<username>\w{0,50})/$', 'loginsys.views.allow_user'),
    url(r'^deny_user/(?P<username>\w{0,50})/$', 'loginsys.views.deny_user'),
]
