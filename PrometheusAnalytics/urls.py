from django.conf.urls import include, url
from django.contrib import admin

"""
urlpatterns = [
    # Examples:
    # url(r'^$', 'PrometheusAnalytics.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
]
"""

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^auth/', include('loginsys.urls')),
    url(r'^schedule/', include('schedule.urls')),
    url(r'^', include('article.urls')),
]
