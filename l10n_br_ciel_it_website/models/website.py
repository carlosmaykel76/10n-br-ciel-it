# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import logging
_logger = logging.getLogger(__name__)

class Website(models.Model):
    _inherit = 'website'
    
    def _prepare_sale_order_values(self, partner, pricelist):

        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)
        
        values['incoterm'] = 6
        
        return values