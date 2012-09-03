#coding:utf8
from django.test import TestCase
from tastypie.test import TestApiClient
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.contrib.sessions.models import Session
from django.contrib.auth.tokens import default_token_generator
from django.db.models.signals import post_save
from tastypie.models import create_api_key
from django.utils.http import int_to_base36

post_save.connect(create_api_key, sender=User)


def is_login_by_session(session_key):
    session = Session.objects.get(session_key=session_key)
    uid = session.get_decoded().get('_auth_user_id')
    return bool(uid)


class TastypieUserTest(TestCase):
    endpoint_uri = '/api/v1/user/'
    resource_name = 'user'

    def setUp(self):
        user = User(
            username='hepochen',
            email='hepochen@gmail.com',
            first_name='Hepo',
            last_name='Chen')
        user.set_password('test_password')
        user.save()
        self.user = user
        self.users_count = User.objects.count()

    @property
    def api_client(self):
        return TestApiClient()

    def check_status(self, response, codes):
        if type(codes) == int:
            codes = [codes, ]
        self.assertTrue(
            response.status_code in codes,
            'status_code should be in %s, return %s. contents is:\n %s' % (
                codes, response.status_code, response.content)
        )

    def login(self):
        client = self.api_client
        response = client.post(
            self.endpoint_uri,
            data={
                "type": "login",
                "username": self.user.username,
                "password": "test_password",
                "expiry_seconds": 0})
        return client, response

    def check_login(self, data, error=False):
        login_response = self.api_client.post(self.endpoint_uri, data=data)

        if not error:
            keys = json.loads(login_response.content)
            self.check_status(login_response, 200)
            self.assertEqual(
                len(keys),
                4,
                'The length we got should 4, now is %s' % len(keys))
        else:
            self.check_status(login_response, 400)

    def check_register(self, data, error_field=None):
        response = self.api_client.post(self.endpoint_uri, data=data)
        if not error_field:
            self.check_status(response, 202)
            self.assertEqual(
                self.users_count + 1,
                User.objects.count(),
                'register failed'
            )
        else:
            errors = json.loads(response.content).get(self.resource_name)
            self.assertTrue(
                error_field in errors,
                'the field "%s" should raise error' % error_field
            )

    def test_register(self):
        self.check_register(
            data={
                "type": "register",
                "username": 'hello',
                "email": "hepo@ued.com.cn",
                "password1": "world_password",
                "password2": "world_password"
            }
        )

    def test_register_existed_username(self):
        self.check_register(
            data={
                "type": "register",
                "username": 'hepochen',
                "email": "hepo@ued.com.cn",
                "password1": "world_password",
                "password2": "world_password"
            },
            error_field='username'
        )

    def test_register_error_password(self):
        self.check_register(
            data={
                "type": "register",
                "username": 'hello',
                "email": "hepo@ued.com.cn",
                "password1": "world_password",
                "password2": "world_password2"
            },
            error_field='password2'
        )

    def test_register_error_password_length(self):
        self.check_register(
            data={
                "type": "register",
                "username": 'hello',
                "email": "hepo@ued.com.cn",
                "password1": "world",
                "password2": "world"
            },
            error_field='password1'
        )

    def test_login_with_username(self):
        self.check_login(
            data={
                "type": "login",
                "username": self.user.username,
                "password": "test_password",
                "expiry_seconds": 0}
        )

        self.check_login(
            data={
                "type": "login",
                "username": self.user.username,
                "password": "test+error",  # error
                "expiry_seconds": 0},
            error=True
        )

    def test_login_with_email(self):
        self.check_login(
            data={
                "type": "login",
                "email": self.user.email,
                "password": "test_password",
                "expiry_seconds": 0
            }
        )
        self.check_login(
            data={
                "type": "login",
                "email": self.user.email,
                "password": "test+error",  # error
                "expiry_seconds": 0
            },
            error=True
        )

    def test_login_with_api_key(self):
        self.check_login(
            data={
                "type": "login",
                "username": self.user.username,
                "api_key": self.user.api_key.key,
                "expiry_seconds": 0
            }
        )

        self.check_login(
            data={
                "type": "login",
                "username": self.user.username,
                "api_key": self.user.api_key.key + 'error',  # error
                "expiry_seconds": 0
            },
            error=True
        )

    def test_logout(self):
        no_login_res = self.client.delete(self.endpoint_uri + 'session/')
        self.check_status(no_login_res, 400)

        client, response = self.login()
        session_key = json.loads(response.content).get('session_key')

        def is_login(session_key):
            try:
                return is_login_by_session(session_key)
            except Session.DoesNotExist:
                return False

        self.assertTrue(is_login(session_key), 'Login failed.')

        response = client.delete(self.endpoint_uri + 'session/')
        self.check_status(response, 204)
        self.assertFalse(is_login(session_key), 'Login failed.')

    def test_reset_api_key(self):
        no_login_res = self.client.delete(self.endpoint_uri + 'api_key/')
        self.check_status(no_login_res, 400)

        client, response = self.login()
        old_api_key = json.loads(response.content).get('api_key')
        response = client.delete(self.endpoint_uri + 'api_key/')
        self.check_status(response, 204)
        new_api_key = User.objects.get(pk=self.user.pk).api_key.key
        self.assertNotEqual(old_api_key, new_api_key, 'api_key not changed')

    def test_get_keys(self):
        client, response = self.login()
        self.check_status(response, 200)
        new_response = client.get(self.endpoint_uri + 'keys/')
        keys = json.loads(new_response.content)
        self.assertEqual(len(keys), 4, 'We can not get the 4 length keys')

    def test_login_expiry(self):
        self.login()

        # try to get keys, will fail
        new_response = self.api_client.get(self.endpoint_uri + 'keys/')
        self.check_status(new_response, 400)

    def test_request_reset_password(self):
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'request_reset_password',
                'email': self.user.email
            }
        )
        self.check_status(response, 202)

        #without email
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'request_reset_password'
            }
        )
        self.check_status(response, 400)

        #with error_email
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'request_reset_password',
                'email': 'error' + self.user.email
            }
        )
        self.check_status(response, 400)

    def test_reset_password(self):
        old_api_key = self.user.api_key.key
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'reset_password',
                'uid': int_to_base36(self.user.id),
                'token': default_token_generator.make_token(self.user),
                'new_password': 'new_password'
            }
        )
        user = User.objects.get(pk=self.user.pk)
        self.check_status(response, 200)
        self.assertTrue(
            user.check_password('new_password'),
            'reset password failed')
        self.assertFalse(
            user.api_key.key == old_api_key,
            'the api_key is not updated!'
        )

    def test_change_password(self):
        not_login_response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'change_password',
                'new_password': 'new_password'
            }
        )
        self.check_status(not_login_response, 400)

        client, response = self.login()
        self.check_status(response, 200)
        login_response = client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 'change_password',
                'new_password': 'new_password'
            }
        )
        user = User.objects.get(pk=self.user.pk)
        self.check_status(login_response, 200)
        self.assertTrue(
            user.check_password('new_password'),
            'change password failed')

    def test_re_activate(self):
        self.user.is_active = False
        self.user.save()
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 're_activate',
                'username': self.user.username
            }
        )
        self.check_status(response, 202)

        #activated error
        self.user.is_active = True
        self.user.save()
        response = self.api_client.patch(
            self.endpoint_uri + 'me/',
            data={
                'action': 're_activate',
                'username': self.user.username
            }
        )
        self.check_status(response, 400)

    def test_GET_detail(self):
        response = self.api_client.get(
            self.endpoint_uri + '%s/' % self.user.pk)
        self.check_status(response, 200)

    def test_PATCH_detail(self):
        response = self.api_client.patch(
            self.endpoint_uri + '%s/' % self.user.pk, data={})
        self.check_status(response, 400)

        # client, response = self.login()
        # response = client.patch(
        #    self.endpoint_uri + '%s/'%self.user.pk,
        #    data={'first_name':'new_name'}
        # )
        # self.check_status(response, 202)
        # self.assertEqual(
        #    'new_name',
        #    User.objects.get(pk=self.user.pk).first_name,
        #    'normal patch user failed')

    def test_PATCH_list(self):
        response = self.api_client.patch(self.endpoint_uri, data={})
        self.check_status(response, [400, 404, 405])

    def test_DELETE_list(self):
        response = self.api_client.delete(self.endpoint_uri, data={})
        self.check_status(response, [400, 404, 405])
