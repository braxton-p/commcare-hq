from __future__ import absolute_import
from __future__ import unicode_literals
from django.test import TestCase

from corehq.apps.aggregate_ucrs.models import AggregateTableDefinition
from corehq.apps.aggregate_ucrs.tests.base import AggregationBaseTestMixin
from corehq.apps.aggregate_ucrs.importer import import_aggregation_models_from_spec
from corehq.apps.userreports.models import DataSourceConfiguration


class ConfigImportTest(TestCase, AggregationBaseTestMixin):

    def setUp(self):
        AggregateTableDefinition.objects.all().delete()

    def test_import_from_basic_definition(self):
        spec = self.get_config_spec()
        data_source = DataSourceConfiguration(
            domain=spec.domain,
            referenced_doc_type='CommCareCase',
            table_id='some_table',
        )
        data_source.save()
        self.addCleanup(data_source.delete)
        # these just have to be valid data source objects
        spec.primary_table.data_source_id = data_source._id
        spec.secondary_tables[0].data_source_id = data_source._id
        aggregate_table_definition = import_aggregation_models_from_spec(spec)
        self.assertEqual(1, AggregateTableDefinition.objects.count())
        table_def = AggregateTableDefinition.objects.get(pk=aggregate_table_definition.pk)
        self.assertEqual(data_source._id, table_def.primary_data_source_id.hex)
        self.assertEqual(4, table_def.primary_columns.count())
        self.assertEqual(1, table_def.secondary_tables.count())
        secondary_table = table_def.secondary_tables.get()
        self.assertEqual(data_source._id, secondary_table.data_source_id.hex)
        self.assertEqual('form.case.@case_id', secondary_table.data_source_key)
        self.assertEqual('received_on', secondary_table.aggregation_column)
        self.assertEqual(1, secondary_table.columns.count())
        secondary_column = secondary_table.columns.get()
        self.assertEqual('fu_forms_in_month', secondary_column.column_id)


