#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'rainp1ng'
from setuptools import find_packages, setup


def get_long_description():
    with open('README.rst', 'r', encoding='UTF-8') as reader:
        return reader.read()


setup(
    name="brain-hub",
    version="0.1",
    description=__doc__,
    long_description=get_long_description(),
    author=__author__,
    author_email="cn-zyp@163.com",
    url="https://github.com/rainp1ng/brain-hub",
    license="MIT",
    entry_points={
        'console_scripts': [
            'brainhub = brain_hub.server_hub:main',
        ]
    },
    packages=find_packages('src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    extras_require={
        'mysql': ['MySQL-python'],
        'web server': ['flask', 'tornado'],
        'yaml': ['yaml'],
    }
)
