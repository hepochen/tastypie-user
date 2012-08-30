#coding:utf8
from django.conf.urls import patterns, include, url
from tastypie.api import Api

from tastypie_user.resources import UserResource
v1_api = Api(api_name='v1')
v1_api.register(UserResource())

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'service.views.home', name='home'),
    # url(r'^service/', include('service.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include(v1_api.urls)),
)
