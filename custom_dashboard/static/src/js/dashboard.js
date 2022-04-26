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
        'click .request_progress_exceptional':'request_progress_exceptional',
        'click .request_new':'request_new',
        'click .request_out_of_scope':'request_out_of_scope',
        'click .request_escalated':'request_escalated',
        'click .request_overdue':'request_overdue',
        'click .request_pending':'request_pending',
        'click .get_employee_name':'get_employee_name',
        'click .get_employee_id':'get_employee_id',
        'click .get_date':'get_date',
        'click .get_date_for_drivers':'get_date_for_drivers',
        'click .request_pending_payment' :'get_pending_payment_request',
        'click .request_incomplete' :'request_incomplete',
        'click .request_escalated_completed' :'request_escalated_completed',
        'click .request_escalated_progress' :'request_escalated_progress',
        'click .request_escalated_incompleted' :'request_escalated_incompleted',
        'click .request_miscellaneous':'request_miscellaneous',
        'click .request_one_time_transaction':'request_one_time_transaction',

    },
    get_date:function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();

        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var myNode = document.getElementById("tasks");
         myNode.innerHTML = '';
        this.start_date = elem.value;
        console.log('start date',typeof(this.start_date));
        this.end_date = elem2.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        console.log('3333333333333333333333333-------',this.start_date,this.end_date);
        this.fetch_data(this.start_date,this.end_date,'');

    },

    get_date_for_drivers:function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('date_day');
        this.date_for_drivers = elem.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.fetch_data('','',this.date_for_drivers);
    },

    init: function(parent, context) {
        this._super(parent, context);
        this.draft = ''
        this.inProgress = ''
        this.onHold = ''
        this.rejected = ''
        this.cancelled = ''
        this.completed = ''
        this.dashboards_templates = ['service_request']
        },

    request_escalated_completed: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Escalated completed"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'escalated_complete'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_escalated_progress: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Escalated progress"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'escalated_progress'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_escalated_incompleted: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Escalated incomplete"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'escalated_incomplete'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_new: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("New"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'new'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_incomplete : function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Incomplete"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'incomplete'],['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

     request_escalated: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Escalated"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'escalated'],['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

     request_one_time_transaction: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Is One Time Transaction"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['date', '>=', date_form], ['date', '<=', date_to],['is_one_time_transaction','=',true]],
            target: 'current'
        }, options)
    },

     request_miscellaneous: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Is Miscellaneous"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['date', '>=', date_form], ['date', '<=', date_to],['is_miscellaneous','=',true]],
            target: 'current'
        }, options)
    },


    request_out_of_scope: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
//        var elem = document.getElementById('daydate');
//        var elem2 = document.getElementById('daydate2');
//        var date_form = elem.value;
//        var date_to = elem2.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Out Of Scope"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['date', '>=', date_form], ['date', '<=', date_to],['is_out_of_scope','=',true]],
            target: 'current'
        }, options)
    },

    get_pending_payment_request : function(e)
    {
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Pending payment"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status', '=', 'pending_payment'], ['date', '<=', date_to], ['date', '>=', date_form]],
            target: 'current'
        }, options)

    },

    request_pending: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Pending"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status', '=', 'pending'], ['date', '<=', date_to], ['date', '>=', date_form]],
            target: 'current'
        }, options)
    },

    request_overdue: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Overdue"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
//            domain: [['is_overdue','=', true],['is_escalated','=', false], ['is_pending', '=', false],
//             ['date', '>=', date_form], ['date', '<=', date_to]],
            domain: [['is_overdue','=', true], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },
     request_progress_exceptional: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Is Exceptional"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['is_exceptional','=',true], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_draft: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Draft"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'draft'],['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_progress: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("In Progress"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'progress'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_hold: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("On Hold"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'hold'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_complete: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Completed"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'complete'],['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_cancel: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Cancelled"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'cancel'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    request_reject: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value;
        var date_to = elem2.value;
        console.log(date_form)
        console.log(date_to)
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Rejected"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['status','=', 'reject'], ['date', '>=', date_form], ['date', '<=', date_to]],
            target: 'current'
        }, options)
    },

    get_employee_name: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var elem = document.getElementById('daydate');
        var elem2 = document.getElementById('daydate2');
        var date_form = elem.value + ' ' + '00:00:00';
        var date_to = elem2.value + ' ' + '00:00:00';
        console.log(date_form)
        console.log(date_to)
        var employee_id = parseInt(e.currentTarget.id)
        var employee_name = "" + e.currentTarget.getAttribute("emp_name")
//        console.log(e.currentTarget)
//        console.log(this.date_start)

        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("In Progress Tasks of "+employee_name),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request.workflow',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'progress'],['due_date', '>=', date_form], ['due_date', '<=', date_to], ['assign_to','=', employee_id]],
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

//            self.render_dashboards();
        });
    },

    get_emp_image_url: function(employee){
        return window.location.origin + '/web/image?model=res.users&field=image_1920&id='+employee;
    },

    fetch_data: function(start_date=false,end_date=false, date_for_drivers =false) {
        var self = this;
//        var year = today.getFullYear();
//        var month = today.getMonth();
//        var day = today.getDate();
//        var date_after_year = today.getFullYear()+1 +'-'+(today.getMonth()+1)+'-'+today.getDate();
        var today = new Date(new Date().getFullYear(), 11, 31);
        var date_today = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate();
        var now = new Date();
        var day = ("0" + now.getDate()).slice(-2);
        var month = ("0" + (now.getMonth() + 1)).slice(-2);
        self.current_date = now.getFullYear()+"-"+(month)+"-"+(day) ;
//        $('#date_day').value(self.current_date)
        if(typeof(self.end_date) != 'undefined')
        {
        console.log('----in ifff-----------------------',self.end_date);
        self.end_date_field = self.end_date;
        }
        else
        {
        console.log('----in else-------------------------');
        self.end_date_field = date_today

        }
        console.log('33333333333',self.current_date,self.end_date_field);
        var def0 =  self._rpc({
                    model: 'ebs_mod.service.request',
                    method: 'get_request',
                    args: [{
//                            'date_from': self.start_date ? self.start_date : date_today,
//                            'date_to': self.end_date ? self.end_date : date_after_year,
                            'date_from': self.start_date ? self.start_date : '2021-01-01',
                            'date_to': self.end_date ? self.end_date :self.end_date_field,
                    }]
            }).then(function(result) {
                self.progress =  result
                $(".draft").text(self.progress['draft']);
                $(".inprogress").text(self.progress['progress']);
                $(".pending").text(self.progress['pending']);
                $(".hold").text(self.progress['hold']);
                $(".cancel").text(self.progress['cancel']);
                $(".reject").text(self.progress['reject']);
                $(".complete").text(self.progress['complete']);
                $(".overdue").text(self.progress['overdue']);
                $(".new").text(self.progress['new']);
                $(".progress_out_of_scope").text(self.progress['progress_out_of_scope']);
                $(".progress_exceptional").text(self.progress['progress_exceptional']);
                $(".escalated").text(self.progress['escalated']);
                $(".escalated_completed").text(self.progress['escalated_complete']);
                $(".escalated_incomplete").text(self.progress['escalated_incomplete']);
                $(".escalated_in_progress").text(self.progress['escalated_progress']);
                $(".request_one_time_transaction").text(self.progress['request_one_time_transaction']);
                $(".request_miscellaneous").text(self.progress['request_miscellaneous']);
            });

        var def1 =  self._rpc({
                    model: 'ebs_mod.service.request.workflow',
                    method: 'get_request',
                    args: [{
                            'date_from': self.start_date ? self.start_date : '2021-01-01',
                            'date_to': self.end_date ? self.end_date :self.end_date_field,
                    }]
            }).then(function(result) {
                self.employee_progress =  result
                jQuery(document).ready(function(){
                    var taskDiv = document.getElementById("tasks")
                    var inner = ''
                    for (var i = 0; i < result.length; i++) {
                        inner += `<div class="card get_employee_name title${i} card_width_height" id= ${result[i]['employee_id']} emp_name=${result[i]['employee_name']}
                                         style="display:inline-block; margin:7px; padding: 5px; cursor: pointer; border-radius: 15px;">
                                        <div class="sub_card" style="display:inline-block;">
                                            <div class="user_image" style="display:inline-block;">
                                                <img class="img o_we_preview_image rounded-circle o_image_40_cover " src=${window.location.origin + '/web/image?model=res.users&field=image_1920&id='+result[i]['employee_id']}
                                                    style="height: 60px; width: 60px;"/>
                                            </div>
                                            <div class="user_progress" style="display:inline-block; margin-left:30px;">
                                               <p class="card-text assigned_inprogress" style="color:black; font-weight:bold;">${result[i]['progress']}</p>
                                            </div>

                                        </div>

                                      <div  style="text-transform: capitalize;">
                                        <p class="card-text" style="color:black; font-weight:bold;">${result[i]['employee_name']}</p>
                                      </div></div>`

//                       taskDiv.innerHTML += inner
                    }
                    try {
                          taskDiv.innerHTML = inner
                    }
                    catch(err) {
                      console.log(err)
                    }
                });
            });

        var def2 =  self._rpc({
                    model: 'ebs_mod.service.request.workflow',
                    method: 'get_driver',
                     args: [{
                            'date_day': self.date_for_drivers,
                    }]

            }).then(function(result) {
                self.drivers =  result
                console.log(result)
                jQuery(document).ready(function(){
                 var tbl = document.getElementById('data')
                 if (tbl != null)
                 {
                    $("#data").html("");
                     for (var i = 0; i < result.length; i++) {
//                    console.log(result[i]['driver_name'])
                    var tbl = document.getElementById('data')

                    var row = tbl.insertRow();
                    var cell1 = row.insertCell()
                    var cell2 = row.insertCell()
                    var cell3 = row.insertCell()
                    var cell4 = row.insertCell()
                    var cell5 = row.insertCell()
                    var cell6 = row.insertCell()
                    var cell7 = row.insertCell()
                    var cell8 = row.insertCell()
                    var cell9 = row.insertCell()
                    var cell10 = row.insertCell()
                    var cell11 = row.insertCell()
                    var cell12 = row.insertCell()
                    var cell13 = row.insertCell()
                    cell1.innerHTML = result[i]['driver_name'];

                    for (var j = 0; j < result[i]['destination'].length; j++){
//                        console.log(result[i]['destination'][j].slot)
                        if (result[i]['destination'][j].slot == '7')
                            cell2.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '8')
                            cell3.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '9')
                            cell4.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '10')
                            cell5.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '11')
                            cell6.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '12')
                            cell7.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '1')
                            cell8.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '2')
                            cell9.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '3')
                            cell10.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '4')
                            cell11.innerHTML = result[i]['destination'][j].destination
                        else if (result[i]['destination'][j].slot == '5')
                            cell12.innerHTML = result[i]['destination'][j].destination
                        else
                            cell13.innerHTML = result[i]['destination'][j].destination

