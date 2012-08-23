#coding:utf8
try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.contrib import auth
from django.http import HttpResponse
from tastypie.exceptions import ImmediateHttpResponse, BadRequest, NotFound
from tastypie.resources import ModelResource
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import UNUSABLE_PASSWORD
from django.conf import settings
from django.utils.http import base36_to_int, int_to_base36
from django.contrib.auth.models import User

UserCreationForm = __import__(
    getattr(settings, 'TASTYPIE_USER_CREATION_FORM', 'django.contrib.auth.forms.UserCreationForm')
)

CAN_CHANGE_UNUSABLE_PASSWORD = getattr(settings, 'CAN_CHANGE_UNUSABLE_PASSWORD', True)
AUTO_LOGIN_AFTER_RESET_PASSWORD = getattr(settings, 'AUTO_LOGIN_AFTER_RESET_PASSWORD', True)


def change_password(user, new_password):
    if not user.is_authenticated():
        raise NotFound

    if new_password == UNUSABLE_PASSWORD and not CAN_CHANGE_UNUSABLE_PASSWORD:
        raise BadRequest('not allowed to change blank password')

    if new_password:
        user.set_password(new_password)
    else:
        raise BadRequest('no password filled')


#不会在UserResource里设定Meta，不会被继承，可扩展性也被降低了

class UserResource(ModelResource):

    def obj_create(self, bundle, request=None, **kwargs):
        create_type = bundle.data.pop('create_type', 'register')

        if create_type == 'register':
            form = UserCreationForm(bundle.data)
            if form.is_valid():
                new_user = form.save()
                new_user.save()
                new_user.send_email_to_activate({
                    'uid': int_to_base36(new_user.id),
                    'token': default_token_generator.make_token(new_user),
                    'uri': self.get_resource_uri(),
                    })#requeire django_user package
                bundle.obj = new_user
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
                keys = {
                    'username': user.username,
                    'api_key': user.api_key.api_key,
                    'session_name': settings.SESSION_COOKIE_NAME,
                    'session_key': request.session.session_key,
                    }
                raise ImmediateHttpResponse(
                    HttpResponse(json.dumps(keys),content_type='application/json')
                )
        else:
            raise BadRequest

        return bundle

        # Support password change
    def obj_update(self, bundle, request=None, skip_errors=False, **kwargs):
        action_type = bundle.data.pop('action_type')

        if action_type:#triggerre by action/function

            if action_type == 'change_password':
                change_password(request.user, bundle.data.get('password'))

            elif action_type == 'request_reset_password':
                try:
                    email = bundle.data.get('email')
                    if not email: raise BadRequest

                    user = User.objects.get(email=email)
                    user.send_email_to_reset_password({
                        'uid': int_to_base36(user.id),
                        'token': default_token_generator.make_token(user),
                        'uri': self.get_resource_uri(),
                    })
                except:
                    raise NotFound

            elif action_type == 'reset_password':
                uid = base36_to_int(bundle.data['uid'])
                user = User.objects.get(id=uid)
                if default_token_generator.check_token(user, bundle.data['token']):
                    change_password(user, bundle.data.get('password'))

                    if AUTO_LOGIN_AFTER_RESET_PASSWORD:
                        user.backend = 'django.contrib.auth.backends.ModelBackend'
                        auth.login(request or bundle.request,user)
                else:
                    raise BadRequest

            elif action_type == 're_activate':
                uid = base36_to_int(bundle.data['uid'])
                user = User.objects.get(id=uid)
                if default_token_generator.check_token(user, bundle.data['token']):
                    user.send_email_to_activate({
                        'uid': int_to_base36(user.id),
                        'token': default_token_generator.make_token(user),#this will be new token
                        'uri': self.get_resource_uri(),
                        })
                else:
                    raise BadRequest

            return bundle

        else:#normal property update
            return super(UserResource, self).obj_update(bundle, request=request, skip_errors=skip_errors, **kwargs)


    def dehydrate(self, bundle):
        bundle.data['email'] = ''
        bundle.data['password'] = ''
        return bundle
