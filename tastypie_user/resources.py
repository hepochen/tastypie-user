#coding:utf8
try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.contrib import auth
from django.http import HttpResponse
from tastypie.exceptions import ImmediateHttpResponse, BadRequest
from tastypie.resources import ModelResource
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.conf import settings
from django.utils.http import base36_to_int
from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from tastypie_user.utils import lazy_import
from tastypie import http


UserCreationForm = lazy_import(
    getattr(settings, 'TASTYPIE_USER_CREATION_FORM', 'django.contrib.auth.forms.UserCreationForm')
)
CAN_CHANGE_UNUSABLE_PASSWORD = getattr(settings, 'CAN_CHANGE_UNUSABLE_PASSWORD', True)
AUTO_LOGIN_AFTER_RESET_PASSWORD = getattr(settings, 'AUTO_LOGIN_AFTER_RESET_PASSWORD', True)

def change_password(user, new_password):
    if not user.is_authenticated():
        raise BadRequest('change password need login')

    if new_password == UNUSABLE_PASSWORD and not CAN_CHANGE_UNUSABLE_PASSWORD:
        raise BadRequest('not allowed to change blank password')

    if new_password:
        user.set_password(new_password)
        user.save()
    else:
        raise BadRequest('no password filled')


class UserResource(ModelResource):

    def show_keys(self,request):
        if request.user.is_authenticated():
            api_key = request.user.api_key.key
            keys = {
                'username': request.user.username,
                'api_key': api_key,
                'session_name': settings.SESSION_COOKIE_NAME,
                'session_key': request.session.session_key,
                }
            raise ImmediateHttpResponse(
                HttpResponse(json.dumps(keys),content_type='application/json')
            )
        else:
            raise BadRequest('not login')

    def obj_create(self, bundle, request=None, **kwargs):
        create_type = bundle.data.pop('type', 'register')

        if create_type == 'register':
            form = UserCreationForm(bundle.data)
            if form.is_valid():
                new_user = form.save()
                new_user.send_email('activate')
                bundle.obj = new_user
                raise ImmediateHttpResponse(http.HttpAccepted())
                #auto login, means request twice, first register, then login!
            else:
                #output the errors for tatstypie
                bundle.errors[self._meta.resource_name] = form.errors
                self.error_response(bundle.errors, request)

        elif create_type == 'login':
            expiry_seconds = bundle.data.pop('expiry_seconds', None)
            user = auth.authenticate(**bundle.data)

            if user is not None and user.is_active:
                auth.login(request, user)
                if expiry_seconds:
                    request.session.set_expiry(int(expiry_seconds))
                self.show_keys(request)
            else:
                raise BadRequest('login error')

        else:
            raise BadRequest('create user resource error')

    def get_detail(self, request=None, **kwargs):
        if kwargs.get('pk') == 'me':
            self.show_keys(request)
        else:
            return super(UserResource,self).get_detail(request,**kwargs)

    def patch_detail(self, request, **kwargs):
        data = json.loads(request.META.get('data',request.raw_post_data))
        action_type = data.pop('action',None)
        if action_type:#triggerre by action/function
            if action_type == 'change_password':
                change_password(request.user, data.get('new_password'))

            elif action_type == 'request_reset_password':
                try:
                    email = data.get('email')
                    if not email:
                        raise BadRequest('need email address to reset password')
                    user = User.objects.get(email=email)
                    user.send_email('reset_password')
                except User.DoesNotExist:
                    raise BadRequest('the email is not registered')

            elif action_type == 're_activate':
                try:
                    user = User.objects.get(username=data.get('username'))
                    if user.is_active:
                        raise BadRequest('already activated')
                    else:
                        user.send_email('re_activate')
                except User.DoesNotExist:
                    raise BadRequest('need username')

            elif action_type == 'reset_password':
                uid = base36_to_int(data['uid'])
                user = User.objects.get(id=uid)
                if default_token_generator.check_token(user, data['token']):
                    change_password(user, data.get('new_password'))

                    if AUTO_LOGIN_AFTER_RESET_PASSWORD:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        auth.login(request,user)
                else:
                    raise BadRequest('token error can not reset your password')

            else:
                raise BadRequest('not allowed ')

            #at last
            raise ImmediateHttpResponse(http.HttpAccepted())

        else:
            if request.user.is_authenticated():
                return super(UserResource,self).patch_detail(request,**kwargs)
            else:
                raise BadRequest('can not modify info of other user')


    def obj_delete(self, request=None, **kwargs):
        delete_type = kwargs.get('pk')

        if delete_type == 'session':
            auth.logout(request)
        else:
            raise BadRequest('This delete type is not allowed')

    def delete_list(self, request=None, **kwargs):
        raise BadRequest('not allowed')

    def patch_list(self, request, **kwargs):
        raise BadRequest('not allowed')

    def obj_get_list(self, request=None, **kwargs):
        raise BadRequest('not allowed')


    def dehydrate(self, bundle):
        bundle.data['email'] = ''
        bundle.data['password'] = ''
        return bundle

    class Meta:
        queryset = User.objects.filter()
        resource_name = 'user'
        detail_allowed_methods = ['get','patch','put','delete']
        list_allowed_methods = ['get','post','delete','patch']
        fields = ['first_name','last_name']
        authorization = Authorization()
