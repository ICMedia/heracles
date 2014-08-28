from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    url(r'^$', 'sitewide.views.frontpage'),

    url(r'^auth/login/$', 'sitewide.views.login', name='auth-login'),
    url(r'^auth/logout/$', 'sitewide.views.logout', name='auth-logout'),
)
