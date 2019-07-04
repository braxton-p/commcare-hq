from __future__ import absolute_import
from __future__ import unicode_literals

import json

from django.test import TestCase
from django.urls import reverse

from corehq.apps.api.odata.tests.utils import (
    OdataTestMixin,
    ensure_es_case_index_deleted,
    ensure_es_form_index_deleted,
    generate_api_key_from_web_user,
    setup_es_case_index,
    setup_es_form_index,
)
from corehq.apps.api.resources.v0_5 import (
    ODataCaseFromExportInstanceResource,
    ODataCommCareCaseResource,
    ODataXFormInstanceResource,
)
from corehq.apps.domain.models import Domain
from corehq.apps.export.models import CaseExportInstance, TableConfiguration
from corehq.util.test_utils import flag_enabled


class TestCaseOdataFeed(TestCase, OdataTestMixin):

    # flag_enabled is used in the test function body because class-level flags in child classes
    # cancel out class level decorators or decorators on non-overriden functions.

    @classmethod
    def setUpClass(cls):
        super(TestCaseOdataFeed, cls).setUpClass()
        cls._set_up_class()
        cls._setup_accounting()
        setup_es_case_index()

    @classmethod
    def tearDownClass(cls):
        ensure_es_case_index_deleted()
        cls._teardownclass()
        cls._teardown_accounting()
        super(TestCaseOdataFeed, cls).tearDownClass()

    def test_no_credentials(self):
        with flag_enabled('ODATA'):
            response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 401)

    def test_wrong_password(self):
        wrong_credentials = self._get_basic_credentials(self.web_user.username, 'wrong_password')
        with flag_enabled('ODATA'):
            response = self._execute_query(wrong_credentials)
        self.assertEqual(response.status_code, 401)

    def test_wrong_domain(self):
        other_domain = Domain(name='other_domain')
        other_domain.save()
        self.addCleanup(other_domain.delete)

        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self.client.get(
                self._odata_feed_url_by_domain(other_domain.name),
                HTTP_AUTHORIZATION='Basic ' + correct_credentials,
            )
        self.assertEqual(response.status_code, 401)

    def test_missing_feature_flag(self):
        correct_credentials = self._get_correct_credentials()
        response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 404)

    def test_request_succeeded(self):
        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 200)

    @property
    def view_url(self):
        return self._odata_feed_url_by_domain(self.domain.name)

    @staticmethod
    def _odata_feed_url_by_domain(domain_name):
        return reverse(
            'api_dispatch_detail',
            kwargs={
                'domain': domain_name,
                'api_name': 'v0.5',
                'resource_name': ODataCommCareCaseResource._meta.resource_name,
                'pk': 'my_case_type',
            }
        )


class TestCaseOdataFeedUsingApiKey(TestCaseOdataFeed):

    @classmethod
    def setUpClass(cls):
        super(TestCaseOdataFeedUsingApiKey, cls).setUpClass()
        cls.api_key = generate_api_key_from_web_user(cls.web_user)

    @classmethod
    def _get_correct_credentials(cls):
        return TestCaseOdataFeedUsingApiKey._get_basic_credentials(cls.web_user.username, cls.api_key.key)


@flag_enabled('TWO_FACTOR_SUPERUSER_ROLLOUT')
class TestCaseOdataFeedWithTwoFactorUsingApiKey(TestCaseOdataFeedUsingApiKey):
    pass


class TestFormOdataFeed(TestCase, OdataTestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestFormOdataFeed, cls).setUpClass()
        cls._set_up_class()
        cls._setup_accounting()
        setup_es_form_index()

    @classmethod
    def tearDownClass(cls):
        ensure_es_form_index_deleted()
        cls._teardownclass()
        cls._teardown_accounting()
        super(TestFormOdataFeed, cls).tearDownClass()

    def test_no_credentials(self):
        with flag_enabled('ODATA'):
            response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 401)

    def test_wrong_password(self):
        wrong_credentials = self._get_basic_credentials(self.web_user.username, 'wrong_password')
        with flag_enabled('ODATA'):
            response = self._execute_query(wrong_credentials)
        self.assertEqual(response.status_code, 401)

    def test_wrong_domain(self):
        other_domain = Domain(name='other_domain')
        other_domain.save()
        self.addCleanup(other_domain.delete)

        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self.client.get(
                self._odata_feed_url_by_domain(other_domain.name),
                HTTP_AUTHORIZATION='Basic ' + correct_credentials,
            )
        self.assertEqual(response.status_code, 401)

    def test_missing_feature_flag(self):
        correct_credentials = self._get_correct_credentials()
        response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 404)

    def test_request_succeeded(self):
        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                '@odata.context': 'http://localhost:8000/a/test_domain/api/v0.5/odata/Forms/my_app_id/$metadata#my_xmlns',
                'value': []
            }
        )

    @property
    def view_url(self):
        return self._odata_feed_url_by_domain(self.domain.name)

    @staticmethod
    def _odata_feed_url_by_domain(domain_name):
        return reverse(
            'api_dispatch_detail',
            kwargs={
                'domain': domain_name,
                'api_name': 'v0.5',
                'resource_name': ODataXFormInstanceResource._meta.resource_name,
                'pk': 'my_app_id/my_xmlns',
            }
        )


