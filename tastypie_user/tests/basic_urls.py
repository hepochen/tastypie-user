#coding:utf8
from django.conf.urls import patterns, include, url
from tastypie.api import Api
from tastypie_user.resources import UserResource


v1_api = Api(api_name='v1')
v1_api.register(UserResource())

urlpatterns = patterns(
    '',
    url(r'^api/', include(v1_api.urls)),
)
