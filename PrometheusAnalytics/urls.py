from django.conf.urls import include, url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/', include('loginsys.urls')),
    url(r'^analysis/', include('schedule.urls')),
    url(r'^', include('article.urls')),
]
