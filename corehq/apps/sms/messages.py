from django.utils.translation import gettext as _
from django.utils.translation import gettext_noop

from corehq.apps.translations.models import SMSTranslations
from corehq.util.translation import localize

MSG_MULTIPLE_SESSIONS = "sms.survey.restart"
MSG_TOUCHFORMS_DOWN = "sms.survey.temporarilydown"
MSG_TOUCHFORMS_ERROR = "sms.survey.internalerror"
MSG_CHOICE_OUT_OF_RANGE = "sms.validation.outofrange"
MSG_INVALID_CHOICE = "sms.validation.invalidchoice"
MSG_INVALID_INT = "sms.validation.invalidint"
MSG_INVALID_INT_RANGE = "sms.validation.invalidintrange"
MSG_INVALID_FLOAT = "sms.validation.invalidfloat"
MSG_INVALID_LONG = "sms.validation.invalidlong"
MSG_INVALID_DATE = "sms.validation.invaliddate"
MSG_INVALID_TIME = "sms.validation.invalidtime"
MSG_KEYWORD_NOT_FOUND = "sms.keyword.notfound"
MSG_START_KEYWORD_USAGE = "sms.keyword.startusage"
MSG_UNKNOWN_GLOBAL_KEYWORD = "sms.keyword.unknownglobal"
MSG_FIELD_REQUIRED = "sms.survey.fieldrequired"
MSG_EXPECTED_NAMED_ARGS_SEPARATOR = "sms.structured.missingseparator"
MSG_MULTIPLE_ANSWERS_FOUND = "sms.structured.multipleanswers"
MSG_MULTIPLE_QUESTIONS_MATCH = "sms.structured.ambiguousanswer"
MSG_MISSING_EXTERNAL_ID = "sms.caselookup.missingexternalid"
MSG_CASE_NOT_FOUND = "sms.caselookup.casenotfound"
MSG_MULTIPLE_CASES_FOUND = "sms.caselookup.multiplecasesfound"
MSG_FIELD_DESCRIPTOR = "sms.survey.fielddescriptor"
MSG_FORM_NOT_FOUND = "sms.survey.formnotfound"
MSG_FORM_ERROR = "sms.survey.formerror"
MSG_OPTED_IN = "sms.opt.in"
MSG_OPTED_OUT = "sms.opt.out"
MSG_DUPLICATE_USERNAME = "sms.validation.duplicateusername"
MSG_USERNAME_TOO_LONG = "sms.validation.usernametoolong"
MSG_VERIFICATION_START_WITH_REPLY = "sms.verify.startwithreplyto"
MSG_VERIFICATION_START_WITHOUT_REPLY = "sms.verify.startwithoutreplyto"
MSG_VERIFICATION_SUCCESSFUL = "sms.verify.successful"
MSG_REGISTRATION_WELCOME_CASE = "sms.registration.welcome.case"
MSG_REGISTRATION_WELCOME_MOBILE_WORKER = "sms.registration.welcome.mobileworker"

