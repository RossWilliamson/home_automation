# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='home',
    version='0.1.0',
    description='Module for controling the home',
    long_description=readme,
    author='Ross Williamson',
    author_email='tweekzilla@gmial.com',
    url='https://github.com/RossWilliamson/home_automation',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

