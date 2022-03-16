from .query_functions import not_, selected_all, selected_any
from .subcase_functions import subcase
from .value_functions import date

# functions that transform a value
XPATH_VALUE_FUNCTIONS = {
    'date': date,
}


XPATH_QUERY_FUNCTIONS = {
    'not': not_,
    'subcase-exists': subcase,
    'subcase-count': subcase,
    'selected': selected_any,  # selected and selected_any function identically.
    'selected-any': selected_any,
    'selected-all': selected_all,
}
