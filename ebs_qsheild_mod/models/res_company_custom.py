from odoo import fields, models, api, _


class ResConfigSettingCustom(models.Model):
    _inherit = "res.company"

    disable_future_date_service = fields.Boolean(
        string='Disable Future Date in Service Request',
        Default=True,readonly=False

    )
