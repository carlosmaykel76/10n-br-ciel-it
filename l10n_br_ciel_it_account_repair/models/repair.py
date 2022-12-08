# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *

import logging
_logger = logging.getLogger(__name__)

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    invoice_ids = fields.Many2many("account.move", string='Invoices', readonly=True, copy=False)

    def action_repair_invoice_create(self):
        res = super(RepairOrder, self).action_repair_invoice_create()
        for repair in self:
            if repair.invoice_id:

                has_service = len(repair.invoice_id.invoice_line_ids.filtered(lambda l: l.product_id.type == 'service')) > 0
                has_material = len(repair.invoice_id.invoice_line_ids.filtered(lambda l: not l.product_id.type == 'service')) > 0
                if has_service and has_material:

                    service_invoice_id = repair.invoice_id.copy()
                    service_invoice_id.update({'l10n_br_tipo_pedido':'servico'})
                    service_invoice_id.with_context(check_move_validity=False).invoice_line_ids.filtered(lambda l: not l.product_id.type == 'service').unlink()
                    service_invoice_id.with_context(check_move_validity=False).invoice_line_ids._onchange_price_subtotal()
                    service_invoice_id.with_context(check_move_validity=False).line_ids._onchange_price_subtotal()
                    service_invoice_id.with_context(check_move_validity=False).onchange_l10n_br_calcular_imposto()

                    material_invoice_id = repair.invoice_id
                    material_invoice_id.update({'l10n_br_tipo_pedido':'venda'})
                    material_invoice_id.with_context(check_move_validity=False).invoice_line_ids.filtered(lambda l: l.product_id.type == 'service').unlink()
                    material_invoice_id.with_context(check_move_validity=False).invoice_line_ids._onchange_price_subtotal()
                    material_invoice_id.line_ids.with_context(check_move_validity=False)._onchange_price_subtotal()
                    material_invoice_id.with_context(check_move_validity=False).onchange_l10n_br_calcular_imposto()

                    repair.update({'invoice_ids': [(4, material_invoice_id.id)]})
                    repair.update({'invoice_ids': [(4, service_invoice_id.id)]})
                
                else:
                    
                    if has_service:
                        repair.invoice_id.update({'l10n_br_tipo_pedido':'servico'})
                    else:
                        repair.invoice_id.update({'l10n_br_tipo_pedido':'venda'})
                        
                    repair.invoice_id.with_context(check_move_validity=False).invoice_line_ids._onchange_price_subtotal()
                    repair.invoice_id.with_context(check_move_validity=False).line_ids._onchange_price_subtotal()
                    repair.invoice_id.with_context(check_move_validity=False).onchange_l10n_br_calcular_imposto()
                    repair.update({'invoice_ids': [(4, repair.invoice_id.id)]})

        return True

    def action_created_invoice(self):
        self.ensure_one()
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id

        return action
