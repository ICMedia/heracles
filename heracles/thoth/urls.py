from django.conf.urls import patterns, include, url
from django.contrib import admin

from . import views as v

urlpatterns = patterns('',
    url(r'^$', v.IndexView.as_view(), name='thoth-home'),
    url(r'^booking/(?P<pk>\d+)/$', v.HandleBookingView.as_view(), name='thoth-booking'),
    url(r'^item/(?P<slug>[a-z0-9\-]+)/$', v.PublicItemCalendarView.as_view(), name='thoth-public-item-calendar'),
    url(r'^booking/new/$', v.PublicMakeView.as_view(), name='thoth-public-make'),
    url(r'^booking/my/$', 'thoth.views.dummy', name='thoth-public-view'),
    url(r'^admin/list/$', 'thoth.views.dummy', name='thoth-admin-list'),
    url(r'^admin/pending/$', 'thoth.views.dummy', name='thoth-admin-pending'),
)
