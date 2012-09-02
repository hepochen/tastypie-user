#!/usr/bin/env python
''' Setup File for backend '''
from setuptools import setup

setup(
    name="tastypie-user",
    version="0.0.1",
    description='A RESTful APIs for User resource',
    author="Hepochen",
    author_email="hepochen@gmail.com",
    url="https://github.com/hepochen/",
    packages=[
        'tastypie_user',
        'tastypie_user.tests'],
    package_data={
        'tastypie_user': ['templates/tastypie-user/emails/*']},
    long_description="Please see README.me"
)
