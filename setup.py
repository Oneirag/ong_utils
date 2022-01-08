from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='ong_utils',
    version='0.2.1',
    packages=['ong_utils'],
    url='www.neirapinuela.es',
    license='',
    author='ongpi',
    author_email='oneirag@yahoo.es',
    description='Common utilities for python projects',
    install_requires=required,
)