//                        cell2.innerHTML = result[i]['destination'][j].slot == '7' ? result[i]['destination'][j].destination
//                        cell3.innerHTML = result[i]['destination'][j].slot == '8' ?  result[i]['destination'][j].destination
//                        cell4.innerHTML = result[i]['destination'][j].slot  == '9' ?  result[i]['destination'][j].destination
//                        cell5.innerHTML = result[i]['destination'][j].slot  == '10' ?  result[i]['destination'][j].destination
//                        cell6.innerHTML = result[i]['destination'][j].slot  == '11' ?  result[i]['destination'][j].destination
//                        cell7.innerHTML = result[i]['destination'][j].slot  == '12' ?  result[i]['destination'][j].destination
//                        cell8.innerHTML = result[i]['destination'][j].slot  == '1' ?  result[i]['destination'][j].destination
//                        cell9.innerHTML = result[i]['destination'][j].slot  == '2' ?  result[i]['destination'][j].destination
//                        cell10.innerHTML = result[i]['destination'][j].slot  == '3' ?  result[i]['destination'][j].destination
//                        cell11.innerHTML = result[i]['destination'][j].slot  == '4' ?  result[i]['destination'][j].destination
//                        cell12.innerHTML = result[i]['destination'][j].slot  == '5' ?  result[i]['destination'][j].destination
//                        cell13.innerHTML = result[i]['destination'][j].slot  == '6' ?  result[i]['destination'][j].destination
                            }
                        }
                 }
            });

        });
//                    var node = document.createElement("tr");                 // Create a <tr> node
//                    var textnode = document.createTextNode(result[i]['driver_name']);         // Create a text node
//                    node.appendChild(textnode);                              // Append the text to <tr>
//                    document.getElementById("data").appendChild(node);
//                    $("#data").append('<tr><td' + 'hello' + '</td></tr>');


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