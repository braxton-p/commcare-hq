from django.utils.translation import gettext as _

from couchdbkit import ResourceNotFound

from corehq import toggles
from corehq.apps.accounting.utils import domain_has_privilege
from corehq.apps.app_manager.dbaccessors import get_app
from corehq.apps.app_manager.exceptions import MultimediaMissingError
from corehq.apps.hqmedia.models import CommCareMultimedia
from corehq.apps.hqwebapp.tasks import send_html_email_async
from corehq.apps.linked_domain.remote_accessors import fetch_remote_media
from corehq.privileges import RELEASE_MANAGEMENT, LITE_RELEASE_MANAGEMENT
from corehq.util.timezones.conversions import ServerTime


def can_user_access_release_management(user, domain, include_lite_version=True, include_toggle=False):
    """
    :param include_lite_version: set to True if the LITE_RELEASE_MANAGEMENT privilege should be checked
    :param include_toggle: set to True if the deprecated linked domains toggle should be checked
    NOTE: can remove include_toggle once the linked domains toggle is deleted
    Checks if the current domain has any of the following enabled:
    - privileges.RELEASE_MANAGEMENT
    - privileges.LITE_RELEASE_MANAGEMENT
    - toggles.LINKED_DOMAINS
    If yes, and the user meets the criteria needed, returns True
    """
    if not user or not domain:
        return False

    is_admin = user.is_domain_admin(domain)

    if domain_has_privilege(domain, RELEASE_MANAGEMENT) and is_admin:
        return True
    if include_lite_version and domain_has_privilege(domain, LITE_RELEASE_MANAGEMENT) and is_admin:
        return True
    if include_toggle and toggles.LINKED_DOMAINS.enabled(domain):
        return True
    return False


def can_domain_access_release_management(domain, include_lite_version=True, include_toggle=False):
    """
    :param include_lite_version: set to True if the LITE_RELEASE_MANAGEMENT privilege should be checked
    :param include_toggle: set to True if the deprecated linked domains toggle should be checked
    NOTE: can remove include_toggle once the linked domains toggle is deleted
    Checks if the current domain has any of the following enabled:
    - privileges.RELEASE_MANAGEMENT
    - privileges.LITE_RELEASE_MANAGEMENT
    - toggles.LINKED_DOMAINS
    """
    if not domain:
        return False

    has_access = domain_has_privilege(domain, RELEASE_MANAGEMENT)
    if include_lite_version:
        has_access |= domain_has_privilege(domain, LITE_RELEASE_MANAGEMENT)
    if include_toggle:
        has_access |= toggles.LINKED_DOMAINS.enabled(domain)

    return has_access


def _clean_json(doc):
    if not isinstance(doc, dict):
        return doc
    doc.pop('domain', None)
    doc.pop('doc_type', None)
    doc.pop('_rev', None)
    for key, val in doc.items():
        if isinstance(val, dict):
            _clean_json(val)
        if isinstance(val, list):
            [_clean_json(inner_doc) for inner_doc in val]
    return doc


def convert_app_for_remote_linking(latest_master_build):
    _attachments = latest_master_build.get_attachments()
    source = latest_master_build.to_json()
    source['_LAZY_ATTACHMENTS'] = {
        name: {'content': content.decode('utf-8')}
        for name, content in _attachments.items()
    }
    source.pop("external_blobs", None)
    return source


def server_to_user_time(server_time, timezone):
    user_time = ServerTime(server_time).user_time(timezone).done()
    return user_time.strftime("%Y-%m-%d %H:%M")


