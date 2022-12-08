# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import uuid
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *
from odoo.addons.l10n_br_ciel_it_account.models.account_payment_term import *

import logging
_logger = logging.getLogger(__name__)

TIPO_PEDIDO_ENTRADA = [
    ('compra','Entrada: Compra'),
    ('importacao','Entrada: Importação'),
    ('servico','Entrada: Serviço'),
    ('retorno','Entrada: Outros Retorno'),
    ('demonstracao','Entrada: Retorno de Demonstração'),
    ('feira','Entrada: Retorno de Feira'),
    ('consignacao','Entrada: Retorno de Consignação'),
    ('locacao','Entrada: Locação'),
    ('ret-locacao','Entrada: Retorno de Locação'),
    ('comodato','Entrada: Retorno de Comodato'),
    ('industrializacao','Entrada: Retorno de Industrialização'),
    ('ent-conserto','Entrada: Conserto'),
    ('ent-demonstracao','Entrada: Demonstração'),
    ('ent-bonificacao','Entrada: Bonificação'),
    ('ent-amostra','Entrada: Amostra Grátis'),
    ('ent-comodato','Entrada: Comodato'),
    ('deposito','Entrada: Retorno de Depósito'),
    ('conserto','Entrada: Retorno de Conserto'),
    ('troca','Entrada: Retorno de Troca'),
    ('devolucao','Entrada: Devolução Emissão Própria'),
    ('devolucao_compra','Entrada: Devolução de Compra'),
    ('outro','Entrada: Outros'),
]

TIPO_PEDIDO_ENTRADA_NO_PAYMENT = [
    'retorno',
    'demonstracao',
    'feira',
    'consignacao',
    'comodato',
    'industrializacao',
    'ent-conserto',
    'ent-demonstracao',
    'ret-locacao',
    'conserto',
    'outro',
]

