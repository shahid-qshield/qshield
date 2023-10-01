from odoo import models, fields, api, _
import base64
import csv
import xlrd
from odoo.exceptions import ValidationError

class ImportPricelist(models.TransientModel):
    _name = 'import.pricelist'

    attachment = fields.Binary(string="Upload file", required=True)
    file_name = fields.Char(string="Attachment Name")

    def action_submit(self):
        if self.file_name[-3:] in ['csv']:
            attachment_str = str(base64.b64decode(self.attachment), 'utf-8')
            file_lines = attachment_str.split('\n')
            data = csv.DictReader(file_lines)
        elif self.file_name[-3:] in ['xls'] or self.file_name[-4:] in ['xlsx']:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.attachment))
            worksheet = workbook.sheet_by_index(0)
            first_row = []  # The row where we stock the name of the column
            for col in range(worksheet.ncols):
                first_row.append(worksheet.cell_value(0, col))
            # transform the workbook to a list of dictionaries
            data = []
            for row in range(1, worksheet.nrows):
                elm = {}
                for col in range(worksheet.ncols):
                    elm[first_row[col]] = worksheet.cell_value(row, col)
                data.append(elm)
        successful_import = True

        for row in data:
            pricelist_name = row.get('Pricelist')
            # product_code = row.get('Internal Reference')
            product_name = row.get('Product')
            price = row.get('Price')
            if pricelist_name and product_name and price:
                if not isinstance(pricelist_name,str):
                    raise ValidationError(_("Price list column must be string"))
                if not isinstance(product_name,str):
                    raise ValidationError(_("Product column must be string"))
                if not isinstance(price,float) or not isinstance(price,int):
                    raise ValidationError(_("Price column must be Float or integer"))
                if isinstance(price,str):
                    price = float(price)
                product = self.env['product.product'].sudo().search([('name', '=', product_name)], limit=1)
                if not product:
                    successful_import = True
                    continue
                pricelist = self.env['product.pricelist'].sudo().search([('name', '=', pricelist_name)], limit=1)
                if not pricelist:
                    self.env['product.pricelist'].sudo().create({
                        'name': pricelist_name,
                        'item_ids': [(0, 0, {
                            'pricelist_id': pricelist.id,
                            'product_id': product.id,
                            'fixed_price': price,
                            'applied_on': "0_product_variant",
                            'compute_price': "fixed",
                        })]
                    })
                else:
                    pricelist_item = self.env['product.pricelist.item'].sudo().search([
                        ('pricelist_id', '=', pricelist.id),
                        ('product_id', '=', product.id)
                    ], limit=1)
                    pricelist_item.sudo().write({'fixed_price': price})
                    if not pricelist_item:
                        self.env['product.pricelist.item'].sudo().create({
                            'pricelist_id': pricelist.id,
                            'product_id': product.id,
                            'fixed_price': price,
                            'applied_on': "0_product_variant",
                            'compute_price': "fixed",
                        })
            else:
                successful_import = True
        if successful_import:
            message = "Import successful"
        else:
            message = "Import failed"
        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Import Status',
                'message': message,
                'sticky': False,
            },
        }


        return action
    