_MESSAGES = {
    MSG_MULTIPLE_SESSIONS: gettext_noop("An error has occurred. Please try restarting the survey."),
    MSG_TOUCHFORMS_DOWN: gettext_noop(
        "Our system is receiving a lot of messages now. "
        "Can you re-send in 15 minutes? Apologies for the inconvenience!"),
    MSG_TOUCHFORMS_ERROR: gettext_noop("Internal server error."),
    MSG_CHOICE_OUT_OF_RANGE: gettext_noop("Answer is out of range."),
    MSG_INVALID_CHOICE: gettext_noop("Invalid choice."),
    MSG_INVALID_INT: gettext_noop("Invalid integer entered."),
    MSG_INVALID_INT_RANGE:
        gettext_noop("Invalid integer entered, expected a number between -2147483648 and 2147483647."),
    MSG_INVALID_FLOAT: gettext_noop("Invalid decimal number entered."),
    MSG_INVALID_LONG: gettext_noop("Invalid long integer entered."),
    MSG_INVALID_DATE: gettext_noop("Invalid date format: expected {0}."),
    MSG_INVALID_TIME: gettext_noop("Invalid time format: expected HHMM (24-hour)."),
    MSG_KEYWORD_NOT_FOUND: gettext_noop("Keyword not found: '{0}'"),
    MSG_START_KEYWORD_USAGE: gettext_noop("Usage: {0} <keyword>"),
    MSG_UNKNOWN_GLOBAL_KEYWORD: gettext_noop("Unknown command: '{0}'"),
    MSG_FIELD_REQUIRED: gettext_noop("This field is required."),
    MSG_EXPECTED_NAMED_ARGS_SEPARATOR: gettext_noop("Expected name and value to be joined by '{0}'."),
    MSG_MULTIPLE_ANSWERS_FOUND: gettext_noop("More than one answer found for '{0}'"),
    MSG_MULTIPLE_QUESTIONS_MATCH: gettext_noop("More than one question matches '{0}'"),
    MSG_MISSING_EXTERNAL_ID: gettext_noop("Please provide an external id for the case."),
    MSG_CASE_NOT_FOUND: gettext_noop("Case with the given external id was not found."),
    MSG_MULTIPLE_CASES_FOUND: gettext_noop("More than one case was found with the given external id."),
    MSG_FIELD_DESCRIPTOR: gettext_noop("Field '{0}': "),
    MSG_FORM_NOT_FOUND: gettext_noop("Could not find the survey being requested."),
    MSG_FORM_ERROR: gettext_noop("There is a configuration error with this survey. "
        "Please contact your administrator."),
    MSG_OPTED_IN: gettext_noop("You have opted-in to receive messages from"
        " CommCareHQ. To opt-out, reply to this number with {0}"),
    MSG_OPTED_OUT: gettext_noop("You have opted-out from receiving"
        " messages from CommCareHQ. To opt-in, reply to this number with {0}"),
    MSG_DUPLICATE_USERNAME: gettext_noop("CommCare user {0} already exists"),
    MSG_USERNAME_TOO_LONG: gettext_noop("Username {0} is too long.  Must be under {1} characters."),
    MSG_VERIFICATION_START_WITH_REPLY: gettext_noop("Welcome to CommCareHQ! Is this phone used by {0}? "
        "If yes, reply '123' to {1} to start using SMS with CommCareHQ."),
    MSG_VERIFICATION_START_WITHOUT_REPLY: gettext_noop("Welcome to CommCareHQ! Is this phone used by {0}? "
        "If yes, reply '123' to start using SMS with CommCareHQ."),
    MSG_VERIFICATION_SUCCESSFUL: gettext_noop("Thank you. This phone has been verified for "
        "using SMS with CommCareHQ"),
    MSG_REGISTRATION_WELCOME_CASE: gettext_noop("Thank you for registering with CommCareHQ."),
    MSG_REGISTRATION_WELCOME_MOBILE_WORKER: gettext_noop("Thank you for registering with CommCareHQ."),
}


def get_message(msg_id, verified_number=None, context=None, domain=None, language=None):
    """
    Translates the message according to the user's and domain's preferences.

    msg_id - one of the MSG_* constants above
    verified_number - pass in the PhoneNumber of a contact in order to
                      use this contact's domain and language to translate
    context - some messages require additional parameters; pass them as a
              tuple or list
    domain - if the contact doesn't have a verified number, pass the domain
             in here to use this domain's translation doc
    language - if the contact doesn't have a verified number, pass the language
               code in here to use this language
    """
    default_msg = _MESSAGES.get(msg_id, "")

    if domain:
        translations = SMSTranslations.objects.filter(domain=domain).first()
    elif verified_number:
        translations = SMSTranslations.objects.filter(domain=verified_number.domain).first()
    else:
        translations = None

    if language:
        user_lang = language
    else:
        try:
            user_lang = verified_number.owner.get_language_code()
        except:
            user_lang = None

    def get_translation(lang):
        return translations.translations.get(lang, {}).get(msg_id, None)

    def domain_msg_user_lang():
        if translations and user_lang in translations.langs:
            return get_translation(user_lang)
        else:
            return None

    def domain_msg_domain_lang():
        if translations and translations.default_lang:
            return get_translation(translations.default_lang)
        else:
            return None

    def global_msg_user_lang():
        result = None
        if user_lang:
            with localize(user_lang):
                result = _(default_msg)
        return result if result != default_msg else None

    def global_msg_domain_lang():
        result = None
        if translations and translations.default_lang:
            with localize(translations.default_lang):
                result = _(default_msg)
        return result if result != default_msg else None

    msg = (
        domain_msg_user_lang() or
        domain_msg_domain_lang() or
        global_msg_user_lang() or
        global_msg_domain_lang() or
        default_msg
    )

    if context:
        msg = msg.format(*context)

    return msg
