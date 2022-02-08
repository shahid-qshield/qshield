from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('account_manager'):
            group = self.env.ref('ebs_qsheild_mod.qshield_account_manager')
            users = group.users
            args.append(('user_id', 'in', users.ids))
            res = super(HrEmployee, self)._search(args, offset, limit, order, count, access_rights_uid)
        else:
            res = super(HrEmployee, self)._search(args, offset, limit, order, count, access_rights_uid)

        return res
