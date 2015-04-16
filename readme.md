# sentry-kafka

An extension for [Sentry](https://github.com/getsentry/sentry) to forward events to [Apache Kafka](http://kafka.apache.org/) for logging.

## Configuration
Enable the plugin in your project's configuration page (Projects -> [Project]) under Manage Integrations.

Go to your project's configuration page (Projects -> [Project]) and select the Kafka Logging tab. Enter the broker and topic settings.

You may optionally set the broker in the sentry config:

    KAFKA_BROKER='my.broker.com:9092'

When set in the config, the broker field will be readonly for all projects.
