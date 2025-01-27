import uuid

from django.test import TestCase
from django.utils.translation import gettext

from unittest.mock import patch

from corehq.apps.data_dictionary.models import CaseProperty, CaseType
from corehq.apps.data_dictionary.tests.utils import setup_data_dictionary
from corehq.apps.data_dictionary.util import generate_data_dictionary, get_values_hints_dict


@patch('corehq.apps.data_dictionary.util._get_all_case_properties')
class GenerateDictionaryTest(TestCase):
    domain = uuid.uuid4().hex

    def tearDown(self):
        CaseType.objects.filter(domain=self.domain).delete()

    def test_no_types(self, mock):
        mock.return_value = {}
        with self.assertNumQueries(1):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 0)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 0)

    def test_empty_type(self, mock):
        mock.return_value = {'': ['prop']}
        with self.assertNumQueries(2):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 0)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 0)

    def test_no_properties(self, mock):
        mock.return_value = {'type': []}
        with self.assertNumQueries(3):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 0)

    def test_one_type(self, mock):
        mock.return_value = {'type': ['property']}
        with self.assertNumQueries(4):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 1)

    def test_two_types(self, mock):
        mock.return_value = {'type': ['property'], 'type2': ['property']}
        with self.assertNumQueries(5):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 2)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 2)

    def test_two_properties(self, mock):
        mock.return_value = {'type': ['property', 'property2']}
        with self.assertNumQueries(4):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 2)

    def test_already_existing_property(self, mock):
        mock.return_value = {'type': ['property']}
        case_type = CaseType(domain=self.domain, name='type')
        case_type.save()
        CaseProperty(case_type=case_type, name='property').save()

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 1)

        with self.assertNumQueries(3):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 1)

    def test_parent_property(self, mock):
        mock.return_value = {'type': ['property', 'parent/property']}
        with self.assertNumQueries(4):
            generate_data_dictionary(self.domain)

        self.assertEqual(CaseType.objects.filter(domain=self.domain).count(), 1)
        self.assertEqual(CaseProperty.objects.filter(case_type__domain=self.domain).count(), 1)


class MiscUtilTest(TestCase):
    domain = uuid.uuid4().hex

    def tearDown(self):
        CaseType.objects.filter(domain=self.domain).delete()

    def test_no_data_dict_info(self):
        case_type_name = 'bare'
        setup_data_dictionary(self.domain, case_type_name)
        self.assertEqual({}, get_values_hints_dict(self.domain, case_type_name))

    def test_date_hint(self):
        case_type_name = 'case1'
        date_prop_name = 'intake_date'
        setup_data_dictionary(self.domain, case_type_name, [(date_prop_name, 'date')])
        values_hints = get_values_hints_dict(self.domain, case_type_name)
        self.assertEqual(len(values_hints), 1)
        self.assertTrue(date_prop_name in values_hints)
        self.assertEqual(values_hints[date_prop_name], [gettext('YYYY-MM-DD')])

    def test_select_hints(self):
        case_type_name = 'case1'
        select_prop1 = 'status'
        select_prop2 = 'active'
        av_dict = {
            select_prop1: ['foster', 'pending', 'adopted'],
            select_prop2: ['true', 'false'],
        }
        prop_list = [(prop, 'select') for prop in [select_prop1, select_prop2]]
        setup_data_dictionary(self.domain, case_type_name, prop_list, av_dict)
        values_hints = get_values_hints_dict(self.domain, case_type_name)
        self.assertEqual(len(values_hints), 2)
        for prop_name, _ in prop_list:
            self.assertTrue(prop_name in values_hints)
            self.assertEqual(sorted(values_hints[prop_name]), sorted(av_dict[prop_name]))
