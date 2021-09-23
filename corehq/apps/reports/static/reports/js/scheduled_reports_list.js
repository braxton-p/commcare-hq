/*

    ScheduledReportModel - model representing a single row on the list / a single report filter file
    ScheduleReportPanelModel - model representing a whole table ('My Scheduled Reports' and 'Other Scheduled Reports')
    ScheduledReportListModel - model representing the whole page (list of reports, actions)

*/

hqDefine("reports/js/scheduled_reports_list", [
    'jquery',
    'knockout',
    'underscore',
    'hqwebapp/js/components.ko', // pagination & feedback widget

], function (
    $,
    ko,
    _,
) {

    var scheduledReportModel = function (data, isOwner, isAdmin) {

        var self = ko.mapping.fromJS(data);

        self.configMany = ko.computed(function() {
            if (data.configs.length === 1){
                return false;
            };
            return true;
        });

        self.recipient_email_count = ko.computed(function() {
            return self.recipient_emails().length;
        });

        self.deleteScheduledReport = function(observable, event){
            $(event.currentTarget).closest('form').submit();
        };

        self.is_owner = isOwner;
        self.is_admin = isAdmin
        self.firstConfig = ko.observable(data.configs[0]);

        return self;
    };

    var scheduledReportsPanelModel = function (options) {
        var self = {};

        self.urls = options.urls

        self.scheduledReports = ko.observableArray();
        self.items = ko.observableArray();
        self.isLoadingPanel = ko.observable(true);
        self.perPage = ko.observable();
        self.header = options.header;
        self.is_owner = options.is_owner;
        self.is_admin = options.is_admin;

        self.scheduledReports(ko.utils.arrayMap(options.reports, function (report) {
            return scheduledReportModel(report, self.is_owner, self.is_admin);
        }));

        self.goToPage = function(page) {
            self.isLoadingPanel(true);
            self.items(self.scheduledReports.slice(self.perPage() * (page - 1), self.perPage() * page));
            self.isLoadingPanel(false);
            //self.getScheduledReportsPage(page);
        }

        /*
        //eventually should slice list on server side - does it matter performance-wise?
        self.getScheduledReportsPage = function (page) {
            //self.pageLoaded(false);
            $.ajax({
                method: 'GET',
                url: self.urls.getPage,
                data: {
                    'limit_request': true,
                    'couch_user': options.couch_user,
                    'page': page,
                    'limit': self.perPage(),
                    'myReports': self.is_owner,
                },
                success: function (data) {
                    //self.pageLoaded(true);
                    console.log("it's working?");
                    console.log(data.total);
                    //console.log(data.reports());
                },
                error: function () {
                    console.log("failed");
                },
            });
        }
        */

        self.selectAll = function () {
            _.each(self.items(), function (e) { e.addedToBulk(true); });
        };

        self.selectNone = function () {
            _.each(self.items(), function (e) { e.addedToBulk(false); });
        }

        self.totalItems = ko.observable(self.scheduledReports().length);

        self.onPaginationLoad = function () {
            self.goToPage(1);
        };

        return self;
    }

    var scheduledReportListModel = function (options) {

        var self = {};
        window.scrollTo(0, 0);

        self.urls = options.urls;

        self.bulkAction = ko.observable(false);
        self.isBulkDeleting = ko.observable(false);
        self.isBulkSending = ko.observable(false);

        self.panels = ko.observableArray([]);
        self.panels.push(scheduledReportsPanelModel({
            reports: options.scheduled_reports,
            is_owner: true,
            is_admin: options.is_admin,
            header: "My Scheduled Reports",
            urls: options.urls,
            couch_user: options.couch_user,
        }));
        self.panels.push(scheduledReportsPanelModel({
            reports: options.other_scheduled_reports,
            is_owner: false,
            is_admin: options.is_admin,
            header: "Other Scheduled Reports",
            urls: options.urls,
            couch_user: options.couch_user,
        }));

        self.reports = ko.computed(function () {
            return _.flatten(_.map(self.panels(), function (panel) { return panel.scheduledReports(); }));
        });

        self.selectedReports = ko.computed(function () {
            return _.filter(self.reports(), function (e) { return e.addedToBulk(); });
        });

        self.selectedReportsCount = ko.computed(function () {
            return self.selectedReports().length;
        });

        self.multiple = ko.computed(function () {
            if (self.selectedReportsCount() > 1) {
                return true;
            }
            return false;
        });

        self.bulkSend = function(){
            self.bulkAction(true);
            self.isBulkSending(true);
            sendList = _.filter(self.reports(), function (e) {return e.addedToBulk()});
            ids = []
            for (let i = 0; i < sendList.length; i++) {
                ids.push(sendList[i].id())
            }
            ids = JSON.stringify(ids);
            $.ajax ({
                method: 'POST',
                url: sendList[0].sendUrl(),
                data: {"sendList": ids,
                       "bulk_send_count": sendList.length},
                success: function (url) {
                    location.reload()
                }
            });
        }

        self.bulkDelete = function(){
            self.bulkAction(true);
            self.isBulkDeleting(true);
            deleteList = _.filter(self.reports(), function (e) {return e.addedToBulk()});
            ids = []
            for (let i = 0; i < deleteList.length; i++) {
                ids.push(deleteList[i].id())
            }
            ids = JSON.stringify(ids);
            $.ajax ({
                method: 'POST',
                url: deleteList[0].deleteUrl(),
                data: {"deleteList": ids,
                       "bulk_delete_count": deleteList.length},
                success: function () {
                    location.reload()
                }
            });
        }

        return self;
    };

    return {
        scheduledReportListModel: scheduledReportListModel,
    };

});

