# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    l10n_br_partner_id = fields.Many2one('res.partner', string='Transportadora', ondelete='restrict', domain="[('company_type', '=', 'company')]")

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    location_id = fields.Many2one(states={'draft': [('readonly', False)], 'waiting': [('readonly', False)], 'confirmed': [('readonly', False)]})

    l10n_br_peso_liquido = fields.Float( string='Peso Liquido' )
    l10n_br_peso_bruto = fields.Float( string='Peso Bruto' )
    l10n_br_volumes = fields.Integer( string='Volumes', default=1 )
    l10n_br_especie = fields.Char( string='Espécie' )
    l10n_br_veiculo_placa = fields.Char( string='Placa' )
    l10n_br_veiculo_uf = fields.Char( string='UF' )
    l10n_br_veiculo_rntc = fields.Char( string='RNTC' )

    @api.model
    def create(self, vals):

        order_name = vals.get('origin')
        if order_name:
            order_id = self.env['sale.order'].search([('name','=',order_name)])
            if order_id:
                total_weight = 0.0
                for line in order_id.order_line.filtered(lambda l: not l.display_type):
                    if line.product_id and line.product_id.type != 'service':
                        total_weight += line.product_id.weight * line.product_uom_qty        
                vals['l10n_br_peso_liquido'] = total_weight
                vals['l10n_br_peso_bruto'] = total_weight
        res = super(StockPicking, self).create(vals)
        return res
