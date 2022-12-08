# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class View(models.Model):
    
    _inherit = "ir.ui.view"

    def get_inheriting_views_arch(self, view_id, model):
        self.env['ir.ui.menu'].clear_caches()
        res = super(View, self).get_inheriting_views_arch(view_id, model)
        self = self.with_context(l10n_br=self.env.company.country_id == self.env.ref('base.br'))
        if self.env.company.country_id != self.env.ref('base.br'):
            result = []
            for line in res:
                view_id = self.env['ir.ui.view'].browse(line[1])
                if not (view_id.model_data_id.module or "").startswith('l10n_br_ciel_it'):
                    result.append(line)
            res = result
        else:

            ir_config = self.sudo().env['ir.config_parameter']
            if not ir_config.get_param('l10n_br_ciel_it_account.modules_disable_view'):
                ir_config.sudo().set_param('l10n_br_ciel_it_account.modules_disable_view', "")
            modules_disable_view = ir_config.get_param('l10n_br_ciel_it_account.modules_disable_view') or ""

            result = []
            for line in res:
                view_id = self.env['ir.ui.view'].browse(line[1])
                if not (view_id.model_data_id.module or "") in modules_disable_view.split(","):
                    result.append(line)
            res = result

        return res
