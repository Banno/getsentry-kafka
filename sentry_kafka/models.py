"""
sentry_kafka.models
~~~~~~~~~~~~~~~~~~~~~
"""

from django import forms
from django.conf import settings
from django.core import (validators, exceptions)
from kafka import KafkaClient, SimpleProducer

from sentry.plugins.bases.notify import NotifyPlugin

import sentry_kafka

import json
import re
import types


def KafkaOptionsFormValidateDots(value):
    if value == '.' or value == '..':
        raise exceptions.ValidationError('Topic cannot be "." or ".."')


class KafkaOptionsForm(forms.Form):
    valid_topic_expr = re.compile('^[-_.a-z0-9]+$', re.IGNORECASE)
    kafka_instance = forms.CharField(
        help_text="Your Kafka broker connection string (may be a comma separated list of brokers)",
        required=True)
    topic = forms.CharField(
        help_text="Kafka topic - will use \"Organization.Team.Project\" by default",
        required=False, max_length=255,
        validators=[validators.RegexValidator(
            regex=valid_topic_expr,
            message='Topics may only include alphanumeric characters, numbers, periods, dashes and underscores'),
            validators.MaxLengthValidator(255),
            KafkaOptionsFormValidateDots])
    assume_topic_exists = forms.BooleanField(
        help_text="Do not check for existence or manually create the topic before sending the message.",
        initial=False, required=False)

    def __init__(self, *args, **kwargs):
        super(KafkaOptionsForm, self).__init__(*args, **kwargs)

        # If the broker is set in the settings configuration, disable the field
        if settings.KAFKA_BROKERS:
            self.fields['kafka_instance'].widget.attrs['disabled'] = True
            self.fields['kafka_instance'].required = False
            self.fields['kafka_instance'].initial = settings.KAFKA_BROKERS

    def clean(self):
        super(KafkaOptionsForm, self).clean()
        if settings.KAFKA_BROKERS:
            self.cleaned_data['kafka_instance'] = settings.KAFKA_BROKERS
        return self.cleaned_data


class KafkaMessage(NotifyPlugin):
    author = 'Chad Killingsworth, Jack Henry and Associates'
    author_url = 'https://github.com/banno/sentry-kafka'
    version = sentry_kafka.VERSION
    description = "Forward events to Kafka for logging."
    resource_links = [
        ('Bug Tracker', 'https://github.com/banno/sentry-kafka/issues'),
        ('Source', 'https://github.com/banno/sentry-kafka'),
    ]
    slug = 'kafka'
    title = 'Kafka Logging'
    conf_title = title
    conf_key = 'kafka'
    project_conf_form = KafkaOptionsForm
    timeout = getattr(settings, 'SENTRY_KAFKA_TIMEOUT', 3)
    invalid_topic_chars_expr = re.compile(r'[^-a-z0-9]+', re.IGNORECASE)

    def is_configured(self, project):
        return all((self.get_option(k, project) for k in ('kafka_instance')))

    def notify(self, notification):
        project = notification.event.project
        team_name = notification.event.project.team.name,
        organization_name = notification.event.project.organization.name,
        project_name = notification.event.project.name,
        topic = self.get_option('topic',
            project) or KafkaMessage.get_default_topic(
            organization_name, team_name, project_name)
        endpoint = (settings.KAFKA_BROKERS or
            self.get_option('kafka_instance', project))
        assume_topic_exists = self.get_option('assume_topic_exists',
            project) or False

        topic = topic[0:255]  # Kafka topics must be at most 255 characters

        if endpoint:
            self.send_payload(
                endpoint=endpoint,
                topic=topic,
                message='{"type":"ALERT","org":"%(organization_name)s","team":"%(team_name)s",' +
                        '"project":"%(project_name)s","platform":"%(platform)s","message":"%(message)s"' +
                        '"data":%(data)s}' % {
                            'organization_name': organization_name,
                            'team_name': team_name,
                            'project_name': project_name,
                            'message': notification.event.error(),
                            'data': json.dumps(notification.event.as_dict(),
                                default=KafkaMessage.date_serializer)
                        },
                ensure_topic_exists=not assume_topic_exists
            )


    def send_payload(self, endpoint, topic, message, ensure_topic_exists=True):
        kafka = KafkaClient(endpoint)
        if ensure_topic_exists:
            kafka.ensure_topic_exists(topic)

        producer = SimpleProducer(kafka, async=True)
        producer.send_messages(topic, message)

    @staticmethod
    def get_default_topic(organization, team, project):
        return ('%s.%s.%s' % (
            KafkaMessage.invalid_topic_chars_expr.sub('_',
                KafkaMessage.list_to_string(organization)),
            KafkaMessage.invalid_topic_chars_expr.sub('_',
                KafkaMessage.list_to_string(team)),
            KafkaMessage.invalid_topic_chars_expr.sub('_',
                KafkaMessage.list_to_string(project))
        ))

    @staticmethod
    def list_to_string(obj):
        return str(obj) if isinstance(obj, types.StringTypes) else str(obj[0])

    @staticmethod
    def date_serializer(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj
