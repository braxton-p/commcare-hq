from django.conf.urls import re_path as url

from .views import (
    DowngradeLocationsView,
    DownloadLocationStatusView,
    EditLocationView,
    FilteredLocationDownload,
    LocationFieldsView,
    LocationImportStatusView,
    LocationImportView,
    LocationsListView,
    LocationsSearchView,
    LocationTypesView,
    NewLocationView,
    archive_location,
    default,
    delete_location,
    location_descendants_count,
    location_download_job_poll,
    location_export,
    location_importer_job_poll,
    location_lineage,
    unarchive_location,
    unassign_users,
    count_locations,
)

settings_urls = [
    url(r'^$', default, name='default_locations_view'),
    url(r'^list/$', LocationsListView.as_view(), name=LocationsListView.urlname),
    url(r'^location_search/$', LocationsSearchView.as_view(), name='location_search'),
    url(r'^location_types/$', LocationTypesView.as_view(), name=LocationTypesView.urlname),
    url(r'^import/$', LocationImportView.as_view(), name=LocationImportView.urlname),
    url(r'^import_status/(?P<download_id>(?:dl-)?[0-9a-fA-Z]{25,32})/$', LocationImportStatusView.as_view(),
        name=LocationImportStatusView.urlname),
    url(r'^location_importer_job_poll/(?P<download_id>(?:dl-)?[0-9a-fA-Z]{25,32})/$',
        location_importer_job_poll, name='location_importer_job_poll'),
    url(r'^export_locations/$', location_export, name='location_export'),
    url(r'^export_status/(?P<download_id>(?:dl-)?[0-9a-fA-Z]{25,32})/$',
        DownloadLocationStatusView.as_view(), name=DownloadLocationStatusView.urlname),
    url(r'^export_job_poll/(?P<download_id>(?:dl-)?[0-9a-fA-Z]{25,32})/$',
        location_download_job_poll, name='org_download_job_poll'),
    url(r'^count_locations/$', count_locations, name='locations_count'),
    url(r'^filter_and_download/$', FilteredLocationDownload.as_view(),
        name=FilteredLocationDownload.urlname),
    url(r'^new/$', NewLocationView.as_view(), name=NewLocationView.urlname),
    url(r'^fields/$', LocationFieldsView.as_view(), name=LocationFieldsView.urlname),
    url(r'^downgrade/$', DowngradeLocationsView.as_view(),
        name=DowngradeLocationsView.urlname),
    url(r'^unassign_users/$', unassign_users, name='unassign_users'),
    url(r'^(?P<loc_id>[\w-]+)/archive/$', archive_location, name='archive_location'),
    url(r'^(?P<loc_id>[\w-]+)/unarchive/$', unarchive_location, name='unarchive_location'),
    url(r'^(?P<loc_id>[\w-]+)/delete/$', delete_location, name='delete_location'),
    url(r'^(?P<loc_id>[\w-]+)/lineage/$', location_lineage, name='location_lineage'),
    url(r'^(?P<loc_id>[\w-]+)/descendants/$', location_descendants_count, name='location_descendants_count'),
    url(r'^(?P<loc_id>[\w-]+)/$', EditLocationView.as_view(), name=EditLocationView.urlname),
]
