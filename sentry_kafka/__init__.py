"""
sentry_kafka
~~~~~~~~~~~~~~
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry_kafka').version
except Exception, e:
    VERSION = 'unknown'
