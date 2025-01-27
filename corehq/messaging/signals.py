from django.conf import settings

from corehq.messaging.tasks import sync_case_for_messaging
from corehq.form_processor.models import CommCareCase
from corehq.form_processor.signals import sql_case_post_save
from dimagi.utils.logging import notify_exception


def messaging_case_changed_receiver(sender, case, **kwargs):
    try:
        sync_case_for_messaging.delay(case.domain, case.case_id)
    except Exception:
        notify_exception(
            None,
            message="Could not create messaging case changed task. Is RabbitMQ running?"
        )


def connect_signals():
    if settings.SYNC_CASE_FOR_MESSAGING_ON_SAVE:
        sql_case_post_save.connect(
            messaging_case_changed_receiver,
            CommCareCase,
            dispatch_uid='messaging_sql_case_receiver'
        )
