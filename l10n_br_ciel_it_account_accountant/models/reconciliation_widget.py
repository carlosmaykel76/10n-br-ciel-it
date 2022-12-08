# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)

class AccountReconciliation(models.AbstractModel):
    _inherit = 'account.reconciliation.widget'

    def _str_domain_for_mv_line(self, search_str):

        domain = super(AccountReconciliation, self)._str_domain_for_mv_line(search_str)
        if self.env.company.country_id != self.env.ref('base.br'):
            return domain

        if search_str:
            domain_str = [('move_id.l10n_br_numero_nf', 'ilike', search_str)]
            domain = expression.OR([ domain, domain_str ])
        
        return domain

