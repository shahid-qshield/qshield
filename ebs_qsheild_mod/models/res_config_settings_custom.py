from odoo import fields, models, api, _


class ResConfigSettingCustom(models.TransientModel):
    _inherit = "res.config.settings"

    disable_future_date_service = fields.Boolean(
        string='Disable Future Date in Service Request',
        default=True,
        readonly=False,
        related='company_id.disable_future_date_service',
    )
