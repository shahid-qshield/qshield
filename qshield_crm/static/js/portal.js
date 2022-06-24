odoo.define('qshield_crm.portal', function (require) {
'use strict';

var core = require('web.core');
var Dialog = require('web.Dialog');
var _t = core._t;
var QWeb = core.qweb;
var ajax = require('web.ajax');
var rpc = require('web.rpc');
// var $modal = $(modal);
var count = 0 ;

$(document).ready(function(){
    $('.btn_approved').on('click', function()  {
            console.log('---------------------------',this)
//            ajax.jsonRpc("/check_user_emails/", 'call', {'user_emails_recs': user_emails_recs}).then(
//                function(data) {
//                    if(data != 'exist') {
//                        $(this).closest('form').submit();
//                    }
//                    else{
//                        Dialog.alert(self, _t("This email address is already registerd."), {
//                            title: _t('Email already exist'),
//                        });
//                        self.val('')
//                        return false
//                    }
//
//                });
            });


         $('.btn_rejected').on('click', function()  {
            console.log('---------------------------',this)
//            ajax.jsonRpc("/check_user_emails/", 'call', {'user_emails_recs': user_emails_recs}).then(
//                function(data) {
//                    if(data != 'exist') {
//                        $(this).closest('form').submit();
//                    }
//                    else{
//                        Dialog.alert(self, _t("This email address is already registerd."), {
//                            title: _t('Email already exist'),
//                        });
//                        self.val('')
//                        return false
//                    }
//
//                });
            });


  });
});
