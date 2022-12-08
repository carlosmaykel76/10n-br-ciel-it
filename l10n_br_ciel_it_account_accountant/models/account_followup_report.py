# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.tools.translate import _
from odoo.addons.l10n_br_ciel_it_account.models.account import *

import logging
_logger = logging.getLogger(__name__)

class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"

    def _get_columns_name(self, options):
        headers = super(AccountFollowupReport , self)._get_columns_name(options)
        if self.env.company.country_id != self.env.ref('base.br'):
            return headers
        headers = headers[:3] + headers[5:]  # Remove the 'Source Document' and 'Communication' columns
        headers[0] = {'name': _('Número NF'), 'style': 'text-align:left; white-space:nowrap;'}
        return headers

    def _get_lines(self, options, line_id=None):
        lines = super(AccountFollowupReport , self)._get_lines(options, line_id)
        if self.env.company.country_id != self.env.ref('base.br'):
            return lines
        lines_new = []
        for line in lines:
            if line.get('account_move'):

                move_display_name = ""
                if line.get('account_move').l10n_br_tipo_documento in ['55','57','NFSE'] and line.get('account_move').l10n_br_numero_nf > 0:
                    move_display_name = "%s: %s Série: %s" % (TIPO_NF_STR[line.get('account_move').l10n_br_tipo_documento],str(line.get('account_move').l10n_br_numero_nf),line.get('account_move').l10n_br_serie_nf or "")

                move_line = self.env['account.move.line'].browse(line.get('id'))
                if move_line and move_line.l10n_br_cobranca_parcela:
                    move_display_name += " - Parcela: %s" % move_line.l10n_br_cobranca_parcela

                line['name'] = move_display_name
            elif self.env.context.get('print_mode'):
                line['columns'][1] = line['columns'][3]
                                
            line['columns'] = line['columns'][:2] + line['columns'][4:]
                
            lines_new.append(line)
        
        return lines_new
