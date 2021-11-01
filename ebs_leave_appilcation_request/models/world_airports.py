from odoo import models, fields, api


class WorldAirportsList(models.Model):
    _name = 'world.airports'
    _description = "World Airports List"
    _rec_name = 'airport'

    airport = fields.Char(string="City/Airport", default="", required=True)
    country = fields.Char(string="Country", default="", required=True)
    airport_code = fields.Char(string="IATA code", default="", required=True)

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s' % rec.airport))
        return res

    @api.model
    def _name_search(self, name='', args= None, operator='ilike', limit=100):
        if args is None:
            args = []
        domain = args + ['|', ('airport_code', operator, name), ('airport', operator, name)]
        return super(WorldAirportsList, self).search(domain, limit=limit).name_get()