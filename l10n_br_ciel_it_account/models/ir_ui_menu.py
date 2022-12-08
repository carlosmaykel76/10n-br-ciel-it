# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _, http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)

class IrUiMenu(models.Model):

    _inherit = 'ir.ui.menu'

    def _visible_menu_ids(self, debug=False):
        res = super(IrUiMenu, self)._visible_menu_ids(debug=debug)

        all_menu_items = self.env['ir.model.data'].sudo().search([('model', '=', 'ir.ui.menu')])
        if self.env.ref('l10n_br_ciel_it_account.group_l10n_br_menu_hide') in self.env.user.groups_id:
            l10n_br_menu_items = all_menu_items.filtered(lambda m: (m.module or "").startswith('l10n_br_ciel_it'))
            l10n_br_menu_items = set(l10n_br_menu_items.mapped('res_id'))
            res = res - l10n_br_menu_items

        if not self.env.ref('l10n_br_ciel_it_account.group_l10n_xx_menu_hide') in self.env.user.groups_id:
            ir_config = self.sudo().env['ir.config_parameter']
            if not ir_config.get_param('l10n_br_ciel_it_account.modules_disable_view'):
                ir_config.sudo().set_param('l10n_br_ciel_it_account.modules_disable_view', "")
            modules_disable_view = ir_config.get_param('l10n_br_ciel_it_account.modules_disable_view') or ""
            l10n_xx_menu_items = all_menu_items.filtered(lambda m: (m.module or "") in modules_disable_view.split(","))
            l10n_xx_menu_items = set(l10n_xx_menu_items.mapped('res_id'))
            res = res - l10n_xx_menu_items

        return res
