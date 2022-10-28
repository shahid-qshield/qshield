odoo.define('hide_archive_action.BasicView', function (require) {
"use strict";
var BasicView = require('web.BasicView');
BasicView.include({

        init: function(viewInfo, params) {
            var self = this;
            this._super.apply(this, arguments);
            const model =  ['ebs_mod.service.request'] ;
            if(model.includes(self.controllerParams.modelName))
            {
               self.controllerParams.archiveEnabled = 'False' in viewInfo.fields;
            }
        },
    });
});