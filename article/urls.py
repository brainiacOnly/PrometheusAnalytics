from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf.urls.static import static

urlpatterns = [
    url(r'^about/', 'article.views.about'),
    #url(r'^articles/all/$', 'article.views.articles'),
    #url(r'^articles/get/(?P<article_id>\d+)/$', 'article.views.article'),
    #url(r'^articles/addlike/(?P<article_id>\d+)/$', 'article.views.addlike'),
    #url(r'^articles/addcomment/(?P<article_id>\d+)/$', 'article.views.addcomment'),
    url(r'^index/', 'article.views.face'),
    url(r'^main/', 'article.views.face'),
    url(r'^profile/', 'article.views.profile'),
    #url(r'^underconstruction/', 'article.views.about'),
    url(r'^course/set_course/$', 'article.views.set_course'),
    url(r'^course/(?P<id>\w+)/$', 'article.views.course'),
    url(r'^platform/(?P<id>\w+)/$', 'article.views.platform'),
    url(r'^', 'article.views.face'),
]
