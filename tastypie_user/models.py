"""add a proxy User which has a new magical function named send_email"""
#coding:utf8
import warnings
from django.conf import settings
from django.contrib.auth.models import User
from tastypie_user.utils import send_email, load_email_content
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import int_to_base36


class MyUser(User):
    def send_email(self, action_type, ctx_dict=None, from_email=None):
        ctx_dict = ctx_dict or {}
        ctx_dict.update({
            'uid': int_to_base36(self.id),
            'token': default_token_generator.make_token(self),
        })

        if not self.email:
            warnings.warn('uid:%s has no email address' % self.id)
            return

        if from_email is None:
            from_email = settings.DEFAULT_FROM_EMAIL

        subject, message, subtype = load_email_content(action_type, ctx_dict)
        send_email(subject, message, from_email, self.email, subtype)

    class Meta:
        proxy = True
