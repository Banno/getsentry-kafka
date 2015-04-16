#!/usr/bin/env python
"""
sentry-kafka
==============

An extension for Sentry which integrates with Apache Kafka. It will forward
events to a Kafka instance for logging.
"""
from setuptools import setup, find_packages

install_requires = [
    'kafka-python>=0.9.2',
    'sentry>=6.0.0',
]

setup(
    name='sentry-kafka',
    version='1.1',
    download_url='https://github.com/banno/getsentry-kafka/tarball/1.0',
    author='Chad Killingsworth - Jack Henry and Associates, Inc.',
    author_email='chadkillingsworth@banno.com',
    url='http://github.com/banno/getsentry-kafka',
    description='A Sentry extension which integrates with Apache Kafka.',
    long_description=__doc__,
    license='Apache-2.0',
    packages=find_packages(),
    zip_safe=False,
    install_requires=install_requires,
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'sentry_kafka = sentry_kafka ',
        ],
        'sentry.plugins': [
            'kafka = sentry_kafka.models:KafkaMessage',
         ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
