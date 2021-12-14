# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ServiceRequestTypes(models.Model):
    _inherit = 'ebs_mod.service.types'

    product_id = fields.Many2one('product.product', string="Product")


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('is_service'):
            product_ids = self.env['ebs_mod.service.types'].search([]).mapped('product_id').ids
            if len(product_ids) > 0:
                args.append(('id', 'not in', product_ids))
        return super(ProductProduct, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