def pull_missing_multimedia_for_app_and_notify(domain, app_id, email, force=False):
    app = get_app(domain, app_id)
    subject = _("Update Status for linked app %s missing multimedia pull") % app.name
    try:
        pull_missing_multimedia_for_app(app, force=force)
    except MultimediaMissingError as e:
        message = str(e)
    except Exception:
        # Send an email but then crash the process
        # so we know what the error was
        send_html_email_async.delay(subject, email, _(
            "Something went wrong while pulling multimedia for your linked app. "
            "Our team has been notified and will monitor the situation. "
            "Please try again, and if the problem persists report it as an issue."))
        raise
    else:
        message = _("Multimedia was successfully updated for the linked app.")
    send_html_email_async.delay(subject, email, message)


def pull_missing_multimedia_for_app(app, old_multimedia_ids=None, force=False):
    if force:
        media_to_pull = _get_all_media(app)
    else:
        media_to_pull = _get_missing_multimedia(app, old_multimedia_ids)
    remote_details = app.domain_link.remote_details
    fetch_remote_media(app.domain, media_to_pull, remote_details)
    if toggles.CAUTIOUS_MULTIMEDIA.enabled(app.domain):
        still_missing_media = _get_missing_multimedia(app, old_multimedia_ids)
        if still_missing_media:
            raise MultimediaMissingError(_(
                'Application has missing multimedia even after an attempt to re-pull them. '
                'Please try re-pulling the app. If this persists, report an issue.'
            ))


def _get_all_media(app):
    return [
        (path.split('/')[-1], media_info)
        for path, media_info in app.multimedia_map.items()
    ]


def _get_missing_multimedia(app, old_multimedia_ids=None):
    missing = []
    for path, media_info in app.multimedia_map.items():
        if old_multimedia_ids and media_info['multimedia_id'] in old_multimedia_ids:
            continue
        try:
            local_media = CommCareMultimedia.get(media_info['multimedia_id'])
        except ResourceNotFound:
            filename = path.split('/')[-1]
            missing.append((filename, media_info))
        else:
            _add_domain_access(app.domain, local_media)
    return missing


def _add_domain_access(domain, media):
    if domain not in media.valid_domains:
        media.add_domain(domain)


def is_linked_report(report):
    return report.report_meta.master_id


def is_domain_available_to_link(upstream_domain_name, candidate_name, user, should_enforce_admin=True):
    if not upstream_domain_name or not candidate_name:
        return False

    if candidate_name == upstream_domain_name:
        return False

    if is_domain_in_active_link(candidate_name):
        # cannot link to an already linked project
        return False

    if should_enforce_admin:
        return user_has_admin_access_in_all_domains(user, [upstream_domain_name, candidate_name])
    else:
        return True


def is_available_upstream_domain(potential_upstream_domain, downstream_domain, user, should_enforce_admin=True):
    """
    :param potential_upstream_domain: potential upstream domain
    :param downstream_domain: domain that would be downstream in this link if able
    :param user: couch user
    :param should_enforce_admin: enforce user is admin in both domains
    :return: True if the potential upstream domain is eligible to link to the specified downstream domain
    """
    from corehq.apps.linked_domain.dbaccessors import is_active_upstream_domain

    if not potential_upstream_domain or not downstream_domain:
        return False

    if potential_upstream_domain == downstream_domain:
        return False

    if not is_active_upstream_domain(potential_upstream_domain):
        # needs to be an active upstream domain
        return False

    if should_enforce_admin:
        return user_has_admin_access_in_all_domains(user, [downstream_domain, potential_upstream_domain])
    else:
        return True


def is_domain_in_active_link(domain_name):
    from corehq.apps.linked_domain.dbaccessors import (
        is_active_downstream_domain,
        is_active_upstream_domain,
    )
    return is_active_downstream_domain(domain_name) or is_active_upstream_domain(domain_name)


def user_has_admin_access_in_all_domains(user, domains):
    return all([user.is_domain_admin(domain) for domain in domains])


def is_keyword_linkable(keyword):
    from corehq.apps.sms.models import KeywordAction
    actions_with_group_recipients = keyword.keywordaction_set.filter(
        recipient=KeywordAction.RECIPIENT_USER_GROUP
    ).count()
    return actions_with_group_recipients == 0
