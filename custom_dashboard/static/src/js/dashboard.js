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
        'click .get_employee_name':'get_employee_name',
        'click .get_employee_id':'get_employee_id',
        'click .get_date':'get_date',
        'click .get_date_for_drivers':'get_date_for_drivers',
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
        this.end_date = elem2.value;
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
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
    },

    request_new: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("New"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['status','=', 'progress']],
            target: 'current'
        }, options)
    },

     request_escalated: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Escalated"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['is_escalated','=', true]],
            target: 'current'
        }, options)
    },

    request_overdue: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        this.do_action({
            name: _t("Overdue"),
            type: 'ir.actions.act_window',
            res_model: 'ebs_mod.service.request',
            view_mode: 'tree,form',
            views: [[false, 'list'],[false, 'form']],
            domain: [['is_overdue','=', true],['is_escalated','=', false]],
            target: 'current'
        }, options)
    },
     request_progress_exceptional: function(e){
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
            domain: [['status','=', 'progress'],['is_exceptional','=', true],['is_escalated','=', false]],
            target: 'current'
        }, options)
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
            domain: [['status','=', 'draft'], ['is_escalated','=', false]],
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
            domain: [['status','=', 'progress'],['is_exceptional','=', false],['is_escalated','=', false]],
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
            domain: [['status','=', 'hold'], ['is_escalated','=', false]],
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
            domain: [['status','=', 'complete'], ['is_escalated','=', false]],
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
            domain: [['status','=', 'cancel'],['is_escalated','=', false]],
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
            domain: [['status','=', 'reject'], ['is_escalated','=', false]],
            target: 'current'
        }, options)
    },

    get_employee_name: function(e){
        var self = this;
        e.stopPropagation();
        e.preventDefault();
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

    fetch_data: function(start_date='',end_date='', date_for_drivers ='') {
        var self = this;
        var def0 =  self._rpc({
                    model: 'ebs_mod.service.request',
                    method: 'get_request',
                    args: [{
                            'date_from': self.start_date,
                            'date_to': self.end_date,
                    }]
            }).then(function(result) {
                self.progress =  result
//                console.log(result)
                $(".draft").text(self.progress['draft']);
                $(".inprogress").text(self.progress['progress_normal']);
                $(".hold").text(self.progress['hold']);
                $(".cancel").text(self.progress['draft']);
                $(".reject").text(self.progress['reject']);
                $(".complete").text(self.progress['complete']);
                $(".overdue").text(self.progress['overdue']);
                $(".new").text(self.progress['new']);
                $(".progress_out_of_scope").text(self.progress['progress_out_of_scope']);
                $(".progress_exceptional").text(self.progress['progress_exceptional']);
                $(".escalated").text(self.progress['escalated']);
            });

        var def1 =  self._rpc({
                    model: 'ebs_mod.service.request.workflow',
                    method: 'get_request',
                    args: [{
                            'date_from': self.start_date,
                            'date_to': self.end_date,
                    }]
            }).then(function(result) {
                self.employee_progress =  result
                console.log(result)
                jQuery(document).ready(function(){
                    var taskDiv = document.getElementById("tasks")
                    var inner = ''
                    for (var i = 0; i < result.length; i++) {
                        inner += `<div class="card get_employee_name title${i} card_width_height" id= ${result[i]['employee_id']}
                                         style="display:inline-block; margin:7px; padding: 5px; cursor: pointer; border-radius: 15px;">
                                        <div class="sub_card" style="display:inline-block;">
                                            <div class="user_image" style="display:inline-block;">
                                                <img class="img o_we_preview_image rounded-circle o_image_40_cover " src=${window.location.origin + '/web/image?model=res.users&field=image_1920&id='+result[i]['employee_id']}
                                                    style="height: 60px; width: 60px;"/>
                                            </div>
                                            <div class="user_progress" style="display:inline-block; margin-left:30px;">
                                               <p class="card-text assigned_inprogress" style="color:white; font-weight:bold;">${result[i]['progress']}</p>
                                            </div>

                                        </div>

                                      <div  style="text-transform: capitalize;">
                                        <p class="card-text" style="color:white; font-weight:bold;">${result[i]['employee_name']}</p>
                                      </div></div>`

//                       taskDiv.innerHTML += inner
                    }
                    try {
                          taskDiv.innerHTML = inner
                          console.log(inner)
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
//                console.log(result)
                jQuery(document).ready(function(){
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