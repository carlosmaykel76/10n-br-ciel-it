# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval
import math

class AccountTaxFixed(models.Model):
    _inherit = "account.tax"

    amount_type = fields.Selection(selection_add=[('fixed_total', 'Fixo (Total)')])

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):

        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        self.ensure_one()

        if self.amount_type == 'fixed_total':
            if base_amount:
                return self.amount * (1.00 if base_amount >= 0.00 else -1.00)
            else:
                return self.amount * (1.00 if quantity >= 0.00 else -1.00)
        return super(AccountTaxFixed, self)._compute_amount(base_amount, price_unit, quantity, product, partner)