class TestFormOdataFeedUsingApiKey(TestFormOdataFeed):

    @classmethod
    def setUpClass(cls):
        super(TestFormOdataFeedUsingApiKey, cls).setUpClass()
        cls.api_key = generate_api_key_from_web_user(cls.web_user)

    @classmethod
    def _get_correct_credentials(cls):
        return TestFormOdataFeedUsingApiKey._get_basic_credentials(cls.web_user.username, cls.api_key.key)


@flag_enabled('TWO_FACTOR_SUPERUSER_ROLLOUT')
class TestFormOdataFeedWithTwoFactorUsingApiKey(TestFormOdataFeedUsingApiKey):
    pass


class TestCaseOdataFeedFromExportInstance(TestCase, OdataTestMixin):

    @classmethod
    def setUpClass(cls):
        super(TestCaseOdataFeedFromExportInstance, cls).setUpClass()
        cls._set_up_class()
        cls._setup_accounting()
        setup_es_case_index()

    @classmethod
    def tearDownClass(cls):
        ensure_es_case_index_deleted()
        cls._teardownclass()
        cls._teardown_accounting()
        super(TestCaseOdataFeedFromExportInstance, cls).tearDownClass()

    def test_no_credentials(self):
        with flag_enabled('ODATA'):
            response = self.client.get(self.view_url)
        self.assertEqual(response.status_code, 401)

    def test_wrong_password(self):
        wrong_credentials = self._get_basic_credentials(self.web_user.username, 'wrong_password')
        with flag_enabled('ODATA'):
            response = self._execute_query(wrong_credentials)
        self.assertEqual(response.status_code, 401)

    def test_wrong_domain(self):
        other_domain = Domain(name='other_domain')
        other_domain.save()
        self.addCleanup(other_domain.delete)

        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self.client.get(
                self._odata_feed_url_by_domain(other_domain.name),
                HTTP_AUTHORIZATION='Basic ' + correct_credentials,
            )
        self.assertEqual(response.status_code, 401)

    def test_config_in_different_domain(self):
        export_config = CaseExportInstance(
            _id='config_id',
            tables=[TableConfiguration(columns=[])],
            case_type='my_case_type',
            domain='different_domain'
        )
        export_config.save()
        self.addCleanup(export_config.delete)

        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 404)

    def test_missing_feature_flag(self):
        correct_credentials = self._get_correct_credentials()
        response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 404)

    def test_request_succeeded(self):
        export_config = CaseExportInstance(
            _id='config_id',
            tables=[TableConfiguration(columns=[])],
            case_type='my_case_type',
            domain=self.domain.name,
        )
        export_config.save()
        self.addCleanup(export_config.delete)

        correct_credentials = self._get_correct_credentials()
        with flag_enabled('ODATA'):
            response = self._execute_query(correct_credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertEqual(response['OData-Version'], '4.0')
        self.assertEqual(
            json.loads(response.content.decode('utf-8')),
            {
                '@odata.context': 'http://localhost:8000/a/test_domain/api/v0.5/odata/cases/$metadata#config_id',
                'value': []
            }
        )

    @property
    def view_url(self):
        return self._odata_feed_url_by_domain(self.domain.name)

    @staticmethod
    def _odata_feed_url_by_domain(domain_name):
        return reverse(
            'api_dispatch_detail',
            kwargs={
                'domain': domain_name,
                'api_name': 'v0.5',
                'resource_name': ODataCaseFromExportInstanceResource._meta.resource_name,
                'pk': 'config_id',
            }
        )


class TestCaseOdataFeedFromExportInstanceUsingApiKey(TestCaseOdataFeedFromExportInstance):

    @classmethod
    def setUpClass(cls):
        super(TestCaseOdataFeedFromExportInstanceUsingApiKey, cls).setUpClass()
        cls.api_key = generate_api_key_from_web_user(cls.web_user)

    @classmethod
    def _get_correct_credentials(cls):
        return TestFormOdataFeedUsingApiKey._get_basic_credentials(cls.web_user.username, cls.api_key.key)


@flag_enabled('TWO_FACTOR_SUPERUSER_ROLLOUT')
class TestCaseOdataFeedFromExportInstanceWithTwoFactorUsingApiKey(TestCaseOdataFeedFromExportInstanceUsingApiKey):
    pass
