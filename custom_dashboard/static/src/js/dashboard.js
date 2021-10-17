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

    events: {
        'click .request_draft':'request_draft',
        'click .request_progress':'request_progress',
        'click .request_hold':'request_hold',
        'click .request_complete':'request_complete',
        'click .request_cancel':'request_cancel',
        'click .request_reject':'request_reject',
        'click .get_employee_name':'get_employee_name',
        'click .get_employee_id':'get_employee_id',
    },

    request_draft: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Draft"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'draft']],
            target: 'current'
        }, options)
    },

    request_progress: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("In Progress"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'progress']],
            target: 'current'
        }, options)
    },

    request_hold: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("On Hold"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'hold']],
            target: 'current'
        }, options)
    },

    request_complete: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Completed"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'complete']],
            target: 'current'
        }, options)
    },

    request_cancel: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Cancelled"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'cancel']],
            target: 'current'
        }, options)
    },

    request_reject: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Rejected"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'reject']],
            target: 'current'
        }, options)
    },

    get_employee_name: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var employee_id = parseInt(e.currentTarget.id)
        var employee_name = "" + e.currentTarget.getAttribute("emp_name")
        console.log(e.currentTarget)


        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("In Progress Tasks of "+employee_name),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request.workflow',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'progress'],['assign_to','=', employee_id]],
//            domain: [['status','=', 'progress']],
            target: 'current'
        }, options)
    },

    on_reverse_breadcrumb: function() {console.log("ON_REVERSE_BREADCRUMB")
        var self = this;
        web_client.do_push_state({});
        this.fetch_data().then(function() {
            self.$('.o_hr_dashboard').empty();
            self.render_dashboards();
        });
    },

    willStart: function() {
        var self = this;
            return self.fetch_data();
    },

    start: function() {
        var self = this;
        this.set("title", 'Dashboard');
        return this._super().then(function() {
            self.render_dashboards();
        });
    },

    get_emp_image_url: function(employee){
        return window.location.origin + '/web/image?model=res.users&field=image_1920&id='+employee;
    },

    fetch_data: function() {
        var self = this;
        var def0 =  self._rpc({
                    model: 'ebs_mod.service.request',
                    method: 'get_request'
            }).then(function(result) {
                self.progress =  result
            });

        var def1 =  self._rpc({
                    model: 'ebs_mod.service.request.workflow',
                    method: 'get_request'
            }).then(function(result) {
                self.employee_progress =  result
            });
        var def2 =  self._rpc({
                    model: 'ebs_mod.service.request.workflow',
                    method: 'get_driver'
            }).then(function(result) {
                self.drivers =  result
            });
        var def3 =  self._rpc({
                    model: 'ebs_mod.service.type.consolidation',
                    method: 'get_request'
            }).then(function(result) {
                self.consolidation =  result
            });
        return $.when(def0,def1,def2,def3);
    },

    render_dashboards: function() {
        var self = this;
        _.each(this.dashboards_templates, function(template) {
            self.$('.o_hr_dashboard').append(QWeb.render(template, {widget: self}));
        });
    },

});


core.action_registry.add('service_request_dashboard', ServiceDashboard);

return ServiceDashboard;

});