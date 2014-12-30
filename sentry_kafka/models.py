"""
sentry_kafka.models
~~~~~~~~~~~~~~~~~~~~~
"""

from django import forms
from django.conf import settings
from kafka import KafkaClient, SimpleProducer

from sentry.plugins.bases.notify import NotifyPlugin

import sentry_kafka

import json
import re
import types

class KafkaOptionsForm(forms.Form):
    kafka_instance = forms.CharField(help_text="Your Kafka instance (including port")
    topic = forms.CharField(help_text="Kafka topic - will use \"Organization.Team.Project\" by default",
                            required=False)

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

    # def on_alert(self, alert, **kwargs):
    #   project = alert.project,
    #    team_name = alert.project.team.name,
    #    organization_name = alert.project.organization.name,
    #    project_name = alert.project.name,
    #    topic = self.get_option('', project) or KafkaMessage.get_default_topic(
    #       organization_name, team_name, project_name)
    #    endpoint = self.get_option('kafka_instance', project)
    #
    #    if endpoint:
    #        self.send_payload(
    #            endpoint=endpoint,
    #            topic=topic,
    #            message='{"type":"ALERT","org":"%(organization_name)s","team":"%(team_name)s",' +
    #                '"project":"%(project_name)s","platform":"%(platform)s","message":"%(message)s"}' % {
    #                'organization_name': organization_name,
    #                'team_name': team_name,
    #                'project_name': project_name,
    #                'platform': project.platform,
    #                'message': alert.message,
    #            }
    #        )
    
    def notify(self, notification):
        project = notification.event.project
        team_name = notification.event.project.team.name,
        organization_name = notification.event.project.organization.name,
        project_name = notification.event.project.name,
        topic = self.get_option('topic', project) or KafkaMessage.get_default_topic(
            organization_name, team_name, project_name)
        endpoint = self.get_option('kafka_instance', project)

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
                     'data': json.dumps(notification.event.as_dict(), default=KafkaMessage.date_serializer)
                 }
             )
 

    def send_payload(self, endpoint, topic, message):
        kafka = KafkaClient(endpoint)
        kafka.ensure_topic_exists(topic)
        producer = SimpleProducer(kafka, async=True)
        producer.send_messages(topic, message)
    
    @staticmethod
    def get_default_topic(organization, team, project):
        return '%s.%s.%s' % (
            KafkaMessage.invalid_topic_chars_expr.sub(r'_', KafkaMessage.list_to_string(organization)),
            KafkaMessage.invalid_topic_chars_expr.sub(r'_', KafkaMessage.list_to_string(team)),
            KafkaMessage.invalid_topic_chars_expr.sub(r'_', KafkaMessage.list_to_string(project))
        )
    
    @staticmethod
    def list_to_string(obj):
        return str(obj) if isinstance(obj, types.StringTypes) else str(obj[0])
    
    @staticmethod  
    def date_serializer(obj):
        return obj.isoformat() if hasattr(obj, 'isoformat') else obj
        