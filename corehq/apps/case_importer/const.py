# Each column results in 3 form fields so this must be true:
#   num_columns * 3 < DATA_UPLOAD_MAX_NUMBER_FIELDS
#
# DATA_UPLOAD_MAX_NUMBER_FIELDS defaults to 1000 but there are
# a few other fields as well. Also 300 is a nice round number.
MAX_CASE_IMPORTER_COLUMNS = 300


class LookupErrors(object):
    NotFound, MultipleResults = list(range(2))
