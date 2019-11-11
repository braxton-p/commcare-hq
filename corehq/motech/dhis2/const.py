SEND_FREQUENCY_MONTHLY = 'monthly'
SEND_FREQUENCY_QUARTERLY = 'quarterly'

SEND_FREQUENCIES = [SEND_FREQUENCY_MONTHLY, SEND_FREQUENCY_QUARTERLY]

# A subset of DHIS2 data types. Omitted data types:
# * COORDINATE
# * EMAIL
# * FILE_RESOURCE
# * INTEGER_NEGATIVE
# * INTEGER_POSITIVE
# * INTEGER_ZERO_OR_POSITIVE
# * LETTER
# * LONG_TEXT
# * PERCENTAGE
# * PHONE_NUMBER
# * TRUE_ONLY
# * UNIT_INTERVAL
DHIS2_DATA_TYPE_BOOLEAN = "dhis2_boolean"
DHIS2_DATA_TYPE_DATE = "dhis2_date"
DHIS2_DATA_TYPE_DATETIME = "dhis2_datetime"
DHIS2_DATA_TYPE_INTEGER = "dhis2_integer"
DHIS2_DATA_TYPE_NUMBER = "dhis2_number"
DHIS2_DATA_TYPE_TEXT = "dhis2_text"

DHIS2_EVENT_STATUS_ACTIVE = "ACTIVE"
DHIS2_EVENT_STATUS_COMPLETED = "COMPLETED"
DHIS2_EVENT_STATUS_VISITED = "VISITED"
DHIS2_EVENT_STATUS_SCHEDULE = "SCHEDULE"
DHIS2_EVENT_STATUS_OVERDUE = "OVERDUE"
DHIS2_EVENT_STATUS_SKIPPED = "SKIPPED"

DHIS2_EVENT_STATUSES = (
    DHIS2_EVENT_STATUS_ACTIVE,
    DHIS2_EVENT_STATUS_COMPLETED,
    DHIS2_EVENT_STATUS_VISITED,
    DHIS2_EVENT_STATUS_SCHEDULE,
    DHIS2_EVENT_STATUS_OVERDUE,
    DHIS2_EVENT_STATUS_SKIPPED
)

LOCATION_DHIS_ID = 'dhis_id'
