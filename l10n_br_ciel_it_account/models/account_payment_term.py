# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)

INDICADOR_PAGAMENTO = [
    ('0', 'Pagamento à Vista'),
    ('1', 'Pagamento à Prazo'),
]

MEIO_PAGAMENTO = [
    ('01', 'Dinheiro'),
    ('02', 'Cheque'),
    ('03', 'Cartão de Crédito'),
    ('04', 'Cartão de Débito'),
    ('05', 'Crédito Loja'),
    ('10', 'Vale Alimentação'),
    ('11', 'Vale Refeição'),
    ('12', 'Vale Presente'),
    ('13', 'Vale Combustível'),
    ('14', 'Duplicata Mercantil'),
    ('15', 'Boleto Bancário'),
    ('90', 'Sem pagamento'),
    ('99', 'Outros'),
]

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    l10n_br_indicador = fields.Selection( INDICADOR_PAGAMENTO, string='Indicador do Pagamento' )
    l10n_br_meio = fields.Selection( MEIO_PAGAMENTO, string='Meio de Pagamento' )
    l10n_br_cobranca_id = fields.Many2one( 'l10n_br_ciel_it_account.tipo.cobranca', string='Tipo de Cobrança' )
    is_sales = fields.Boolean( string='Ativo p/ Vendas', default=True )
    is_purchase = fields.Boolean( string='Ativo p/ Compras', default=True )
    is_advpay = fields.Boolean( string='Pagamento Antecipado', default=False )

class PaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    l10n_br_meio = fields.Selection( MEIO_PAGAMENTO, string='Meio de Pagamento' )
    l10n_br_cobranca_id = fields.Many2one( 'l10n_br_ciel_it_account.tipo.cobranca', string='Tipo de Cobrança' )
