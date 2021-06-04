from django.db.models.aggregates import Count
from corehq.apps.reports.generic import GenericTabularReport
from corehq.apps.enterprise.dispatcher import EnterpriseInterfaceDispatcher
from corehq.apps.reports.datatables import DataTablesColumn, DataTablesHeader
from corehq.apps.accounting.filters import DateCreatedFilter, NameFilter
from corehq.apps.sms.models import INCOMING, OUTGOING

from corehq.apps.smsbillables.filters import (
    DateSentFilter,
    GatewayTypeFilter,
    HasGatewayFeeFilter,
    ShowBillablesFilter,
)
from corehq.apps.enterprise.filters import EnterpriseDomainFilter
from corehq.apps.accounting.models import (
    BillingAccount,
    Subscription
)
from corehq.apps.smsbillables.models import (
    SmsBillable,
)

from couchexport.models import Format
from dimagi.utils.dates import DateSpan


class EnterpriseSMSBillablesInterface(GenericTabularReport):
    base_template = "accounting/report_filter_actions.html"
    section_name = "Enterprise"
    dispatcher = EnterpriseInterfaceDispatcher
    name = "SMS Detailed Report"
    description = """This is a report of SMS details that can be altered by using the filter options 
    above. Once you are happy with your filters, simply click Apply."""
    slug = "Enterprise"
    ajax_pagination = True
    exportable = True
    exportable_all = True
    export_format_override = Format.UNZIPPED_CSV
    fields = [
        'corehq.apps.smsbillables.interface.DateSentFilter',
        'corehq.apps.accounting.interface.DateCreatedFilter',
        'corehq.apps.smsbillables.interface.ShowBillablesFilter',
        'corehq.apps.enterprise.interface.EnterpriseDomainFilter',
        'corehq.apps.smsbillables.interface.HasGatewayFeeFilter',
        'corehq.apps.smsbillables.interface.GatewayTypeFilter',
    ]

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn("Date of Message"),
            DataTablesColumn("Project Space"),
            DataTablesColumn("Direction"),
            DataTablesColumn("SMS parts"),
            DataTablesColumn("Gateway", sortable=False),
            DataTablesColumn("Gateway Charge", sortable=False),
            DataTablesColumn("Usage Charge", sortable=False),
            DataTablesColumn("Total Charge", sortable=False),
            DataTablesColumn("Message Log ID", sortable=False),
            DataTablesColumn("Is Valid?", sortable=False),
            DataTablesColumn("Date Created"),
        )

    @property
    def sort_field(self):
        sort_fields = [
            'date_sent',
            'domain',
            'direction',
            'multipart_count',
            None,
            None,
            None,
            None,
            None,
            'date_created',
        ]
        sort_index = int(self.request.GET.get('iSortCol_0', 1))
        field = sort_fields[sort_index]
        sort_descending = self.request.GET.get('sSortDir_0', 'asc') == 'desc'
        return field if not sort_descending else '-{0}'.format(field)

    @property
    def shared_pagination_GET_params(self):
        return DateSentFilter.shared_pagination_GET_params(self.request) + \
            DateCreatedFilter.shared_pagination_GET_params(self.request) + [
                {
                    'name': DateCreatedFilter.optional_filter_slug(),
                    'value': DateCreatedFilter.optional_filter_string_value(self.request)
                },
                {
                    'name': ShowBillablesFilter.slug,
                    'value': ShowBillablesFilter.get_value(self.request, self.domain)
                },
                {
                    'name': NameFilter.slug,
                    'value': NameFilter.get_value(self.request, self.domain)
                },
                {
                    'name': EnterpriseDomainFilter.slug,
                    'value': EnterpriseDomainFilter.get_value(self.request, self.domain)
                },
                {
                    'name': HasGatewayFeeFilter.slug,
                    'value': HasGatewayFeeFilter.get_value(self.request, self.domain)
                },
                {
                    'name': GatewayTypeFilter.slug,
                    'value': GatewayTypeFilter.get_value(self.request, self.domain)
                },
        ]

    @property
    def get_all_rows(self):
        query = self.sms_billables
        query = query.order_by(self.sort_field)
        return self._format_billables(query)

    @property
    def total_records(self):
        query = self.sms_billables
        return query.aggregate(Count('id'))['id__count']

    @property
    def rows(self):
        query = self.sms_billables
        query = query.order_by(self.sort_field)

        sms_billables = query[self.pagination.start:(self.pagination.start + self.pagination.count)]
        return self._format_billables(sms_billables)

    def _format_billables(self, sms_billables):
        return [
            [
                sms_billable.date_sent,
                sms_billable.domain,
                {
                    INCOMING: "Incoming",
                    OUTGOING: "Outgoing",
                }.get(sms_billable.direction, ""),
                sms_billable.multipart_count,
                sms_billable.gateway_fee.criteria.backend_api_id if sms_billable.gateway_fee else "",
                sms_billable.gateway_charge,
                sms_billable.usage_charge,
                sms_billable.gateway_charge + sms_billable.usage_charge,
                sms_billable.log_id,
                sms_billable.is_valid,
                sms_billable.date_created,
            ]
            for sms_billable in sms_billables
        ]

    @property
    def sms_billables(self):
        datespan = DateSpan(DateSentFilter.get_start_date(self.request), DateSentFilter.get_end_date(self.request))
        selected_billables = SmsBillable.objects.filter(
            date_sent__gte=datespan.startdate,
            date_sent__lt=datespan.enddate_adjusted,
        )
        if DateCreatedFilter.use_filter(self.request):
            date_span = DateSpan(
                DateCreatedFilter.get_start_date(self.request), DateCreatedFilter.get_end_date(self.request)
            )
            selected_billables = selected_billables.filter(
                date_created__gte=date_span.startdate,
                date_created__lt=date_span.enddate_adjusted,
            )
        show_billables = ShowBillablesFilter.get_value(
            self.request, self.domain)
        if show_billables:
            selected_billables = selected_billables.filter(
                is_valid=(show_billables == ShowBillablesFilter.VALID),
            )
        account_name = NameFilter.get_value(self.request, self.domain)
        if account_name:
            account = BillingAccount.objects.filter(name=account_name).first()
            domains = Subscription.visible_objects.filter(
                account=account
            ).values_list('subscriber__domain', flat=True).distinct()
            domains = set(domains).union([account.created_by_domain])
            selected_billables = selected_billables.filter(
                domain__in=domains
            )
        domain = EnterpriseDomainFilter.get_value(self.request, self.domain)
        if domain:
            selected_billables = selected_billables.filter(
                domain=domain,
            )
        has_gateway_fee = HasGatewayFeeFilter.get_value(
            self.request, self.domain
        )
        if has_gateway_fee:
            if has_gateway_fee == HasGatewayFeeFilter.YES:
                selected_billables = selected_billables.exclude(
                    gateway_fee=None
                )
            else:
                selected_billables = selected_billables.filter(
                    gateway_fee=None
                )
        gateway_type = GatewayTypeFilter.get_value(self.request, self.domain)
        if gateway_type:
            selected_billables = selected_billables.filter(
                gateway_fee__criteria__backend_api_id=gateway_type,
            )
        return selected_billables
