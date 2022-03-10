from odoo import fields, models, api, _


class ResConfigSettingCustom(models.TransientModel):
    _inherit = "res.config.settings"

    disable_future_date_service = fields.Boolean(
        string='Disable Future Date in Service Request',
        default=True,
        readonly=False,
        related='company_id.disable_future_date_service',
    )
    is_send_service_notification = fields.Boolean(string="Send service status notification")
    send_notification_email = fields.Char(string="Send notification email")

    @api.model
    def get_values(self):
        res = super(ResConfigSettingCustom, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_send_service_notification=params.get_param('ebs_qsheild_mod.is_send_service_notification'),
            send_notification_email=params.get_param('ebs_qsheild_mod.send_notification_email')
        )
        return res

    def set_values(self):
        res = super(ResConfigSettingCustom, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ebs_qsheild_mod.is_send_service_notification',
                                                         self.is_send_service_notification)
        self.env['ir.config_parameter'].sudo().set_param('ebs_qsheild_mod.send_notification_email', self.send_notification_email)
        return res