TIPO_PEDIDO_ENTRADA_DEVOLUCAO = [
    'devolucao',
    'devolucao_compra',
]

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    dfe_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe', string='Documento', check_company=True )
    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', compute="_get_l10n_br_operacao_id", check_company=True )
    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_ENTRADA, string='Tipo de Pedido', default='compra', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    payment_term_id = fields.Many2one( readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    payment_acquirer_id = fields.Many2one( 'payment.acquirer', string='Forma de Pagamento', readonly=True, states={'draft': [('readonly', False)]}, domain=[('state', '=', 'enabled')] )
    incoterm_id = fields.Many2one( string='Tipo de Frete', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )

    l10n_br_informacao_fiscal = fields.Text( string='Informação Fiscal', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_informacao_complementar = fields.Text( string='Informação Complementar', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )

    l10n_br_imposto_auto = fields.Boolean( string='Calcular Impostos Automaticamente', default=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_calcular_imposto = fields.Boolean( string='Calcular Impostos', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )

    l10n_br_icms_base = fields.Float( string='Total da Base de Cálculo do ICMS', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_icms_valor = fields.Float( string='Total do ICMS', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icms_valor_isento = fields.Float( string='Total do ICMS (Isento/Não Tributável)', readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icms_valor_outros = fields.Float( string='Total do ICMS (Outros)', readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icms_valor_desonerado = fields.Float( string='Total do ICMS (Desonerado)', readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    
    l10n_br_icmsst_base = fields.Float( string='Total da Base de Cálculo do ICMSST', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icmsst_valor = fields.Float( string='Total do ICMSST', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icmsst_valor_outros = fields.Float( string='Total do ICMSST (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_icmsst_substituto_valor = fields.Float( string='Total do ICMSST Substituto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icmsst_substituto_valor_outros = fields.Float( string='Total do ICMSST Substituto (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icmsst_retido_valor = fields.Float( string='Total do ICMSST Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icmsst_retido_valor_outros = fields.Float( string='Total do ICMSST Retido (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_icms_dest_valor = fields.Float( string='Total do ICMS UF Destino', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_icms_remet_valor = fields.Float( string='Total do ICMS UF Remetente', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_fcp_dest_valor = fields.Float( string='Total do Fundo de Combate a Pobreza', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_fcp_st_valor = fields.Float( string='Total do Fundo de Combate a Pobreza Retido por ST', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_fcp_st_ant_valor = fields.Float( string='Total do Fundo de Combate a Pobreza Retido Anteriormente por ST', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_prod_valor = fields.Float( string='Total dos Produtos', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_frete = fields.Float( string='Total do Frete', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_seguro = fields.Float( string='Total do Seguro', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_despesas_acessorias = fields.Float( string='Total da Despesas Acessórias', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_desc_valor = fields.Float( string='Total do Desconto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_ipi_valor = fields.Float( string='Total do IPI', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_ipi_valor_isento = fields.Float( string='Total do IPI (Isento/Não Tributável)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_ipi_valor_outros = fields.Float( string='Total do IPI (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_pis_valor = fields.Float( string='Total do PIS', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_pis_valor_isento = fields.Float( string='Total do PIS (Isento/Não Tributável)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_pis_valor_outros = fields.Float( string='Total do PIS (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_cofins_valor = fields.Float( string='Total do Cofins', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_cofins_valor_isento = fields.Float( string='Total do Cofins (Isento/Não Tributável)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_cofins_valor_outros = fields.Float( string='Total do Cofins (Outros)', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_ii_valor = fields.Float( string='Total do II', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_ii_valor_aduaneira = fields.Float( string='Total do II Aduaneira', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_irpj_ret_valor = fields.Float( string='Valor do IRPJ Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_inss_ret_valor = fields.Float( string='Valor do INSS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_iss_ret_valor = fields.Float( string='Valor do ISS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_csll_ret_valor = fields.Float( string='Valor do CSLL Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_pis_ret_valor = fields.Float( string='Valor do PIS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_cofins_ret_valor = fields.Float( string='Valor do Cofins Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_total_nfe = fields.Float( string='Total do Pedido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_tributos = fields.Float( string='Total dos Tributos', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    def unlink(self):
        for order in self:
            if order.dfe_id and order.dfe_id.l10n_br_status == '04':
                order.dfe_id.write({'l10n_br_status': '03'})
        res = super(PurchaseOrder, self).unlink()
        return res

    def _get_l10n_br_operacao_id(self):
        for record in self:
            record.l10n_br_operacao_id = record.order_line[0].l10n_br_operacao_id if len(record.order_line) > 0 else False

    @api.onchange('l10n_br_calcular_imposto')
    def onchange_l10n_br_calcular_imposto(self, **kwargs):
        for item in self:
            item._do_rateio_frete()
            for line in item.order_line:
                line._do_calculate_l10n_br_impostos(**kwargs)
            item._do_calculate_l10n_br_impostos()

    def _do_rateio_frete(self):

        self.ensure_one()

        for line in self.order_line:
            values_to_update = {}
            values_to_update['l10n_br_frete'] = 0.00
            values_to_update['l10n_br_seguro'] = 0.00
            values_to_update['l10n_br_despesas_acessorias'] = 0.00

            line.update(values_to_update)

        l10n_br_frete = self.l10n_br_frete
        l10n_br_seguro = self.l10n_br_seguro
        l10n_br_despesas_acessorias = self.l10n_br_despesas_acessorias

        for line in self.order_line:
            values_to_update = {}

            fator = (line.l10n_br_prod_valor - line.l10n_br_desc_valor) / ((self.l10n_br_prod_valor - self.l10n_br_desc_valor) or 1.00)

            values_to_update['l10n_br_frete'] = round(l10n_br_frete * fator,2)
            values_to_update['l10n_br_seguro'] = round(l10n_br_seguro * fator,2)
            values_to_update['l10n_br_despesas_acessorias'] = round(l10n_br_despesas_acessorias * fator,2)

            l10n_br_frete -= values_to_update['l10n_br_frete']
            l10n_br_seguro -= values_to_update['l10n_br_seguro']
            l10n_br_despesas_acessorias -= values_to_update['l10n_br_despesas_acessorias']

            if line == self.order_line[-1]:
                values_to_update['l10n_br_frete'] += l10n_br_frete
                values_to_update['l10n_br_seguro'] += l10n_br_seguro
                values_to_update['l10n_br_despesas_acessorias'] += l10n_br_despesas_acessorias

            line.update(values_to_update)

    def _do_calculate_l10n_br_impostos(self):

        if self.company_id.country_id != self.env.ref('base.br'):
            return

        self.ensure_one()

        if not self.l10n_br_imposto_auto:
            return

        #############################
        ##### INFORMAÇÃO FISCAL #####
        #############################
        values_to_update = {}

        l10n_br_mensagem_fiscal_ids = []
        for line in self.order_line:
            if line.l10n_br_mensagem_fiscal_ids and line.l10n_br_mensagem_fiscal_ids.ids:
                l10n_br_mensagem_fiscal_ids = l10n_br_mensagem_fiscal_ids + line.l10n_br_mensagem_fiscal_ids.ids
    
        l10n_br_mensagem_fiscal_ids = list(dict.fromkeys(l10n_br_mensagem_fiscal_ids))
        mensagens = self.env['l10n_br_ciel_it_account.mensagem.fiscal'].browse(l10n_br_mensagem_fiscal_ids)
        l10n_br_informacao_fiscal = ''
        for mensagem in mensagens:
            l10n_br_informacao_fiscal += (" " if l10n_br_informacao_fiscal else "") + mensagem.name

        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_mensagem_fiscal_01_id%%',self.partner_id.l10n_br_mensagem_fiscal_01_id.name or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_mensagem_fiscal_02_id%%',self.partner_id.l10n_br_mensagem_fiscal_02_id.name or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_mensagem_fiscal_03_id%%',self.partner_id.l10n_br_mensagem_fiscal_03_id.name or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_mensagem_fiscal_04_id%%',self.partner_id.l10n_br_mensagem_fiscal_04_id.name or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_mensagem_fiscal_05_id%%',self.partner_id.l10n_br_mensagem_fiscal_05_id.name or "")

        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_is%%',self.partner_id.l10n_br_is or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%email%%',self.partner_id.email or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%invoice_origin%%',self.name or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_pedido_compra%%',"")

        values_to_update['l10n_br_informacao_fiscal'] = l10n_br_informacao_fiscal

        self.update(values_to_update)

    @api.onchange('order_line','l10n_br_tipo_pedido','partner_id','company_id','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias')
    def onchange_l10n_br_imposto(self):
        for item in self:
            item.l10n_br_calcular_imposto = not item.l10n_br_calcular_imposto

    @api.depends('order_line.l10n_br_icms_base','order_line.l10n_br_icms_valor','order_line.l10n_br_icmsst_base','order_line.l10n_br_icmsst_valor','order_line.l10n_br_icmsst_valor_outros',
        'order_line.l10n_br_prod_valor','order_line.l10n_br_desc_valor','order_line.l10n_br_ipi_valor','order_line.l10n_br_pis_valor',
        'order_line.l10n_br_cofins_valor','order_line.l10n_br_total_nfe','order_line.l10n_br_total_tributos','order_line.l10n_br_icms_dest_valor',
        'order_line.l10n_br_icms_remet_valor','order_line.l10n_br_fcp_dest_valor','order_line.l10n_br_fcp_st_valor','order_line.l10n_br_fcp_st_ant_valor',
        'order_line.l10n_br_icms_valor_isento','order_line.l10n_br_icms_valor_outros','order_line.l10n_br_icms_valor_desonerado','order_line.l10n_br_ipi_valor_isento','order_line.l10n_br_ipi_valor_outros',
        'order_line.l10n_br_pis_valor_isento','order_line.l10n_br_pis_valor_outros','order_line.l10n_br_cofins_valor_isento','order_line.l10n_br_cofins_valor_outros','order_line.l10n_br_ii_valor','order_line.l10n_br_ii_valor_aduaneira',
        'order_line.l10n_br_irpj_ret_valor','order_line.l10n_br_inss_ret_valor','order_line.l10n_br_iss_ret_valor','order_line.l10n_br_csll_ret_valor','order_line.l10n_br_pis_ret_valor','order_line.l10n_br_cofins_ret_valor',
        'order_line.l10n_br_icmsst_substituto_valor', 'order_line.l10n_br_icmsst_substituto_valor_outros', 'order_line.l10n_br_icmsst_retido_valor', 'order_line.l10n_br_icmsst_retido_valor_outros')
    def _l10n_br_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            l10n_br_icms_base = sum(order.order_line.mapped('l10n_br_icms_base'))
            l10n_br_icms_valor = sum(order.order_line.mapped('l10n_br_icms_valor'))
            l10n_br_icms_valor_isento = sum(order.order_line.mapped('l10n_br_icms_valor_isento'))
            l10n_br_icms_valor_outros = sum(order.order_line.mapped('l10n_br_icms_valor_outros'))
            l10n_br_icms_valor_desonerado = sum(order.order_line.mapped('l10n_br_icms_valor_desonerado'))
            l10n_br_icms_dest_valor = sum(order.order_line.mapped('l10n_br_icms_dest_valor'))
            l10n_br_icms_remet_valor = sum(order.order_line.mapped('l10n_br_icms_remet_valor'))
            l10n_br_fcp_dest_valor = sum(order.order_line.mapped('l10n_br_fcp_dest_valor'))
            l10n_br_fcp_st_valor = sum(order.order_line.mapped('l10n_br_fcp_st_valor'))
            l10n_br_fcp_st_ant_valor = sum(order.order_line.mapped('l10n_br_fcp_st_ant_valor'))
            l10n_br_icmsst_base = sum(order.order_line.mapped('l10n_br_icmsst_base'))
            l10n_br_icmsst_valor = sum(order.order_line.mapped('l10n_br_icmsst_valor'))
            l10n_br_icmsst_valor_outros = sum(order.order_line.mapped('l10n_br_icmsst_valor_outros'))
            l10n_br_icmsst_substituto_valor = sum(order.order_line.mapped('l10n_br_icmsst_substituto_valor'))
            l10n_br_icmsst_substituto_valor_outros = sum(order.order_line.mapped('l10n_br_icmsst_substituto_valor_outros'))
            l10n_br_icmsst_retido_valor = sum(order.order_line.mapped('l10n_br_icmsst_retido_valor'))
            l10n_br_icmsst_retido_valor_outros = sum(order.order_line.mapped('l10n_br_icmsst_retido_valor_outros'))
            l10n_br_prod_valor = sum(order.order_line.mapped('l10n_br_prod_valor'))
            l10n_br_desc_valor = sum(order.order_line.mapped('l10n_br_desc_valor'))
            l10n_br_ipi_valor = sum(order.order_line.mapped('l10n_br_ipi_valor'))
            l10n_br_ipi_valor_isento = sum(order.order_line.mapped('l10n_br_ipi_valor_isento'))
            l10n_br_ipi_valor_outros = sum(order.order_line.mapped('l10n_br_ipi_valor_outros'))
            l10n_br_pis_valor = sum(order.order_line.mapped('l10n_br_pis_valor'))
            l10n_br_pis_valor_isento = sum(order.order_line.mapped('l10n_br_pis_valor_isento'))
            l10n_br_pis_valor_outros = sum(order.order_line.mapped('l10n_br_pis_valor_outros'))
            l10n_br_cofins_valor = sum(order.order_line.mapped('l10n_br_cofins_valor'))
            l10n_br_cofins_valor_isento = sum(order.order_line.mapped('l10n_br_cofins_valor_isento'))
            l10n_br_cofins_valor_outros = sum(order.order_line.mapped('l10n_br_cofins_valor_outros'))
            l10n_br_ii_valor = sum(order.order_line.mapped('l10n_br_ii_valor'))
            l10n_br_ii_valor_aduaneira = sum(order.order_line.mapped('l10n_br_ii_valor_aduaneira'))
            l10n_br_irpj_ret_valor = sum(order.order_line.mapped('l10n_br_irpj_ret_valor'))
            l10n_br_inss_ret_valor = sum(order.order_line.mapped('l10n_br_inss_ret_valor'))
            l10n_br_iss_ret_valor = sum(order.order_line.mapped('l10n_br_iss_ret_valor'))
            l10n_br_csll_ret_valor = sum(order.order_line.mapped('l10n_br_csll_ret_valor'))
            l10n_br_pis_ret_valor = sum(order.order_line.mapped('l10n_br_pis_ret_valor'))
            l10n_br_cofins_ret_valor = sum(order.order_line.mapped('l10n_br_cofins_ret_valor'))
            l10n_br_total_nfe = sum(order.order_line.mapped('l10n_br_total_nfe'))
            l10n_br_total_tributos = sum(order.order_line.mapped('l10n_br_total_tributos'))

            order.update({
                'l10n_br_icms_base': l10n_br_icms_base,
                'l10n_br_icms_valor': l10n_br_icms_valor,
                'l10n_br_icms_valor_isento': l10n_br_icms_valor_isento,
                'l10n_br_icms_valor_outros': l10n_br_icms_valor_outros,
                'l10n_br_icms_valor_desonerado': l10n_br_icms_valor_desonerado,
                'l10n_br_icms_dest_valor': l10n_br_icms_dest_valor,
                'l10n_br_icms_remet_valor': l10n_br_icms_remet_valor,
                'l10n_br_fcp_dest_valor': l10n_br_fcp_dest_valor,
                'l10n_br_fcp_st_valor': l10n_br_fcp_st_valor,
                'l10n_br_fcp_st_ant_valor': l10n_br_fcp_st_ant_valor,
                'l10n_br_icmsst_base': l10n_br_icmsst_base,
                'l10n_br_icmsst_valor': l10n_br_icmsst_valor,
                'l10n_br_icmsst_valor_outros': l10n_br_icmsst_valor_outros,
                'l10n_br_icmsst_substituto_valor': l10n_br_icmsst_substituto_valor,
                'l10n_br_icmsst_substituto_valor_outros': l10n_br_icmsst_substituto_valor_outros,
                'l10n_br_icmsst_retido_valor': l10n_br_icmsst_retido_valor,
                'l10n_br_icmsst_retido_valor_outros': l10n_br_icmsst_retido_valor_outros,
                'l10n_br_prod_valor': l10n_br_prod_valor,
                'l10n_br_desc_valor': l10n_br_desc_valor,
                'l10n_br_ipi_valor': l10n_br_ipi_valor,
                'l10n_br_ipi_valor_isento': l10n_br_ipi_valor_isento,
                'l10n_br_ipi_valor_outros': l10n_br_ipi_valor_outros,
                'l10n_br_pis_valor': l10n_br_pis_valor,
                'l10n_br_pis_valor_isento': l10n_br_pis_valor_isento,
                'l10n_br_pis_valor_outros': l10n_br_pis_valor_outros,
                'l10n_br_cofins_valor': l10n_br_cofins_valor,
                'l10n_br_cofins_valor_isento': l10n_br_cofins_valor_isento,
                'l10n_br_cofins_valor_outros': l10n_br_cofins_valor_outros,
                'l10n_br_ii_valor': l10n_br_ii_valor,
                'l10n_br_ii_valor_aduaneira': l10n_br_ii_valor_aduaneira,
                'l10n_br_irpj_ret_valor': l10n_br_irpj_ret_valor,
                'l10n_br_inss_ret_valor': l10n_br_inss_ret_valor,
                'l10n_br_iss_ret_valor': l10n_br_iss_ret_valor,
                'l10n_br_csll_ret_valor': l10n_br_csll_ret_valor,
                'l10n_br_pis_ret_valor': l10n_br_pis_ret_valor,
                'l10n_br_cofins_ret_valor': l10n_br_cofins_ret_valor,
                'l10n_br_total_nfe': l10n_br_total_nfe,
                'l10n_br_total_tributos': l10n_br_total_tributos,
            })

    def _prepare_invoice(self):
    
        invoice_vals = {}

        if self.company_id.country_id != self.env.ref('base.br'):
            return invoice_vals

        if self.l10n_br_tipo_pedido in TIPO_PEDIDO_ENTRADA_DEVOLUCAO:
            invoice_vals['type'] = 'out_refund'

        if self.l10n_br_tipo_pedido in TIPO_PEDIDO_ENTRADA_NO_PAYMENT:
            company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', 'purchase'), ('l10n_br_no_payment', '=', True), ('l10n_br_tipo_pedido', '=', False), ('l10n_br_tipo_pedido_entrada', '=', self.l10n_br_tipo_pedido)]
            journal = self.env['account.journal'].search(domain, limit=1)
            invoice_vals['journal_id'] = journal.id
            if journal.fiscal_position_id:
                invoice_vals['fiscal_position_id'] = journal.fiscal_position_id.id

        invoice_vals['l10n_br_tipo_pedido_entrada'] = self.l10n_br_tipo_pedido

        invoice_vals['l10n_br_informacao_fiscal'] = self.l10n_br_informacao_fiscal
        invoice_vals['l10n_br_informacao_complementar'] = self.l10n_br_informacao_complementar

        if self.l10n_br_cfop_id:
            invoice_vals['l10n_br_cfop_id'] = self.l10n_br_cfop_id.id

        if self.payment_acquirer_id:
            invoice_vals['payment_acquirer_id'] = self.payment_acquirer_id.id

        invoice_vals['l10n_br_imposto_auto'] = self.l10n_br_imposto_auto
        invoice_vals['l10n_br_calcular_imposto'] = self.l10n_br_calcular_imposto

        invoice_vals['l10n_br_frete'] = self.l10n_br_frete
        invoice_vals['l10n_br_seguro'] = self.l10n_br_seguro
        invoice_vals['l10n_br_despesas_acessorias'] = self.l10n_br_despesas_acessorias
        invoice_vals['invoice_incoterm_id'] = self.incoterm_id.id
        
        if self.dfe_id:
            invoice_vals['dfe_id'] = self.dfe_id.id
            invoice_vals['l10n_br_chave_nf'] = self.dfe_id.protnfe_infnfe_chnfe
            invoice_vals['l10n_br_numero_nf'] = self.dfe_id.nfe_infnfe_ide_nnf
            invoice_vals['l10n_br_serie_nf'] = self.dfe_id.nfe_infnfe_ide_serie
            invoice_vals['invoice_date'] = self.dfe_id.nfe_infnfe_ide_dhemi
            invoice_vals['date'] = self.dfe_id.l10n_br_data_entrada
            if self.dfe_id.protnfe_infnfe_chnfe:
                invoice_vals['l10n_br_tipo_documento'] = self.dfe_id.protnfe_infnfe_chnfe[20:22]
            invoice_vals['l10n_br_xml_aut_nfe'] = self.dfe_id.l10n_br_xml_dfe
            invoice_vals['l10n_br_pdf_aut_nfe'] = self.dfe_id.l10n_br_pdf_dfe
            invoice_vals['invoice_payment_ref'] = self.dfe_id.payment_reference

            l10n_br_icms_credito_valor = sum(self.dfe_id.lines_ids.mapped('det_imposto_icms_vcredicmssn'))
            invoice_vals['simples_nacional'] = l10n_br_icms_credito_valor > 0.00
            if self.dfe_id.cte_infcte_ide_cmunini:
                invoice_vals['l10n_br_municipio_inicio_id'] = self.env["l10n_br_ciel_it_account.res.municipio"].search([("codigo_ibge","=",self.dfe_id.cte_infcte_ide_cmunini)],limit=1).id
            if self.dfe_id.cte_infcte_ide_cmunfim:
                invoice_vals['l10n_br_municipio_fim_id'] = self.env["l10n_br_ciel_it_account.res.municipio"].search([("codigo_ibge","=",self.dfe_id.cte_infcte_ide_cmunfim)],limit=1).id

        return invoice_vals

    def button_cancel_all(self):
        if any(po.state == 'done' for po in self):
            raise UserError(_("Some purchase order are already done, you cannot cancel this purchase order."))
        self.button_cancel()


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    account_id = fields.Many2one('account.account', string='Account', index=True, ondelete="cascade", check_company=True, domain=[('deprecated', '=', False)])
    dfe_line_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe.line', string='Item Documento Fiscal', check_company=True )

    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', domain = [('l10n_br_tipo_operacao','=','entrada')], check_company=True )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP', default=lambda self: self.order_id.l10n_br_cfop_id )
    l10n_br_cfop_codigo = fields.Char( related='l10n_br_cfop_id.codigo_cfop' )
    l10n_br_frete = fields.Float( string='Frete' )
    l10n_br_seguro = fields.Float( string='Seguro' )
    l10n_br_despesas_acessorias = fields.Float( string='Despesas Acessórias' )
    l10n_br_desc_valor = fields.Float( string='Valor do Desconto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_prod_valor = fields.Float( string='Valor do Produto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_nfe = fields.Float( string='Valor do Item do Pedido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_tributos = fields.Float( string='Valor dos Tributos', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_informacao_adicional = fields.Text( string='Informações Adicionais' )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )
    l10n_br_mensagem_fiscal_ids = fields.Many2many( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal' )

    l10n_br_imposto_auto = fields.Boolean( related='order_id.l10n_br_imposto_auto' )
    l10n_br_calcular_imposto = fields.Boolean( related='order_id.l10n_br_calcular_imposto' )

    l10n_br_icms_modalidade_base = fields.Selection( MODALIDADE_ICMS, string='Modalidade de Determinação da BC do ICMS' )
    l10n_br_icms_reducao_base = fields.Float( string='Aliquota de Redução da BC do ICMS (%)', digits = (12,4) )
    l10n_br_icms_diferido_valor_operacao = fields.Float( string='Valor do ICMS da Operação' )
    l10n_br_icms_diferido_aliquota = fields.Float( string='Aliquota do ICMS Diferido (%)' )
    l10n_br_icms_diferido_valor = fields.Float( string='Valor do ICMS Diferido' )

    l10n_br_icms_cst = fields.Selection( ICMS_CST, string='Código de Situação Tributária do ICMS' )
    l10n_br_icms_base = fields.Float( string='Valor da Base de Cálculo do ICMS' )
    l10n_br_icms_aliquota = fields.Float( string='Aliquota do ICMS (%)' )
    l10n_br_icms_valor = fields.Float( string='Valor do ICMS' )
    l10n_br_icms_valor_isento = fields.Float( string='Valor do ICMS (Isento/Não Tributável)' )
    l10n_br_icms_valor_outros = fields.Float( string='Valor do ICMS (Outros)' )
    l10n_br_icms_valor_desonerado = fields.Float( string='Valor do ICMS (Desonerado)' )
    l10n_br_icms_motivo_desonerado = fields.Selection( MOTIVO_ICMS_DESONERACAO, string='Motivo Desoneração do ICMS' )

    l10n_br_icms_dest_base = fields.Float( string='Valor da Base de Cálculo do ICMS UF Destino' )
    l10n_br_icms_dest_aliquota = fields.Float( string='Aliquota do ICMS UF Destino (%)' )
    l10n_br_icms_inter_aliquota = fields.Float( string='Aliquota do ICMS Interestadual (%)' )
    l10n_br_icms_inter_participacao = fields.Float( string='Participação da Aliquota do ICMS Interestadual (%)' )
    l10n_br_icms_dest_valor = fields.Float( string='Valor do ICMS UF Destino' )
    l10n_br_icms_remet_valor = fields.Float( string='Valor do ICMS UF Remetente' )

    l10n_br_icms_credito_aliquota = fields.Float( string='Alíquota aplicável de cálculo do crédito (Simples Nacional)' )
    l10n_br_icms_credito_valor = fields.Float( string='Valor crédito do ICMS que pode ser aproveitado' )

    l10n_br_codigo_beneficio = fields.Char( string='Código do Benefício Fiscal' )

    l10n_br_fcp_base = fields.Float( string='Valor da Base do Fundo de Combate a Pobreza' )
    l10n_br_fcp_dest_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%)' )
    l10n_br_fcp_dest_valor = fields.Float( string='Valor do Fundo de Combate a Pobreza' )

    l10n_br_fcp_st_base = fields.Float( string='Valor da Base do Fundo de Combate a Pobreza retido por ST' )
    l10n_br_fcp_st_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%) retido por ST' )
    l10n_br_fcp_st_valor = fields.Float( string='Valor do Fundo de Combate a Pobreza retido por ST' )

    l10n_br_fcp_st_ant_base = fields.Float( string='Valor da Base do Fundo de Combate a Pobreza retido anteriormente por ST' )
    l10n_br_fcp_st_ant_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%) retido anteriormente por ST' )
    l10n_br_fcp_st_ant_valor = fields.Float( string='Valor do Fundo de Combate a Pobreza retido anteriormente por ST' )

    l10n_br_icmsst_modalidade_base = fields.Selection( MODALIDADE_ICMSST, string='Modalidade de Determinação da BC do ICMSST' )
    l10n_br_icmsst_reducao_base = fields.Float( string='Aliquota de Redução da BC do ICMSST (%)', digits = (12,4) )
    l10n_br_icmsst_mva = fields.Float( string='Aliquota da Margem de Valor Adicionado do ICMSST (%)' )

    l10n_br_icmsst_base = fields.Float( string='Valor da Base de Cálculo do ICMSST' )
    l10n_br_icmsst_aliquota = fields.Float( string='Aliquota do ICMSST (%)' )
    l10n_br_icmsst_valor = fields.Float( string='Valor do ICMSST' )
    l10n_br_icmsst_valor_outros = fields.Float( string='Valor do ICMSST (Outros)' )

    l10n_br_icmsst_retido_base = fields.Float( string='Valor da Base de Cálculo do ICMSST Retido' )
    l10n_br_icmsst_retido_aliquota = fields.Float( string='Alíquota suportada pelo Consumidor Final (%)' )
    l10n_br_icmsst_substituto_valor = fields.Float( string='Valor do ICMS próprio do Substituto' )
    l10n_br_icmsst_substituto_valor_outros = fields.Float( string='Valor do ICMS próprio do Substituto (Outros)' )
    l10n_br_icmsst_retido_valor = fields.Float( string='Valor do ICMSST Retido' )
    l10n_br_icmsst_retido_valor_outros = fields.Float( string='Valor do ICMSST Retido (Outros)' )

    l10n_br_icmsst_base_propria_aliquota = fields.Float( string='Alíquota da Base de Cálculo da Operação Própria' )
    l10n_br_icmsst_uf = fields.Char( string='UF para qual é devido o ICMSST' )

    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )
    l10n_br_ipi_base = fields.Float( string='Valor da Base de Cálculo do IPI' )
    l10n_br_ipi_aliquota = fields.Float( string='Aliquota do IPI (%)' )
    l10n_br_ipi_valor = fields.Float( string='Valor do IPI' )
    l10n_br_ipi_valor_isento = fields.Float( string='Valor do IPI (Isento/Não Tributável)' )
    l10n_br_ipi_valor_outros = fields.Float( string='Valor do IPI (Outros)' )

    l10n_br_ipi_cnpj = fields.Char( string='CNPJ do produtor da mercadoria' )
    l10n_br_ipi_selo_codigo = fields.Char( string='Código do selo de controle IPI' )
    l10n_br_ipi_selo_quantidade = fields.Integer( string='Quantidade de selo de controle' )
    l10n_br_ipi_enq = fields.Char( string='Código Enquadramento' )

    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_pis_base = fields.Float( string='Valor da Base de Cálculo do PIS' )
    l10n_br_pis_aliquota = fields.Float( string='Aliquota do PIS (%)' )
    l10n_br_pis_valor = fields.Float( string='Valor do PIS' )
    l10n_br_pis_valor_isento = fields.Float( string='Valor do PIS (Isento/Não Tributável)' )
    l10n_br_pis_valor_outros = fields.Float( string='Valor do PIS (Outros)' )

    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )
    l10n_br_cofins_base = fields.Float( string='Valor da Base de Cálculo do Cofins' )
    l10n_br_cofins_aliquota = fields.Float( string='Aliquota do Cofins (%)' )
    l10n_br_cofins_valor = fields.Float( string='Valor do Cofins' )
    l10n_br_cofins_valor_isento = fields.Float( string='Valor do Cofins (Isento/Não Tributável)' )
    l10n_br_cofins_valor_outros = fields.Float( string='Valor do Cofins (Outros)' )

    l10n_br_ii_base = fields.Float( string='Valor da Base de Cálculo do II' )
    l10n_br_ii_aliquota = fields.Float( string='Aliquota do II (%)' )
    l10n_br_ii_valor = fields.Float( string='Valor do II' )
    l10n_br_ii_valor_aduaneira = fields.Float( string='Valor do II Aduaneira' )
    l10n_br_di_adicao_id = fields.Many2one('l10n_br_ciel_it_account.di.adicao', string='DI/Adição', check_company=True)

    l10n_br_irpj_ret_base = fields.Float( string='Valor da Base de Cálculo do IRPJ Retido' )
    l10n_br_irpj_ret_aliquota = fields.Float( string='Aliquota do IRPJ Retido (%)' )
    l10n_br_irpj_ret_valor = fields.Float( string='Valor do IRPJ Retido' )

    l10n_br_inss_ret_base = fields.Float( string='Valor da Base de Cálculo do INSS Retido' )
    l10n_br_inss_ret_aliquota = fields.Float( string='Aliquota do INSS Retido (%)' )
    l10n_br_inss_ret_valor = fields.Float( string='Valor do INSS Retido' )

    l10n_br_iss_ret_base = fields.Float( string='Valor da Base de Cálculo do ISS Retido' )
    l10n_br_iss_ret_aliquota = fields.Float( string='Aliquota do ISS Retido (%)' )
    l10n_br_iss_ret_valor = fields.Float( string='Valor do ISS Retido' )

    l10n_br_csll_ret_base = fields.Float( string='Valor da Base de Cálculo do CSLL Retido' )
    l10n_br_csll_ret_aliquota = fields.Float( string='Aliquota do CSLL (%) Retido' )
    l10n_br_csll_ret_valor = fields.Float( string='Valor do CSLL Retido' )

    l10n_br_pis_ret_base = fields.Float( string='Valor da Base de Cálculo do PIS Retido' )
    l10n_br_pis_ret_aliquota = fields.Float( string='Aliquota do PIS (%) Retido' )
    l10n_br_pis_ret_valor = fields.Float( string='Valor do PIS Retido' )

    l10n_br_cofins_ret_base = fields.Float( string='Valor da Base de Cálculo do Cofins Retido' )
    l10n_br_cofins_ret_aliquota = fields.Float( string='Aliquota do Cofins (%) Retido' )
    l10n_br_cofins_ret_valor = fields.Float( string='Valor do Cofins Retido' )

    qty_available = fields.Float( related='product_id.qty_available' )
    virtual_available = fields.Float( related='product_id.virtual_available' )

    def _get_stock_move_price_unit(self):

        price_unit = super(PurchaseOrderLine, self)._get_stock_move_price_unit()
        if self.company_id.country_id != self.env.ref('base.br'):
            return price_unit

        line = self[0]
        new_price_unit = (line.l10n_br_total_nfe - line.l10n_br_icms_valor - line.l10n_br_ipi_valor) / (line.product_qty or 1.00)
        price_unit = price_unit > 0.00 and new_price_unit or -new_price_unit
        return price_unit

    @api.model
    def _handle_taxes(self, name, tax_key, price_include, amount):

        company = self.env.company
        tax_master = self.env['account.tax'].sudo().search([
            ('name', '=', name+'[*]'),
            ('amount_type', '=', 'fixed_total'),
            ('amount', '=', 0.00),
            ('company_id', '=', company.id),
            ('price_include', '=', price_include),
            ('type_tax_use', '=', 'purchase')], limit=1)
        if not tax_master:
            tax_master = self.env['account.tax'].sudo().create({
                'name': name+'[*]',
                'amount': 0.00,
                'amount_type': 'fixed_total',
                'type_tax_use': 'purchase',
                'description': name,
                'company_id': company.id,
                'price_include': price_include,
                'active': True,
            })

        tax = self.env['account.tax'].sudo().search([
            ('name', '=', name+'['+tax_key+']'),
            ('company_id', '=', company.id),
            ('price_include', '=', price_include),
            ('type_tax_use', '=', 'purchase')], limit=1)
        if not tax:
            tax = tax_master.copy()
        tax.update({'name': name+'['+tax_key+']', 'description': name, 'amount_type': 'fixed_total', 'amount': amount})

        return tax

    def l10n_br_compute_tax_id(self):
        for line in self:

            tax_key = str(uuid.uuid4())[:8]
            line.update({'taxes_id': [(5,)]})

            if line.order_id.l10n_br_tipo_pedido == 'importacao':

                ## ICMS ##
                amount = line.l10n_br_icms_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    if line.order_id.company_id.l10n_br_incidencia_cumulativa == '2' and line.order_id.company_id.l10n_br_regime_tributario == '3':
                        tax_icms_id = line._handle_taxes('ICMS EX', tax_key, True, amount)
                        line.update({'taxes_id': [(4, tax_icms_id.id)]})
                    else:
                        tax_icms_id = line._handle_taxes('ICMS EX', tax_key, False, amount)
                        line.update({'taxes_id': [(4, tax_icms_id.id)]})
            else:

                ## ICMS ##
                amount = line.l10n_br_icms_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_icms_id = line._handle_taxes('ICMS', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_isento # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS ISENTO', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS OUTROS', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_desonerado # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS DESONERADO', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icms_id.id)]})

            ## ICMSST ##
            amount = line.l10n_br_icmsst_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            ## ICMSST ##
            amount = line.l10n_br_icmsst_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST OUTROS', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_substituto_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST SUB', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_substituto_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST SUB OUTROS', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_retido_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST RET', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_retido_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST RET OUTROS', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_icmsst_id.id)]})

            ## IPI ##
            amount = line.l10n_br_ipi_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_ipi_id.id)]})

            amount = line.l10n_br_ipi_valor_isento # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI ISENTO', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_ipi_id.id)]})

            amount = line.l10n_br_ipi_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI OUTROS', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_ipi_id.id)]})

            if line.order_id.l10n_br_tipo_pedido == 'importacao':
                ## PIS ##
                amount = line.l10n_br_pis_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS EX', tax_key, False, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_isento # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS ISENTO EX', tax_key, False, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_outros # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS OUTROS EX', tax_key, False, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                ## COFINS ##
                amount = line.l10n_br_cofins_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS EX', tax_key, False, amount)
                    line.update({'taxes_id': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_isento # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS ISENTO EX', tax_key, False, amount)
                    line.update({'taxes_id': [(4, tax_cofins_id.id)]})

            else:

                ## PIS ##
                amount = line.l10n_br_pis_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_isento # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS ISENTO', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_outros # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS OUTROS', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_pis_id.id)]})

                ## COFINS ##
                amount = line.l10n_br_cofins_valor # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_isento # / (line.product_qty or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS ISENTO', tax_key, True, amount)
                    line.update({'taxes_id': [(4, tax_cofins_id.id)]})

            amount = line.l10n_br_cofins_valor_outros # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_cofins_id = line._handle_taxes('COFINS OUTROS', tax_key, True, amount)
                line.update({'taxes_id': [(4, tax_cofins_id.id)]})

            ## II ##
            amount = line.l10n_br_ii_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_ii_id = line._handle_taxes('II', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_ii_id.id)]})

            ## ADUANEIRA ##
            amount = line.l10n_br_ii_valor_aduaneira # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_ii_id = line._handle_taxes('ADUANEIRA', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_ii_id.id)]})

            ## CSLL RET ##
            amount = line.l10n_br_csll_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_csll_ret_id = line._handle_taxes('CSLL RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_csll_ret_id.id)]})

            ## IRPJ RET ##
            amount = line.l10n_br_irpj_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_irpj_ret_id = line._handle_taxes('IRPJ RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_irpj_ret_id.id)]})

            ## INSS RET ##
            amount = line.l10n_br_inss_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_inss_ret_id = line._handle_taxes('INSS RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_inss_ret_id.id)]})

            ## ISS RET ##
            amount = line.l10n_br_iss_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_iss_ret_id = line._handle_taxes('ISS RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_iss_ret_id.id)]})

            ## PIS RET ##
            amount = line.l10n_br_pis_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_pis_ret_id = line._handle_taxes('PIS RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_pis_ret_id.id)]})

            ## COFINS RET ##
            amount = line.l10n_br_cofins_ret_valor # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_cofins_ret_id = line._handle_taxes('COFINS RET', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_cofins_ret_id.id)]})

            ## FRETE ##
            amount = line.l10n_br_frete # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_frete_id = line._handle_taxes('FRETE', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_frete_id.id)]})

            ## SEGURO ##
            amount = line.l10n_br_seguro # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_seguro_id = line._handle_taxes('SEGURO', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_seguro_id.id)]})

            ## DESPESAS ##
            amount = line.l10n_br_despesas_acessorias # / (line.product_qty or 1.00)
            if amount != 0.00:
                tax_despesas_id = line._handle_taxes('DESPESAS', tax_key, False, amount)
                line.update({'taxes_id': [(4, tax_despesas_id.id)]})

    @api.onchange('product_id')
    def l10n_br_onchange_product_id(self):
        for item in self:
            item.account_id = self._get_computed_account()
            item._do_update_l10n_br_informacao_adicional()

    def _do_update_l10n_br_informacao_adicional(self):

        ################################
        ##### INFORMAÇÃO ADICIONAL #####
        ################################
        values_to_update = {}
        values_to_update['l10n_br_informacao_adicional'] = self.product_id.l10n_br_informacao_adicional
        self.update(values_to_update)

    def _do_calculate_l10n_br_impostos(self, **kwargs):

        self.ensure_one()

        if self.l10n_br_imposto_auto:

            ##############################
            ##### DETERMINA OPERAÇÃO #####
            ##############################
            values_to_update = {}

            values_to_update['l10n_br_operacao_id'] = False

            domain = [('l10n_br_tipo_operacao','=','entrada'),('l10n_br_tipo_pedido_entrada','=',self.order_id.l10n_br_tipo_pedido)]

            l10n_br_tipo_produto = 'produzido'
            if self.product_id.type == 'service':
                l10n_br_tipo_produto = 'servico'
            elif self.product_id.purchase_ok:
                l10n_br_tipo_produto = 'comprado'

            domain_aux = expression.OR([
                [('l10n_br_tipo_produto','=',l10n_br_tipo_produto)],
                [('l10n_br_tipo_produto','=',False)],
                [('l10n_br_tipo_produto','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            l10n_br_tipo_cliente = 'pj'
            if self.order_id.partner_id.l10n_br_cpf:
                l10n_br_tipo_cliente = 'pf'
            if self.order_id.company_id.country_id != self.order_id.partner_id.country_id:
                l10n_br_tipo_cliente = 'ex'
            if self.order_id.partner_id.l10n_br_is:
                l10n_br_tipo_cliente = 'zf'
        
            domain_aux = expression.OR([
                [('l10n_br_tipo_cliente','=',l10n_br_tipo_cliente)],
                [('l10n_br_tipo_cliente','=',False)],
                [('l10n_br_tipo_cliente','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            domain_aux = expression.OR([
                [('l10n_br_indicador_ie','=',self.order_id.partner_id.l10n_br_indicador_ie)],
                [('l10n_br_indicador_ie','=',False)],
                [('l10n_br_indicador_ie','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            l10n_br_destino_operacao = ''
            if self.order_id.company_id.state_id == self.order_id.partner_id.state_id:
                l10n_br_destino_operacao = '1' # 1 - Operação interna
            elif self.order_id.company_id.country_id != self.order_id.partner_id.country_id:
                l10n_br_destino_operacao = '3' # 3 - Operação com exterior
            else:
                l10n_br_destino_operacao = '2' # 2 - Opeação interestadual
        
            domain_aux = expression.OR([
                [('l10n_br_destino_operacao','=',l10n_br_destino_operacao)],
                [('l10n_br_destino_operacao','=',False)],
                [('l10n_br_destino_operacao','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            l10n_br_tipo_destinacao = 'uso'
            if self.l10n_br_compra_indcom:
                l10n_br_tipo_destinacao = self.l10n_br_compra_indcom

            domain_aux = expression.OR([
                [('l10n_br_tipo_destinacao','=',l10n_br_tipo_destinacao)],
                [('l10n_br_tipo_destinacao','=',False)],
                [('l10n_br_tipo_destinacao','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            if self.dfe_line_id.det_imposto_icms_cst in ['10','30','60','70','201','202','203','500']:
                domain_aux = expression.OR([
                    [('l10n_br_operacao_icmsst','=','cst_st')],
                    [('l10n_br_operacao_icmsst','=',False)],
                    [('l10n_br_operacao_icmsst','=','')],
                ])
            else:
                ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self.order_id.company_id.state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
                ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self.order_id.company_id.state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.order_id.partner_id.id)],limit=1)
                if ncm_cliente_uf:
                    ncm_uf = ncm_cliente_uf

                if ncm_uf and ncm_uf.l10n_br_icmsst_modalidade_base:
                    domain_aux = expression.OR([
                        [('l10n_br_operacao_icmsst','=','ncmuf')],
                        [('l10n_br_operacao_icmsst','=',False)],
                        [('l10n_br_operacao_icmsst','=','')],
                    ])
                else:
                    domain_aux = expression.OR([
                        [('l10n_br_operacao_icmsst','=',False)],
                        [('l10n_br_operacao_icmsst','=','')],
                    ])
            domain = expression.AND([domain,domain_aux])

            domain_aux = expression.OR([
                [('categ_ids','in',self.product_id.categ_id.id)],
                [('categ_ids','=',False)],
            ])
            domain = expression.AND([domain,domain_aux])

            domain_aux = expression.OR([
                [('product_ids','in',self.product_id.id)],
                [('product_ids','=',False)],
            ])
            domain = expression.AND([domain,domain_aux])

            domain_aux = expression.OR([
                [('partner_ids','in',self.order_id.partner_id.id)],
                [('partner_ids','=',False)],
            ])
            domain = expression.AND([domain,domain_aux])

            operacao = self.env["l10n_br_ciel_it_account.operacao"].search(domain,order='l10n_br_tipo_produto,l10n_br_tipo_cliente,l10n_br_indicador_ie,l10n_br_tipo_destinacao,l10n_br_operacao_icmsst,l10n_br_destino_operacao,categ_is_set desc,product_is_set desc,partner_is_set desc',limit=1)
            if operacao:
                values_to_update['l10n_br_operacao_id'] = operacao.id

            self.update(values_to_update)

            ################
            ##### CFOP #####
            ################
            values_to_update = {}

            values_to_update['l10n_br_cfop_id'] = False
            if self.l10n_br_operacao_id:
                if self.order_id.company_id.state_id == self.order_id.partner_id.state_id:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_intra_cfop_id.id
                elif self.order_id.company_id.country_id != self.order_id.partner_id.country_id:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_ext_cfop_id.id
                else:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_inter_cfop_id.id

            self.update(values_to_update)
            self.order_id.update(values_to_update)

            #############################
            ##### OBSERVAÇÃO FISCAL #####
            #############################
            if self.l10n_br_operacao_id.l10n_br_mensagem_fiscal_id:
                values_to_update = {}
                
                values_to_update['l10n_br_mensagem_fiscal_ids'] = [(6, 0, [self.l10n_br_operacao_id.l10n_br_mensagem_fiscal_id.id])]

                self.update(values_to_update)

            ################
            ###### IPI #####
            ################
            values_to_update = {}
            
            values_to_update['l10n_br_ipi_cst'] = False
            values_to_update['l10n_br_ipi_base'] = False
            values_to_update['l10n_br_ipi_aliquota'] = False
            values_to_update['l10n_br_ipi_valor'] = False
            values_to_update['l10n_br_ipi_valor_isento'] = False
            values_to_update['l10n_br_ipi_valor_outros'] = False
            values_to_update['l10n_br_ipi_enq'] = False
            
            if kwargs.get('ipi_aliquota'):
                values_to_update['l10n_br_ipi_base'] = self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor
                values_to_update['l10n_br_ipi_aliquota'] = self.l10n_br_ipi_aliquota
                values_to_update['l10n_br_ipi_valor'] = round(values_to_update['l10n_br_ipi_base'] * values_to_update['l10n_br_ipi_aliquota'] / 100.00, 2)
            else:
                if self.l10n_br_operacao_id.l10n_br_ipi_cst:
                    values_to_update['l10n_br_ipi_cst'] = self.l10n_br_operacao_id.l10n_br_ipi_cst                
            
            if not kwargs.get('ipi'):
                self.update(values_to_update)

            ################
            ##### ICMS #####
            ################
            values_to_update = {}

            values_to_update['l10n_br_icms_modalidade_base'] = False
            values_to_update['l10n_br_icms_reducao_base'] = False
            values_to_update['l10n_br_icms_diferido_valor_operacao'] = False
            values_to_update['l10n_br_icms_diferido_aliquota'] = False
            values_to_update['l10n_br_icms_diferido_valor'] = False
            values_to_update['l10n_br_icms_cst'] = False
            values_to_update['l10n_br_icms_base'] = False
            values_to_update['l10n_br_icms_aliquota'] = False
            values_to_update['l10n_br_icms_valor'] = False
            values_to_update['l10n_br_icms_valor_isento'] = False
            values_to_update['l10n_br_icms_valor_outros'] = False
            values_to_update['l10n_br_icms_valor_desonerado'] = False
            values_to_update['l10n_br_icms_motivo_desonerado'] = False
            values_to_update['l10n_br_icms_credito_aliquota'] = False
            values_to_update['l10n_br_icms_credito_valor'] = False
            values_to_update['l10n_br_codigo_beneficio'] = False    

            if self.l10n_br_operacao_id.l10n_br_icms_cst:
                values_to_update['l10n_br_icms_cst'] = self.l10n_br_operacao_id.l10n_br_icms_cst
                if values_to_update['l10n_br_icms_cst'] == '00':

                    l10n_br_icms_aliquota = self.l10n_br_operacao_id.l10n_br_icms_aliquota
                    l10n_br_icms_reducao_base = self.l10n_br_operacao_id.l10n_br_icms_reducao_base

                    l10n_br_icms_base = self.l10n_br_total_nfe
                    l10n_br_icms_base = round(l10n_br_icms_base * (1.00 - (l10n_br_icms_reducao_base/100.00)), 2)
                    l10n_br_icms_valor = round(l10n_br_icms_base * l10n_br_icms_aliquota / 100.00, 2)

                    values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                    values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                    values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor

            if kwargs.get('icms_aliquota'):
                l10n_br_icms_aliquota = self.l10n_br_icms_aliquota
                l10n_br_icms_reducao_base = self.l10n_br_icms_reducao_base

                l10n_br_icms_base = self.l10n_br_total_nfe
                l10n_br_icms_base = round(l10n_br_icms_base * (1.00 - (l10n_br_icms_reducao_base/100.00)), 2)
                l10n_br_icms_valor = round(l10n_br_icms_base * l10n_br_icms_aliquota / 100.00, 2)

                values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor

            if not kwargs.get('icms'):
                self.update(values_to_update)

            ##################
            ##### ICMSST #####
            ##################
            #values_to_update = {}
            #
            #values_to_update['l10n_br_icmsst_modalidade_base'] = False
            #values_to_update['l10n_br_icmsst_reducao_base'] = False
            #values_to_update['l10n_br_icmsst_mva'] = False
            #values_to_update['l10n_br_icmsst_base'] = False
            #values_to_update['l10n_br_icmsst_aliquota'] = False
            #values_to_update['l10n_br_icmsst_valor'] = False
            #values_to_update['l10n_br_icmsst_retido_base'] = False
            #values_to_update['l10n_br_icmsst_retido_aliquota'] = False
            #values_to_update['l10n_br_icmsst_substituto_valor'] = False
            #values_to_update['l10n_br_icmsst_retido_valor'] = False
            #
            #self.update(values_to_update)

            #########################
            ##### ICMS PARTILHA #####
            #########################
            #values_to_update = {}
            #
            #values_to_update['l10n_br_icmsst_base_propria_aliquota'] = False
            #values_to_update['l10n_br_icmsst_uf'] = False
            #values_to_update['l10n_br_icms_dest_base'] = False
            #values_to_update['l10n_br_icms_dest_aliquota'] = False
            #values_to_update['l10n_br_icms_inter_aliquota'] = False
            #values_to_update['l10n_br_icms_inter_participacao'] = False
            #values_to_update['l10n_br_icms_dest_valor'] = False
            #values_to_update['l10n_br_icms_remet_valor'] = False
            #
            #self.update(values_to_update)

            ####################
            ######## FCP #######
            ####################
            #values_to_update = {}
            #
            #values_to_update['l10n_br_fcp_base'] = False
            #values_to_update['l10n_br_fcp_dest_aliquota'] = False
            #values_to_update['l10n_br_fcp_dest_valor'] = False
            #values_to_update['l10n_br_fcp_st_base'] = False
            #values_to_update['l10n_br_fcp_st_aliquota'] = False
            #values_to_update['l10n_br_fcp_st_valor'] = False
            #values_to_update['l10n_br_fcp_st_ant_base'] = False
            #values_to_update['l10n_br_fcp_st_ant_aliquota'] = False
            #values_to_update['l10n_br_fcp_st_ant_valor'] = False
            #
            #self.update(values_to_update)

            ###############
            ##### PIS #####
            ###############
            values_to_update = {}

            values_to_update['l10n_br_pis_cst'] = False
            values_to_update['l10n_br_pis_base'] = False
            values_to_update['l10n_br_pis_aliquota'] = False
            values_to_update['l10n_br_pis_valor'] = False
            values_to_update['l10n_br_pis_valor_isento'] = False
            values_to_update['l10n_br_pis_valor_outros'] = False

            if self.l10n_br_cfop_id.l10n_br_pis_cst:
                values_to_update['l10n_br_pis_cst'] = self.l10n_br_cfop_id.l10n_br_pis_cst
            if self.l10n_br_operacao_id.l10n_br_pis_cst:
                values_to_update['l10n_br_pis_cst'] = self.l10n_br_operacao_id.l10n_br_pis_cst

            if values_to_update['l10n_br_pis_cst'] in ['50','51','52','53','54','55','56','60','61','62','63','64','65','66','67']:
                values_to_update['l10n_br_pis_base'] = 0.00
                l10n_br_pis_reducao_base = 0.00
                if self.l10n_br_operacao_id.l10n_br_pis_reducao_base > 0.00:
                    l10n_br_pis_reducao_base = self.l10n_br_operacao_id.l10n_br_pis_reducao_base
                values_to_update['l10n_br_pis_base'] = (self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor)
                values_to_update['l10n_br_pis_base'] = values_to_update['l10n_br_pis_base'] * (1.00 - (l10n_br_pis_reducao_base/100.00))

                values_to_update['l10n_br_pis_aliquota'] = 0.00
                if self.l10n_br_operacao_id.l10n_br_pis_cst:
                    values_to_update['l10n_br_pis_aliquota'] = self.l10n_br_operacao_id.l10n_br_pis_aliquota

                values_to_update['l10n_br_pis_valor'] = round(values_to_update['l10n_br_pis_base'] * values_to_update['l10n_br_pis_aliquota'] / 100.00, 2)
                values_to_update['l10n_br_pis_valor_isento'] = 0.00
                values_to_update['l10n_br_pis_valor_outros'] = 0.00
            
            self.update(values_to_update)

            ##################
            ##### COFINS #####
            ##################
            values_to_update = {}

            values_to_update['l10n_br_cofins_cst'] = False
            values_to_update['l10n_br_cofins_base'] = False
            values_to_update['l10n_br_cofins_aliquota'] = False
            values_to_update['l10n_br_cofins_valor'] = False
            values_to_update['l10n_br_cofins_valor_isento'] = False
            values_to_update['l10n_br_cofins_valor_outros'] = False

            if self.l10n_br_cfop_id.l10n_br_cofins_cst:
                values_to_update['l10n_br_cofins_cst'] = self.l10n_br_cfop_id.l10n_br_cofins_cst
            if self.l10n_br_operacao_id.l10n_br_cofins_cst:
                values_to_update['l10n_br_cofins_cst'] = self.l10n_br_operacao_id.l10n_br_cofins_cst

            if values_to_update['l10n_br_cofins_cst'] in ['50','51','52','53','54','55','56','60','61','62','63','64','65','66','67']:
                values_to_update['l10n_br_cofins_base'] = 0.00
                l10n_br_cofins_reducao_base = 0.00
                if self.l10n_br_operacao_id.l10n_br_cofins_reducao_base > 0.00:
                    l10n_br_cofins_reducao_base = self.l10n_br_operacao_id.l10n_br_cofins_reducao_base
                values_to_update['l10n_br_cofins_base'] = (self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor)
                values_to_update['l10n_br_cofins_base'] = values_to_update['l10n_br_cofins_base'] * (1.00 - (l10n_br_cofins_reducao_base/100.00))

                values_to_update['l10n_br_cofins_aliquota'] = 0.00
                if self.l10n_br_operacao_id.l10n_br_cofins_cst:
                    values_to_update['l10n_br_cofins_aliquota'] = self.l10n_br_operacao_id.l10n_br_cofins_aliquota

                values_to_update['l10n_br_cofins_valor'] = round(values_to_update['l10n_br_cofins_base'] * values_to_update['l10n_br_cofins_aliquota'] / 100.00, 2)
                values_to_update['l10n_br_cofins_valor_isento'] = 0.00
                values_to_update['l10n_br_cofins_valor_outros'] = 0.00
            
            self.update(values_to_update)

            ####################
            ##### IRPJ RET #####
            ####################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_irpj_ret_aliquota != 0.00:
                values_to_update['l10n_br_irpj_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_irpj_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_irpj_ret_aliquota
                values_to_update['l10n_br_irpj_ret_valor'] = round(values_to_update['l10n_br_irpj_ret_base'] * values_to_update['l10n_br_irpj_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

            ####################
            ##### INSS RET #####
            ####################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_inss_ret_aliquota != 0.00:
                values_to_update['l10n_br_inss_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_inss_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_inss_ret_aliquota
                values_to_update['l10n_br_inss_ret_valor'] = round(values_to_update['l10n_br_inss_ret_base'] * values_to_update['l10n_br_inss_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

            ####################
            ##### ISS RET #####
            ####################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_iss_ret_aliquota != 0.00:
                values_to_update['l10n_br_iss_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_iss_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_iss_ret_aliquota
                values_to_update['l10n_br_iss_ret_valor'] = round(values_to_update['l10n_br_iss_ret_base'] * values_to_update['l10n_br_iss_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

            ####################
            ##### CSLL RET #####
            ####################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_csll_ret_aliquota != 0.00:
                values_to_update['l10n_br_csll_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_csll_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_csll_ret_aliquota
                values_to_update['l10n_br_csll_ret_valor'] = round(values_to_update['l10n_br_csll_ret_base'] * values_to_update['l10n_br_csll_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

            ###################
            ##### PIS RET #####
            ###################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_pis_ret_aliquota != 0.00:
                values_to_update['l10n_br_pis_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_pis_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_pis_ret_aliquota
                values_to_update['l10n_br_pis_ret_valor'] = round(values_to_update['l10n_br_pis_ret_base'] * values_to_update['l10n_br_pis_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

            ######################
            ##### COFINS RET #####
            ######################
            values_to_update = {}

            if self.l10n_br_operacao_id.l10n_br_cofins_ret_aliquota != 0.00:
                values_to_update['l10n_br_cofins_ret_base'] = self.l10n_br_total_nfe
                values_to_update['l10n_br_cofins_ret_aliquota'] = self.l10n_br_operacao_id.l10n_br_cofins_ret_aliquota
                values_to_update['l10n_br_cofins_ret_valor'] = round(values_to_update['l10n_br_cofins_ret_base'] * values_to_update['l10n_br_cofins_ret_aliquota'] / 100.00, 2)

            self.update(values_to_update)

        ###########################
        ##### IMPOSTOS TAX_ID #####
        ###########################

        self.l10n_br_compute_tax_id()

    @api.depends('l10n_br_icms_valor','l10n_br_icmsst_valor','l10n_br_icmsst_valor_outros','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias','l10n_br_ipi_valor','l10n_br_ipi_valor_isento','l10n_br_ipi_valor_outros','price_unit','product_qty',
                 'l10n_br_icmsst_substituto_valor', 'l10n_br_icmsst_substituto_valor_outros', 'l10n_br_icmsst_retido_valor', 'l10n_br_icmsst_retido_valor_outros',
                 'l10n_br_pis_valor','l10n_br_cofins_valor','l10n_br_ii_valor','l10n_br_ii_valor_aduaneira','l10n_br_csll_ret_valor','l10n_br_irpj_ret_valor','l10n_br_inss_ret_valor','l10n_br_iss_ret_valor','l10n_br_pis_ret_valor','l10n_br_cofins_ret_valor')
    def _l10n_br_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for line in self:

            price_unit_discount = line.price_unit - line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            l10n_br_desc_valor = round(price_unit_discount * line.product_qty,2)

            l10n_br_prod_valor = round(line.price_unit * line.product_qty,2)

            l10n_br_total_nfe = l10n_br_prod_valor - l10n_br_desc_valor + line.l10n_br_icmsst_valor + line.l10n_br_icmsst_valor_outros + line.l10n_br_frete + line.l10n_br_seguro + line.l10n_br_despesas_acessorias + line.l10n_br_ipi_valor + line.l10n_br_ipi_valor_isento + line.l10n_br_ipi_valor_outros + line.l10n_br_ii_valor + line.l10n_br_ii_valor_aduaneira
            if line.order_id.l10n_br_tipo_pedido == 'importacao':
                l10n_br_total_nfe += line.l10n_br_pis_valor + line.l10n_br_cofins_valor
            l10n_br_total_tributos = line.l10n_br_icms_valor + line.l10n_br_icmsst_valor + line.l10n_br_ipi_valor + line.l10n_br_pis_valor + line.l10n_br_cofins_valor + line.l10n_br_ii_valor + line.l10n_br_ii_valor_aduaneira

            line.update({
                'l10n_br_desc_valor': l10n_br_desc_valor,
                'l10n_br_prod_valor': l10n_br_prod_valor,
                'l10n_br_total_nfe': l10n_br_total_nfe,
                'l10n_br_total_tributos': l10n_br_total_tributos,
            })

    def _get_computed_account(self):
        self.ensure_one()

        if not self.product_id:
            return

        fiscal_position = self.order_id.fiscal_position_id
        accounts = self.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        return accounts['expense']

    def _prepare_account_move_line(self, move):
        
        invoice_line_vals = super(PurchaseOrderLine, self)._prepare_account_move_line(move)

        if self.company_id.country_id != self.env.ref('base.br'):
            return invoice_line_vals

        if 'quantity' in invoice_line_vals and invoice_line_vals['quantity'] == 0.00:
            invoice_line_vals['quantity'] = self.product_qty
        
        invoice_line_vals['dfe_line_id'] = self.dfe_line_id.id
        invoice_line_vals['account_id'] = self.account_id.id
        invoice_line_vals['l10n_br_operacao_id'] = self.l10n_br_operacao_id.id
        invoice_line_vals['l10n_br_cfop_id'] = self.l10n_br_cfop_id.id
        invoice_line_vals['l10n_br_frete'] = self.l10n_br_frete
        invoice_line_vals['l10n_br_seguro'] = self.l10n_br_seguro
        invoice_line_vals['l10n_br_despesas_acessorias'] = self.l10n_br_despesas_acessorias
        invoice_line_vals['l10n_br_informacao_adicional'] = self.l10n_br_informacao_adicional
        invoice_line_vals['l10n_br_compra_indcom'] = self.l10n_br_compra_indcom
        invoice_line_vals['l10n_br_mensagem_fiscal_ids'] = [(6,0,self.l10n_br_mensagem_fiscal_ids.ids)]
        invoice_line_vals['l10n_br_imposto_auto'] = self.l10n_br_imposto_auto
        invoice_line_vals['l10n_br_calcular_imposto'] = self.l10n_br_calcular_imposto
        invoice_line_vals['l10n_br_icms_modalidade_base'] = self.l10n_br_icms_modalidade_base
        invoice_line_vals['l10n_br_icms_reducao_base'] = self.l10n_br_icms_reducao_base
        invoice_line_vals['l10n_br_icms_diferido_valor_operacao'] = self.l10n_br_icms_diferido_valor_operacao
        invoice_line_vals['l10n_br_icms_diferido_aliquota'] = self.l10n_br_icms_diferido_aliquota
        invoice_line_vals['l10n_br_icms_diferido_valor'] = self.l10n_br_icms_diferido_valor
        invoice_line_vals['l10n_br_icms_cst'] = self.l10n_br_icms_cst
        invoice_line_vals['l10n_br_icms_base'] = self.l10n_br_icms_base
        invoice_line_vals['l10n_br_icms_aliquota'] = self.l10n_br_icms_aliquota
        invoice_line_vals['l10n_br_icms_valor'] = self.l10n_br_icms_valor
        invoice_line_vals['l10n_br_icms_valor_isento'] = self.l10n_br_icms_valor_isento
        invoice_line_vals['l10n_br_icms_valor_outros'] = self.l10n_br_icms_valor_outros
        invoice_line_vals['l10n_br_icms_valor_desonerado'] = self.l10n_br_icms_valor_desonerado
        invoice_line_vals['l10n_br_icms_motivo_desonerado'] = self.l10n_br_icms_motivo_desonerado
        invoice_line_vals['l10n_br_codigo_beneficio'] = self.l10n_br_codigo_beneficio
        invoice_line_vals['l10n_br_icms_dest_base'] = self.l10n_br_icms_dest_base
        invoice_line_vals['l10n_br_icms_dest_aliquota'] = self.l10n_br_icms_dest_aliquota
        invoice_line_vals['l10n_br_icms_inter_aliquota'] = self.l10n_br_icms_inter_aliquota
        invoice_line_vals['l10n_br_icms_inter_participacao'] = self.l10n_br_icms_inter_participacao
        invoice_line_vals['l10n_br_icms_dest_valor'] = self.l10n_br_icms_dest_valor
        invoice_line_vals['l10n_br_icms_remet_valor'] = self.l10n_br_icms_remet_valor
        invoice_line_vals['l10n_br_icms_credito_aliquota'] = self.l10n_br_icms_credito_aliquota
        invoice_line_vals['l10n_br_icms_credito_valor'] = self.l10n_br_icms_credito_valor
        invoice_line_vals['l10n_br_fcp_base'] = self.l10n_br_fcp_base
        invoice_line_vals['l10n_br_fcp_dest_aliquota'] = self.l10n_br_fcp_dest_aliquota
        invoice_line_vals['l10n_br_fcp_dest_valor'] = self.l10n_br_fcp_dest_valor
        invoice_line_vals['l10n_br_fcp_st_base'] = self.l10n_br_fcp_st_base
        invoice_line_vals['l10n_br_fcp_st_aliquota'] = self.l10n_br_fcp_st_aliquota
        invoice_line_vals['l10n_br_fcp_st_valor'] = self.l10n_br_fcp_st_valor
        invoice_line_vals['l10n_br_fcp_st_ant_base'] = self.l10n_br_fcp_st_ant_base
        invoice_line_vals['l10n_br_fcp_st_ant_aliquota'] = self.l10n_br_fcp_st_ant_aliquota
        invoice_line_vals['l10n_br_fcp_st_ant_valor'] = self.l10n_br_fcp_st_ant_valor
        invoice_line_vals['l10n_br_icmsst_modalidade_base'] = self.l10n_br_icmsst_modalidade_base
        invoice_line_vals['l10n_br_icmsst_reducao_base'] = self.l10n_br_icmsst_reducao_base
        invoice_line_vals['l10n_br_icmsst_mva'] = self.l10n_br_icmsst_mva
        invoice_line_vals['l10n_br_icmsst_base'] = self.l10n_br_icmsst_base
        invoice_line_vals['l10n_br_icmsst_aliquota'] = self.l10n_br_icmsst_aliquota
        invoice_line_vals['l10n_br_icmsst_valor'] = self.l10n_br_icmsst_valor
        invoice_line_vals['l10n_br_icmsst_valor_outros'] = self.l10n_br_icmsst_valor_outros
        invoice_line_vals['l10n_br_icmsst_retido_base'] = self.l10n_br_icmsst_retido_base
        invoice_line_vals['l10n_br_icmsst_retido_aliquota'] = self.l10n_br_icmsst_retido_aliquota
        invoice_line_vals['l10n_br_icmsst_substituto_valor'] = self.l10n_br_icmsst_substituto_valor
        invoice_line_vals['l10n_br_icmsst_substituto_valor_outros'] = self.l10n_br_icmsst_substituto_valor_outros
        invoice_line_vals['l10n_br_icmsst_retido_valor'] = self.l10n_br_icmsst_retido_valor
        invoice_line_vals['l10n_br_icmsst_retido_valor_outros'] = self.l10n_br_icmsst_retido_valor_outros
        invoice_line_vals['l10n_br_icmsst_base_propria_aliquota'] = self.l10n_br_icmsst_base_propria_aliquota
        invoice_line_vals['l10n_br_icmsst_uf'] = self.l10n_br_icmsst_uf
        invoice_line_vals['l10n_br_ipi_cst'] = self.l10n_br_ipi_cst
        invoice_line_vals['l10n_br_ipi_base'] = self.l10n_br_ipi_base
        invoice_line_vals['l10n_br_ipi_aliquota'] = self.l10n_br_ipi_aliquota
        invoice_line_vals['l10n_br_ipi_valor'] = self.l10n_br_ipi_valor
        invoice_line_vals['l10n_br_ipi_valor_isento'] = self.l10n_br_ipi_valor_isento
        invoice_line_vals['l10n_br_ipi_valor_outros'] = self.l10n_br_ipi_valor_outros
        invoice_line_vals['l10n_br_ipi_cnpj'] = self.l10n_br_ipi_cnpj
        invoice_line_vals['l10n_br_ipi_selo_codigo'] = self.l10n_br_ipi_selo_codigo
        invoice_line_vals['l10n_br_ipi_selo_quantidade'] = self.l10n_br_ipi_selo_quantidade
        invoice_line_vals['l10n_br_ipi_enq'] = self.l10n_br_ipi_enq
        invoice_line_vals['l10n_br_pis_cst'] = self.l10n_br_pis_cst
        invoice_line_vals['l10n_br_pis_base'] = self.l10n_br_pis_base
        invoice_line_vals['l10n_br_pis_aliquota'] = self.l10n_br_pis_aliquota
        invoice_line_vals['l10n_br_pis_valor'] = self.l10n_br_pis_valor
        invoice_line_vals['l10n_br_pis_valor_isento'] = self.l10n_br_pis_valor_isento
        invoice_line_vals['l10n_br_pis_valor_outros'] = self.l10n_br_pis_valor_outros
        invoice_line_vals['l10n_br_cofins_cst'] = self.l10n_br_cofins_cst
        invoice_line_vals['l10n_br_cofins_base'] = self.l10n_br_cofins_base
        invoice_line_vals['l10n_br_cofins_aliquota'] = self.l10n_br_cofins_aliquota
        invoice_line_vals['l10n_br_cofins_valor'] = self.l10n_br_cofins_valor
        invoice_line_vals['l10n_br_cofins_valor_isento'] = self.l10n_br_cofins_valor_isento
        invoice_line_vals['l10n_br_cofins_valor_outros'] = self.l10n_br_cofins_valor_outros
        invoice_line_vals['l10n_br_ii_valor'] = self.l10n_br_ii_valor
        invoice_line_vals['l10n_br_ii_valor_aduaneira'] = self.l10n_br_ii_valor_aduaneira
        invoice_line_vals['l10n_br_csll_ret_valor'] = self.l10n_br_csll_ret_valor
        invoice_line_vals['l10n_br_irpj_ret_valor'] = self.l10n_br_irpj_ret_valor
        invoice_line_vals['l10n_br_inss_ret_valor'] = self.l10n_br_inss_ret_valor
        invoice_line_vals['l10n_br_iss_ret_valor'] = self.l10n_br_iss_ret_valor
        invoice_line_vals['l10n_br_pis_ret_valor'] = self.l10n_br_pis_ret_valor
        invoice_line_vals['l10n_br_cofins_ret_valor'] = self.l10n_br_cofins_ret_valor
        invoice_line_vals['l10n_br_di_adicao_id'] = self.l10n_br_di_adicao_id.id

        return invoice_line_vals

class L10nBrOperacao(models.Model):
    _inherit = 'l10n_br_ciel_it_account.operacao'

    l10n_br_tipo_pedido_entrada = fields.Selection( TIPO_PEDIDO_ENTRADA, string='Tipo de Pedido (Entrada)' )

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_price_unit(self):

        price_unit = super(StockMove, self)._get_price_unit()

        if self.company_id.country_id != self.env.ref('base.br'):
            return price_unit

        if self.purchase_line_id:
            line = self.purchase_line_id
            if line.company_id.l10n_br_incidencia_cumulativa == '1' or line.order_id.company_id.l10n_br_regime_tributario != '3':
                new_price_unit = (line.l10n_br_total_nfe - line.l10n_br_icms_valor - line.l10n_br_ipi_valor - line.l10n_br_ipi_valor_isento - line.l10n_br_ipi_valor_outros) / (line.product_qty or 1.00)
            else:
                new_price_unit = (line.l10n_br_total_nfe - line.l10n_br_ipi_valor - line.l10n_br_ipi_valor_isento - line.l10n_br_ipi_valor_outros) / (line.product_qty or 1.00)

            price_unit = price_unit > 0.00 and new_price_unit or -new_price_unit
        return price_unit
