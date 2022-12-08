# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

MODALIDADE_FRETE = [
    ('0', 'CIF'),
    ('1', 'FOB'),
    ('2', 'Contratação do Frete por Conta de Terceiros'),
    ('3', 'Transporte Próprio por Conta do Remetente'),
    ('4', 'Transporte Próprio por Conta do Destinatário'),
    ('9', 'Sem ocorrência de transporte'),
]

class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    l10n_br_modalidade_frete = fields.Selection( MODALIDADE_FRETE, string='Modalidade do Frete' )
