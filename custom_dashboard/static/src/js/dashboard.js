odoo.define('custom_dashboard.Dashboard', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var ServiceDashboard = AbstractAction.extend({
    template: 'service_request',

//    init: function(parent, context) {
//        this._super(parent, context);
//        this.dashboards_templates = ['LoginEmployeeDetails'];
//        this.announcements = [];
//    },
//
//    start: function() {
//        var self = this;
//        this.set("title", 'Dashboard');
//        return this._super().then(function() {
//            self.render_dashboards();
//        });
//    },
//
//    render_dashboards: function() {
//        var self = this;
//            _.each(templates, function(template) {
//                self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
//            });
//        }
//    },
});


core.action_registry.add('service_request_dashboard', ServiceDashboard);

return ServiceDashboard;

});