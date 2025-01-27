from jsonobject import DefaultProperty
from jsonobject.exceptions import BadValueError

from dimagi.ext.jsonobject import (
    BooleanProperty,
    DictProperty,
    JsonObject,
    ListProperty,
    StringProperty,
)

from corehq.apps.userreports.datatypes import DataTypeProperty
from corehq.apps.userreports.expressions.getters import (
    TransformedGetter,
    getter_from_property_reference,
    transform_for_datatype,
)
from corehq.apps.userreports.operators import equal, in_multiselect
from corehq.apps.userreports.specs import TypeProperty
from corehq.apps.userreports.transforms.factory import TransformFactory
from corehq.apps.userreports.util import add_tabbed_text


class IndicatorSpecBase(JsonObject):
    """
    Base class for indicator specs. All specs (for now) are assumed to have a column_id and
    a display_name, which defaults to the column_id.
    """
    _allow_dynamic_properties = False

    type = StringProperty(required=True)

    column_id = StringProperty(required=True)
    display_name = StringProperty()
    comment = StringProperty()

    @classmethod
    def wrap(cls, obj):
        wrapped = super(IndicatorSpecBase, cls).wrap(obj)
        if not wrapped.column_id:
            raise BadValueError('column_id must not be empty!')
        if not wrapped.display_name not in obj:
            wrapped.display_name = wrapped.column_id
        return wrapped

    def readable_output(self, context):
        return self.type


class PropertyReferenceIndicatorSpecBase(IndicatorSpecBase):
    """
    Extension of an indicator spec that references a property - either via
    a property_name or property_path.
    """
    property_name = StringProperty()
    property_path = ListProperty()

    @property
    def getter(self):
        return getter_from_property_reference(self)

    def readable_output(self, context):
        return self.property_name or "/".join(self.property_path)


class BooleanIndicatorSpec(IndicatorSpecBase):
    type = TypeProperty('boolean')
    filter = DictProperty(required=True)

    def readable_output(self, context):
        from corehq.apps.userreports.filters.factory import FilterFactory
        filter_object = FilterFactory.from_spec(self.filter, context)
        return str(filter_object)


class SmallBooleanIndicatorSpec(BooleanIndicatorSpec):
    type = TypeProperty('small_boolean')


class RawIndicatorSpec(PropertyReferenceIndicatorSpecBase):
    type = TypeProperty('raw')
    datatype = DataTypeProperty(required=True)
    is_nullable = BooleanProperty(default=True)
    is_primary_key = BooleanProperty(default=False)
    create_index = BooleanProperty(default=False)

    @property
    def getter(self):
        transform = transform_for_datatype(self.datatype)
        getter = getter_from_property_reference(self)
        return TransformedGetter(getter, transform)


class ExpressionIndicatorSpec(IndicatorSpecBase):
    type = TypeProperty('expression')
    datatype = DataTypeProperty(required=True)
    is_nullable = BooleanProperty(default=True)
    is_primary_key = BooleanProperty(default=False)
    create_index = BooleanProperty(default=False)
    expression = DefaultProperty(required=True)
    transform = DictProperty(required=False)

    def parsed_expression(self, context):
        from corehq.apps.userreports.expressions.factory import ExpressionFactory
        expression = ExpressionFactory.from_spec(self.expression, context)
        datatype_transform = transform_for_datatype(self.datatype)
        if self.transform:
            generic_transform = TransformFactory.get_transform(self.transform).get_transform_function()
            inner_getter = TransformedGetter(expression, generic_transform)
        else:
            inner_getter = expression
        return TransformedGetter(inner_getter, datatype_transform)

    def readable_output(self, context):
        from corehq.apps.userreports.expressions.factory import ExpressionFactory
        expression_object = ExpressionFactory.from_spec(self.expression, context)
        return str(expression_object)


class ChoiceListIndicatorSpec(PropertyReferenceIndicatorSpecBase):
    type = TypeProperty('choice_list')
    choices = ListProperty()
    select_style = StringProperty(choices=['single', 'multiple'])

    def get_operator(self):
        return in_multiselect if self.select_style == 'multiple' else equal

    def readable_output(self, context):
        readable_output = super(ChoiceListIndicatorSpec, self).readable_output(context)
        return "{} for choices:\n{}".format(readable_output,
                                            add_tabbed_text(str(self.choices)))


class LedgerBalancesIndicatorSpec(IndicatorSpecBase):
    type = TypeProperty('ledger_balances')
    product_codes = ListProperty(required=True)
    ledger_section = StringProperty(required=True)
    case_id_expression = DictProperty(required=True)

    def get_case_id_expression(self, context=None):
        from corehq.apps.userreports.expressions.factory import ExpressionFactory
        return ExpressionFactory.from_spec(self.case_id_expression, context)

    def readable_output(self, context):
        return "Ledgers from {}".format(str(self.get_case_id_expression(context)))


class DueListDateIndicatorSpec(LedgerBalancesIndicatorSpec):
    type = TypeProperty('due_list_date')

    def readable_output(self, context):
        return "Due List Dates from {}".format(str(self.get_case_id_expression(context)))
