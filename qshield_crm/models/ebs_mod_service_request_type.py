# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ServiceRequestTypes(models.Model):
    _inherit = 'ebs_mod.service.types'

    product_id = fields.Many2one('product.product', string="Product")
    product_price = fields.Monetary(currency_field='currency_id', string="Product Price")
    currency_id = fields.Many2one('res.currency', related='product_id.currency_id')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_price = self.product_id.lst_price

    @api.onchange('product_price')
    def onchange_product_price(self):
        self.product_id.write({'lst_price': self.product_price})


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('lst_price')
    def onchange_lst_price(self):
        if self.lst_price:
            service_type = self.env['ebs_mod.service.types'].search([('product_id', '=', self._origin.id)], limit=1)
            service_type.write({'product_price': self.lst_price})

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('is_service'):
            product_ids = self.env['ebs_mod.service.types'].search([]).mapped('product_id').ids
            if len(product_ids) > 0:
                args.append(('id', 'not in', product_ids))
        return super(ProductProduct, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                                   access_rights_uid=access_rights_uid)
