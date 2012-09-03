#coding:utf8
from django.contrib.auth.forms import UserCreationForm as BasicUserForm
from django.conf import settings
from tastypie_user.models import User
from django import forms
from django.utils.translation import ugettext_lazy as _


MIN_PASSWORD_LENGTH = getattr(settings, 'MIN_PASSWORD_LENGTH', 6)


class UserCreationForm(BasicUserForm):
    def clean_password1(self):
        password1 = self.cleaned_data.get("password1", "")
        if len(password1) < MIN_PASSWORD_LENGTH:
            raise forms.ValidationError(_('password should be longer than %s' %
                                          MIN_PASSWORD_LENGTH))
        return password1

    class Meta:
        model = User
        fields = ("username", )
