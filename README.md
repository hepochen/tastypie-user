Tastypie User
======


## Installation and Configs
###  install tastypie-user in settings.py
	INSTALLED_APPS = (
	    #.....
	    'tastypie_user',
		#.....
		)


### add authentication backends in settings.py
	AUTHENTICATION_BACKENDS = (
	    'tastypie_user.auth_backends.ApiKeyBackend',
	    'tastypie_user.auth_backends.EmailBackend',
	    'django.contrib.auth.backends.ModelBackend',
	    )
		
### config you user creation form
In the setting.py, set your owner TASTYPIE_USER_USER_CREATION_FORM, default value is 'django.contrib.auth.forms.UserCreationForm' .

The Form is a validation when your client try to create a new user.

### other configs
* PASSWORD_RESET_TIMEOUT_DAYS, default is 3

* MIN_PASSWORD_LENGTH, default is 6

* CAN_CHANGE_UNUSABLE_PASSWORD, default is True
	* the blank password is '!'
	* if you create a user without password, '!' will fill the password field.
	* if you use social_auth, you will find it should be needed.
	
* AUTO_LOGIN_AFTER_RESET_PASSWORD, default is True

* TASTYPIE_USER_TEMPLATE_FOLDER





## Register & Login & .etc
suppose the user list endpoint is '/user/'

### Register
The method your client from fontend should be POST, the type=register is necessary, it tells the user list endpoint how to create a resource.

And the others fields in your data, it depends the TASTYPIE_USER_USER_CREATION_FORM in your settings.py.

	client.POST('/user/',
		data={
			'type': 'register',
			'username': 'hello',
			'email': 'youremail@google.com',
			'more_fields': 'your value'
		}
	)

### Login
1, The method is also 'POST', and type=login is necessary, it tells the user list endpoint to create a user resource for user. If you use it on the WEB, the login user resource would be session which stored session_key in the COOKIE.

2, After login, you will get a response, formated in JSON, and the data would look like:

	{
		"username": "your_username",
		"api_key": "apikey-lookslike-sdfagdfokg",
		"session_name": "session_id"
		"session_key": "lookslikekemcnckfhalmxckfhfh"
	}
	#btw, if you call the api in WEB site, the session_name, session_key already saved in your COOKIE, which makes you login without a new request.
	
3, AUTHENTICATION_BACKENDS in your settings.py is very important, when you using the login method.

For example, if config in settings is this:

	AUTHENTICATION_BACKENDS = (
	    'tastypie_user.auth_backends.ApiKeyBackend',
	    'tastypie_user.auth_backends.EmailBackend',
	    'django.contrib.auth.backends.ModelBackend',
	    )

Then, the three ways below will work well.

	client.POST('/user/',
		data={
			'type': 'login',
			'username': 'username',
			'password': 'password'
		}
	)
	
	client.POST('/user/',
		data={
			'type': 'login',
			'email': 'youremail@google.com',
			'password': 'password'
		}
	)
	
	client.POST('/user/',
		data={
			'type': 'login',
			'username': 'username',
			'api_key': 'apikey-lookslike-sdfagdfokg'
		}
	)

### Get Keys
if you login already, then request to '/user/keys/' in 'GET' method, you also can get the keys. 

	{
		"username": "your_username",
		"api_key": "apikey-lookslike-sdfagdfokg",
		"session_name": "session_id"
		"session_key": "lookslikekemcnckfhalmxckfhfh"
	}

### Request Rest Password
We thought this is a way to update the user resource, so you need to PATCH it.

	client.PATCH('/user/me/',
		data={
			'action': 'request_reset_password',			
			'email': 'youremail@gmail.com'			
		}
	)
btw, the endpoint '/user/anything/' also works, but '/user/me/' looks natural.

This request will get a on content responce, but a reset password mail is sent to the email address. uid(in base36 format) & token is neccessary in the mail. And the two thinng is passed to email content template automaticly.

What's more, the token will be timeout in 3 days defaultly. but you can config it in your settings.py, the config is PASSWORD_RESET_TIMEOUT_DAYS.

### Reset Password
The uid and token is passing throught email, but your client (user) should input the new password.

It will return the keys, because the api_key will be changed when password is changed.

	client.PATCH('/user/me/',
		data={
			'action': 'reset_password',
			'uid': 'int in base36 formate'
			'token': 'thetokenkey',
			'new_password': 'new_password'
		}
	)


### Change Password
This method is only available after you login. It will return the keys, because the api_key will be changed when password is changed.

	client.PATCH('/user/me/',
		data={
			'action': 'change_password',
			'new_password': 'new_password'
		}
	)


### ReActivate
If you wanna re send a activate email to user, you will need this method. It return a no content response.

	client.PATCH('/user/me/',
		data={
			'action': 're_activate',
			'username': 'yourname'
		}
	)

### Logout & Reset Api Key
The DELETE methods is only available after you login.

If you delete session, it works on the WEB. and you also can to reset a new api key.


	client.DELETE('/user/session/')
	
	client.DELETE('/user/api_key/')


## Special Methods

### user.send_email

We bind a new method to User Model, called 'send_email'.

It accepts the vars like this:

	user.send_email('activate')
	user.send_email('activate', ctx_dict={'more_args':'more_value'})
	user.send_email('activate', from_email='yourmail@gmail.com')

By default, we gave two vars in the mail content context: token & uid (in base36 formate).

For example， if you call user.send_mail('activate')：

* make sure the file named 'active.txt' or 'activate.html' is in your templates folders
* 'activate.html' will be used firstly if it exists, and sending the mail in html format
* if only 'activate.txt' can be used, the email will be sent in plain text format.
* if you have a template named 'activate_subject.txt', the subject of the email will be from this file content, otherwise it will be the default value, which means 'Active'.

### what's the template_folder?
It's very important, when you wana custom your own email content templates, change TASTYPIE_USER_TEMPLATE_FOLDER in your settings.py.

The default value of this config is 'tastypie-user'. If you call user.send_mail('activate'), Tastypie-User will try to find the template at 'tastypie-user/emails/activate.html'.

For example, if you change it to 'yourapp', Tastypie-User will try to find the template at 'yourapp/emails/activate.html'.




