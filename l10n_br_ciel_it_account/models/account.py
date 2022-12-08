# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *
from odoo.addons.l10n_br_ciel_it_account.models.purchase import *
from odoo.addons.l10n_br_ciel_it_account.models.account_payment_term import *
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from pycpfcnpj import cpf, cnpj, compatible

import urllib.parse

import pytz
from datetime import datetime, timedelta, time as dtime
import time

import json
import requests
from requests.auth import HTTPBasicAuth
import base64

import zipfile
import io

import xml.etree.ElementTree as ET
import xml.dom.minidom

import sys
import logging
_logger = logging.getLogger(__name__)

VIA_TRANSPORTE_DI = [
    ('1','Marítima'),
    ('2','Fluvial'),
    ('3','Lacustre'),
    ('4','Aérea'),
    ('5','Postal'),
    ('6','Ferroviária'),
    ('7','Rodoviária;'),
    ('8','Conduto / Rede Transmissão'),
    ('9','Meios Próprios'),
    ('10','Entrada / Saída ficta'),
    ('11','Courier'),
    ('12','Handcarry'),
]

TIPO_IMPORTACAO = [
    ('1','Importação por conta própria'),
    ('2','Importação por conta e ordem'),
    ('3','Importação por encomenda'),
]

TIPO_DESPESA_IMPORTACAO = [
    ('frete','Frete'),
    ('seguro','Seguro'),
    ('adicional','Despesa Adicional'),
    ('aduaneira','Despesa Aduaneira'),
]

SITUACAO_NF = [
    ('rascunho', 'Rascunho'),
    ('autorizado', 'Autorizado'),
    ('excecao_autorizado', 'Exceção'),
    ('cce', 'Carta de Correção'),
    ('excecao_cce', 'Exceção'),
    ('cancelado', 'Cancelado'),
    ('excecao_cancelado', 'Exceção'),
]

TIPO_NF = {
    'out_invoice': 1,
    'in_refund': 1,
    'out_refund': 0,
    'in_invoice': 0,
}

TIPO_NF_OPERACAO = {
    'out_invoice': 'saida',
    'in_refund': 'saida',
    'out_refund': 'entrada',
    'in_invoice': 'entrada',
}

SITUACAO_COBRANCA = [
    ('SALVO', 'Salvo'),
    ('PENDENTE_RETENTATIVA', 'Pendente'),
    ('FALHA', 'Falha'),
    ('EMITIDO', 'Emitido'),
    ('REJEITADO', 'Rejeitado'),
    ('REGISTRADO', 'Registrado'),
    ('LIQUIDADO', 'Liquidado'),
    ('BAIXADO', 'Baixado'),
]

COBRANCA_ESPECIE = [
    ('01', 'DM - Duplicata Mercantil'),
    ('25', 'DMI - Duplicata Mercantil por Indicação'),
]

TIPO_TRANSMISSAO = [
    ('webservice', 'Webservice / Ecommerce'),
    ('automatico', 'Remessa Automática (VAN)'),
    ('manual', 'Remessa Manual (Internet Bank)'),
]

COBRANCA_BAIXA = [
    ('1', '1 - Baixar / Devolver'),
    ('2', '2 - Não baixar / Não Devolver'),
    ('3', '3 - Cancelar prazo para baixa / Devolução'),
]

COBRANCA_MULTA = [
    ('0', '0 - Não registra a multa'),
    ('1', '1 - Valor em reais fixo'),
    ('2', '2 - Valor em percentual'),
]

COBRANCA_JUROS = [
    ('1', '1 - Valor por dia'),
    ('2', '2 - Taxa Mensal'),
    ('3', '3 - Isento'),
]

COBRANCA_PROTESTO = [
    ('1', '1 - Protestar Dias Corridos.'),
    ('2', '2 - Protestar Dias Úteis.'),
    ('3', '3 - Não Protestar.'),
    ('4', '4 - Protestar Fim Falimentar - Dias Úteis.'),
    ('5', '5 - Protestar Fim Falimentar - Dias Corridos.'),
    ('8', '8 - Negativação sem Protesto.'),
    ('9', '9 - Cancelamento Protesto Automático (somente válido p/ Código Movimento Remessa = 31)'),
]

MDFE_STATUS = [
    ('01', 'Rascunho'),
    ('02', 'Emitido'),
    ('03', 'Cancelado'),
    ('04', 'Finalizado'),
]

DFE_STATUS = [
    ('01', 'Rascunho'),
    ('02', 'Sincronizado'),
    ('03', 'Ciência'),
    ('04', 'PO'),
    ('05', 'Rateio'),
]

DI_STATUS = [
    ('01', 'Rascunho'),
    ('02', 'Calculado'),
    ('03', 'Finalizado'),
]

TIPO_RODADO = [
    ('01', 'Truck'),
    ('02', 'Toco'),
    ('03', 'Cavalo Mecânico'),
    ('04', 'VAN'),
    ('05', 'Utilitário'),
    ('06', 'Outros'),
]

TIPO_CARROCERIA = [
    ('00', 'Não aplicável'),
    ('01', 'Aberta'),
    ('02', 'Fechada/Baú'),
    ('03', 'Granelera'),
    ('04', 'Porta Container'),
    ('05', 'Sider'),
]

VERSAO_MDFE = [
    ('3.00','MDFE 3.00'),
]

AMBIENTE_MDFE = [
    ('1','Produção'),
    ('2','Homologação'),
]

EMITENTE_MDFE = [
    ('1','Prestador de serviço de transporte'),
    ('2','Transportador de Carga Própria'),
]

MODAL_MDFE = [
    ('1', 'Rodoviário'),
    ('2', 'Aéreo'),
    ('3', 'Aquaviário'),
    ('4', 'Ferroviário'),
]

TIPO_EMISSAO_MDFE = [
    ('1','Normal'),
    ('2','Contingência'),
]

TIPO_DOCUMENTO_FISCAL = [
    ('NFS', 'Nota Fiscal de Serviços Instituída por Municípios'),
    ('NFSE', 'Nota Fiscal de Serviços Eletrônica - NFS-e'),
    ('01', 'Nota Fiscal'),
    ('1B', 'Nota Fiscal Avulsa'),
    ('02', 'Nota Fiscal de Venda a Consumidor'),
    ('2D', 'Cupom Fiscal'),
    ('2E', 'Cupom Fiscal Bilhete de Passagem'),
    ('04', 'Nota Fiscal de Produtor'),
    ('06', 'Nota Fiscal/Conta de Energia Elétrica'),
    ('07', 'Nota Fiscal de Serviço de Transporte'),
    ('08', 'Conhecimento de Transporte Rodoviário de Cargas'),
    ('8B', 'Conhecimento de Transporte de Cargas Avulso'),
    ('09', 'Conhecimento de Transporte Aquaviário de Cargas'),
    ('10', 'Conhecimento Aéreo'),
    ('11', 'Conhecimento de Transporte Ferroviário de Cargas'),
    ('13', 'Bilhete de Passagem Rodoviário'),
    ('14', 'Bilhete de Passagem Aquaviário'),
    ('15', 'Bilhete de Passagem e Nota de Bagagem'),
    ('16', 'Bilhete de Passagem Ferroviário'),
    ('18', 'Resumo de Movimento Diário'),
    ('21', 'Nota Fiscal de Serviço de Comunicação'),
    ('22', 'Nota Fiscal de Serviço de Telecomunicação'),
    ('26', 'Conhecimento de Transporte Multimodal de Cargas'),
    ('27', 'Nota Fiscal De Transporte Ferroviário De Carga'),
    ('28', 'Nota Fiscal/Conta de Fornecimento de Gás Canalizado'),
    ('29', 'Nota Fiscal/Conta de Fornecimento de Água Canalizada'),
    ('55', 'Nota Fiscal Eletrônica (NF-e)'),
    ('57', 'Conhecimento de Transporte Eletrônico (CT-e)'),
    ('59', 'Cupom Fiscal Eletrônico (CF-e-SAT)'),
    ('60', 'Cupom Fiscal Eletrônico (CF-e-ECF)'),
    ('63', 'Bilhete de Passagem Eletrônico (BP-e)'),
    ('65', 'Nota Fiscal Eletrônica ao Consumidor Final (NFC-e)'),
    ('67', 'Conhecimento de Transporte Eletrônico (CT-e OS)'),
]

TIPO_NF_STR = {
    'NFSE': 'NFS-e',
    '55': 'NF-e',
    '57': 'CT-e',
}

class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_contact_id = fields.Many2one(
        'res.partner', string='Contato', readonly=True,
        states={'draft': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

    invoice_date = fields.Date( string='Data de Emissão' )
    date = fields.Date( string='Data de Entrada/Saída' )

    l10n_br_numero_nf = fields.Integer( string='Número da Nota Fiscal', copy=False )
    l10n_br_numero_nfse = fields.Char( string='Número da Nota Fiscal de Serviço', copy=False )
    l10n_br_numero_rps = fields.Integer( string='Número RPS', copy=False )
    l10n_br_serie_nf = fields.Char( string='Série da Nota Fiscal', copy=False )
    l10n_br_tipo_documento = fields.Selection( TIPO_DOCUMENTO_FISCAL, string='Tipo Documento Fiscal', default='55', copy=False, check_company=True )
    l10n_br_chave_nf = fields.Char( string='Chave da Nota Fiscal', copy=False )
    l10n_br_cstat_nf = fields.Char( string='Status da Nota Fiscal', copy=False )
    l10n_br_xmotivo_nf = fields.Char( string='Situação da Nota Fiscal', copy=False )
    l10n_br_sequencia_evento = fields.Integer( string='Sequencia Evento NF-e', copy=False )
    simples_nacional = fields.Boolean( string='Emitente Simples Nacional' )
    l10n_br_correcao = fields.Text( string='Correção', copy=False )
    l10n_br_motivo = fields.Text( string='Motivo Cancelamento', copy=False )
    l10n_br_situacao_nf = fields.Selection( SITUACAO_NF, string='Situação NF-e', default='rascunho', copy=False )
    l10n_br_handle_nfse = fields.Integer(string='Handle da Nota Fiscal de Serviço')

    dfe_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe', copy=False, string='Documento', check_company=True )
    l10n_br_carrier_id = fields.Many2one("delivery.carrier", string="Carrier", check_company=True, readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_peso_liquido = fields.Float( string='Peso Líquido', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_peso_bruto = fields.Float( string='Peso Bruto', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_volumes = fields.Integer( string='Volumes', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_especie = fields.Char( string='Espécie', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_veiculo_placa = fields.Char( string='Placa', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_veiculo_uf = fields.Char( string='UF', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_veiculo_rntc = fields.Char( string='RNTC', readonly=True, states={'draft': [('readonly', False)]} )

    l10n_br_uf_saida_pais = fields.Char( string='Sigla UF de Saída', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_local_despacho = fields.Char( string='Local de despacho', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_local_embarque = fields.Char( string='Local de embarque', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_municipio_inicio_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município de Origem', ondelete='restrict')
    l10n_br_municipio_fim_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município de Destino', ondelete='restrict')

    l10n_br_xml_aut_nfe = fields.Binary( string="XML NF-e", copy=False )
    l10n_br_xml_aut_nfe_fname = fields.Char( string="Arquivo XML NF-e", compute="_get_l10n_br_xml_aut_nfe_fname" )
    l10n_br_pdf_aut_nfe = fields.Binary( string="DANFE NF-e", copy=False )
    l10n_br_pdf_aut_nfe_fname = fields.Char( string="Arquivo DANFE NF-e", compute="_get_l10n_br_pdf_aut_nfe_fname" )

    l10n_br_xml_cce_nfe = fields.Binary( string="XML CC-e", copy=False )
    l10n_br_xml_cce_nfe_fname = fields.Char( string="Arquivo XML CC-e", compute="_get_l10n_br_xml_cce_nfe_fname" )
    l10n_br_pdf_cce_nfe = fields.Binary( string="DANFE CC-e", copy=False )
    l10n_br_pdf_cce_nfe_fname = fields.Char( string="Arquivo DANFE CC-e", compute="_get_l10n_br_pdf_cce_nfe_fname" )

    l10n_br_xml_can_nfe = fields.Binary( string="XML NF-e Cancelamento", copy=False )
    l10n_br_xml_can_nfe_fname = fields.Char( string="Arquivo XML NF-e Cancelamento", compute="_get_l10n_br_xml_can_nfe_fname" )
    l10n_br_pdf_can_nfe = fields.Binary( string="DANFE NF-e Cancelamento", copy=False )
    l10n_br_pdf_can_nfe_fname = fields.Char( string="Arquivo DANFE NF-e Cancelamento", compute="_get_l10n_br_pdf_can_nfe_fname" )

    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', compute="_get_l10n_br_operacao_id", check_company=True )
    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_SAIDA, string='Tipo de Pedido (saída)', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_tipo_pedido_entrada = fields.Selection( TIPO_PEDIDO_ENTRADA, string='Tipo de Pedido (entrada)', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_operacao_consumidor = fields.Selection( OPERACAO_CONSUMIDOR, string='Operação Consumidor Final', default='0', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_indicador_presenca = fields.Selection( INDICADOR_PRESENCA, string='Indicador Presença', default='0', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )
    invoice_payment_term_id = fields.Many2one( readonly=True, states={'draft': [('readonly', False)]} )
    payment_acquirer_id = fields.Many2one( 'payment.acquirer', string='Forma de Pagamento', readonly=True, states={'draft': [('readonly', False)]}, domain=[('state', '=', 'enabled')] )

    invoice_incoterm_id = fields.Many2one( string='Tipo de Frete', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_pedido_compra = fields.Char( string='Pedido de Compra do Cliente', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_item_pedido_compra = fields.Char( string='Item Pedido de Compra do Cliente', readonly=True, states={'draft': [('readonly', False)]} )

    l10n_br_informacao_fiscal = fields.Text( string='Informação Fiscal', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_informacao_complementar = fields.Text( string='Informação Complementar', readonly=True, states={'draft': [('readonly', False)]} )

    l10n_br_imposto_auto = fields.Boolean( string='Calcular Impostos Automaticamente', default=True, readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_calcular_imposto = fields.Boolean( string='Calcular Impostos', readonly=True, states={'draft': [('readonly', False)]} )

    l10n_br_icms_base = fields.Float( string='Total da Base de Cálculo do ICMS', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_icms_valor = fields.Float( string='Total do ICMS (Tributável)', readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
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
    l10n_br_frete = fields.Float( string='Total do Frete', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_seguro = fields.Float( string='Total do Seguro', readonly=True, states={'draft': [('readonly', False)]} )
    l10n_br_despesas_acessorias = fields.Float( string='Total da Despesas Acessórias', readonly=True, states={'draft': [('readonly', False)]} )
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

    l10n_br_iss_valor = fields.Float( string='Total do ISS', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_irpj_valor = fields.Float( string='Total do IRPJ', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_csll_valor = fields.Float( string='Total do CSLL', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_irpj_ret_valor = fields.Float( string='Valor do IRPJ Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_inss_ret_valor = fields.Float( string='Valor do INSS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_iss_ret_valor = fields.Float( string='Valor do ISS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_csll_ret_valor = fields.Float( string='Valor do CSLL Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_pis_ret_valor = fields.Float( string='Valor do PIS Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_cofins_ret_valor = fields.Float( string='Valor do Cofins Retido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_total_nfe = fields.Float( string='Total do Pedido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_tributos = fields.Float( string='Total dos Tributos', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )

    l10n_br_nfe_emails = fields.Char( string="Email XML NF-e", compute="_get_l10n_br_nfe_emails" )

    referencia_ids = fields.One2many('l10n_br_ciel_it_account.account.move.referencia', 'move_id', string='NF-e referência', copy=False, readonly=True, states={'draft': [('readonly', False)]}, check_company=True)

    payment_line_ids = fields.Many2many('account.move.line', string='Payment lines', compute="_compute_get_payment_lines" )

    l10n_br_iss_municipio_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município de Incidência do ISS', ondelete='restrict')


    def post(self):
        res = super(AccountMove, self).post()
        for invoice in self.filtered(lambda invoice: invoice.partner_contact_id and invoice.partner_contact_id not in invoice.message_partner_ids):
            invoice.message_subscribe([invoice.partner_contact_id.id])
        return res

    @api.depends('line_ids','line_ids.account_id')
    def _compute_get_payment_lines(self):
        for record in self:
            record.payment_line_ids = record.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))

    def _reverse_moves(self, default_values_list=None, cancel=False):
    
        reverse_moves = super(AccountMove, self)._reverse_moves(default_values_list, cancel)

        if self.company_id.country_id == self.env.ref('base.br'):
            reverse_moves.with_context(update_tax=False).onchange_l10n_br_calcular_imposto()

            referencia_ids = []
            for move_id in self:
                referencia_values = { 'move_id': move_id.id, 'l10n_br_chave_nf': move_id.l10n_br_chave_nf }
                referencia_ids.append((0,0,referencia_values))

            reverse_moves.write({
                'referencia_ids': referencia_ids
            })

        return reverse_moves    

    def l10n_br_map_account(self, account_id):

        if self.fiscal_position_id:
            return self.fiscal_position_id.map_account(account_id)
        return account_id

    def _recompute_tax_lines(self, recompute_tax_base_amount=False, tax_rep_lines_to_recompute=None):

        super(AccountMove, self)._recompute_tax_lines(recompute_tax_base_amount=recompute_tax_base_amount, tax_rep_lines_to_recompute=tax_rep_lines_to_recompute)
        if self.company_id.country_id == self.env.ref('base.br'):
            for line in self.line_ids.filtered('tax_repartition_line_id'):
                account_id = self.l10n_br_map_account(line.account_id)
                if account_id != line.account_id:
                    line.with_context(check_move_validity=False).write({'account_id': account_id.id})

    def _get_move_display_name(self, show_ref=False):

        result = super(AccountMove, self)._get_move_display_name(show_ref)
        move_display_name = ""
        if self.company_id.country_id == self.env.ref('base.br'):
            if self.l10n_br_tipo_documento in ['55','57','NFSE'] and self.l10n_br_numero_nf > 0:
                move_display_name = "%s: %s Série: %s - " % (TIPO_NF_STR[self.l10n_br_tipo_documento],str(self.l10n_br_numero_nf),self.l10n_br_serie_nf)
        return move_display_name + result

    def _onchange_invoice_date(self):
        if self.dfe_id:
            self.date = self.dfe_id.l10n_br_data_entrada
            self._onchange_currency()
        else:
            super(AccountMove, self)._onchange_invoice_date()

    @api.onchange('partner_id')
    def onchange_l10n_br_partner_id(self):
        for item in self:
            if item.partner_id:
                item.l10n_br_compra_indcom = item.partner_id.l10n_br_compra_indcom
                item.partner_contact_id = item.partner_id.child_ids[0].id if len(item.partner_id.child_ids) > 0 else item.partner_id.id
            else:
                item.partner_contact_id = False

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _l10n_br_onchange_purchase_auto_complete(self):
        if not self.purchase_id:
            return
        
        invoice_vals = self.purchase_id._prepare_invoice()
        self.update(invoice_vals)
        self.onchange_l10n_br_calcular_imposto()

    def _get_l10n_br_nfe_emails(self):
        for record in self:
            l10n_br_nfe_emails = (record.partner_id.email or "")
            l10n_br_nfe_emails += (", " if l10n_br_nfe_emails else "") + (record.partner_contact_id.email or "")
            for partner_id in record.partner_id.child_ids:
                if partner_id.l10n_br_receber_nfe and partner_id.email_formatted:
                    l10n_br_nfe_emails += (", " if l10n_br_nfe_emails else "") + partner_id.email
                    
            record.l10n_br_nfe_emails = l10n_br_nfe_emails

    @api.depends('invoice_line_ids.l10n_br_operacao_id')
    def _get_l10n_br_operacao_id(self):
        for record in self:
            invoice_line_ids = record.invoice_line_ids.filtered(lambda l: not l.display_type)
            record.l10n_br_operacao_id = invoice_line_ids[0].l10n_br_operacao_id if len(invoice_line_ids) > 0 else False

    def _get_l10n_br_xml_aut_nfe_fname(self):
        for record in self:
            record.l10n_br_xml_aut_nfe_fname = "%s-nfe.xml" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)

    def _get_l10n_br_pdf_aut_nfe_fname(self):
        for record in self:
            record.l10n_br_pdf_aut_nfe_fname = "%s-nfe.pdf" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)

    def _get_l10n_br_xml_cce_nfe_fname(self):
        for record in self:
            record.l10n_br_xml_cce_nfe_fname = "%s-cce.xml" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)

    def _get_l10n_br_pdf_cce_nfe_fname(self):
        for record in self:
            record.l10n_br_pdf_cce_nfe_fname = "%s-cce.pdf" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)
        
    def _get_l10n_br_xml_can_nfe_fname(self):
        for record in self:
            record.l10n_br_xml_can_nfe_fname = "%s-can.xml" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)
        
    def _get_l10n_br_pdf_can_nfe_fname(self):
        for record in self:
            record.l10n_br_pdf_can_nfe_fname = "%s-can.pdf" % (record.l10n_br_chave_nf or record.l10n_br_numero_nf or record.l10n_br_numero_nfse)

    def _gerar_cobranca_escritural(self):

        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_datetime(date):
            return datetime.strftime(date,'%d/%m/%Y')

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_decimal_2(valor):
            return "{:.2f}".format(valor).replace(".",",")

        def _format_cep(texto):
            return str(texto).replace("-","").replace(".","")

        self.ensure_one()
        invoice = self

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        boletos = []
        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity and not line.l10n_br_cobranca_idintegracao], key=lambda l: l[0].date_maturity)):

            if invoice_payment.date_maturity == invoice_payment.move_id.invoice_date:
                continue
            
            amount = invoice_payment.debit
            if len([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity and not line.l10n_br_cobranca_idintegracao]) == 1:
                amount = invoice.amount_residual
    
            if not invoice_payment.l10n_br_cobranca_situacao:
                boleto = {}

                boleto["CedenteContaNumero"] = l10n_br_cobranca_id.l10n_br_cedente_conta
                boleto["CedenteContaNumeroDV"] = l10n_br_cobranca_id.l10n_br_cedente_conta_digito
                boleto["CedenteConvenioNumero"] = l10n_br_cobranca_id.l10n_br_cedente_convenio
                boleto["CedenteContaCodigoBanco"] = l10n_br_cobranca_id.l10n_br_cedente_banco

                if invoice.partner_id.l10n_br_cnpj:
                    boleto["SacadoCPFCNPJ"] = _format_cnpj_cpf(invoice.partner_id.l10n_br_cnpj)
                elif invoice.partner_id.l10n_br_cpf:
                    boleto["SacadoCPFCNPJ"] = _format_cnpj_cpf(invoice.partner_id.l10n_br_cpf)

                boleto["SacadoEmail"] = invoice.partner_id.email or ""
                boleto["SacadoEnderecoNumero"] = invoice.partner_id.l10n_br_endereco_numero or ""
                boleto["SacadoEnderecoBairro"] = invoice.partner_id.l10n_br_endereco_bairro or ""
                boleto["SacadoEnderecoCEP"] = _format_cep(invoice.partner_id.zip)
                boleto["SacadoEnderecoCidade"] = invoice.partner_id.l10n_br_municipio_id.name
                boleto["SacadoEnderecoComplemento"] = invoice.partner_id.street2 or ""
                boleto["SacadoEnderecoLogradouro"] = invoice.partner_id.street
                boleto["SacadoEnderecoPais"] = invoice.partner_id.country_id.name
                boleto["SacadoEnderecoUF"] = invoice.partner_id.state_id.code
                boleto["SacadoNome"] = invoice.partner_id.l10n_br_razao_social
                boleto["SacadoTelefone"] = _format_fone(invoice.partner_id.phone or "")

                invoice_date_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
                boleto["TituloDataEmissao"] = _format_datetime(invoice_date_br)

                boleto["TituloDataVencimento"] = _format_datetime(invoice_payment.date_maturity)
                boleto["TituloNossoNumero"] = invoice_payment.l10n_br_cobranca_nossonumero
                boleto["TituloAceite"] = "N"
                boleto["TituloNumeroDocumento"] = "%s/%s" % (invoice.l10n_br_numero_nf, str(invoice_payment.l10n_br_cobranca_parcela).zfill(3))
                boleto["TituloDocEspecie"] = l10n_br_cobranca_id.l10n_br_especie
                boleto["TituloValor"] = _format_decimal_2(amount)

                mensagens = []
                if l10n_br_cobranca_id.l10n_br_codigo_juros:
                    boleto["TituloCodigoJuros"] = l10n_br_cobranca_id.l10n_br_codigo_juros
                    if l10n_br_cobranca_id.l10n_br_codigo_juros != "3":
                        boleto["TituloDataJuros"] = _format_datetime(invoice_payment.date_maturity+timedelta(days=1))
                        if l10n_br_cobranca_id.l10n_br_codigo_juros == "1":
                            juros_por_dia = amount * l10n_br_cobranca_id.l10n_br_percentual_juros / 100.00 / 30.00
                            juros_por_dia = juros_por_dia if juros_por_dia > 0.01 else 0.01
                            boleto["TituloValorJuros"] = _format_decimal_2(juros_por_dia)
                            mensagens.append("APOS O VENCIMENTO COBRAR MORA DE R$ %s AO DIA" % _format_decimal_2(juros_por_dia))
                        else:
                            boleto["TituloValorJurosTaxa"] = _format_decimal_2(l10n_br_cobranca_id.l10n_br_percentual_juros)
                            mensagens.append("APOS O VENCIMENTO COBRAR MORA DE %s%%" % _format_decimal_2(l10n_br_cobranca_id.l10n_br_percentual_juros))

                if l10n_br_cobranca_id.l10n_br_codigo_multa:
                    boleto["TituloCodigoMulta"] = l10n_br_cobranca_id.l10n_br_codigo_multa
                    if l10n_br_cobranca_id.l10n_br_codigo_multa != "0":
                        boleto["TituloDataMulta"] = _format_datetime(invoice_payment.date_maturity+timedelta(days=1))
                        if l10n_br_cobranca_id.l10n_br_codigo_multa == "1":
                            boleto["TituloValorMultaTaxa"] = _format_decimal_2(amount * l10n_br_cobranca_id.l10n_br_percentual_multa / 100.00)
                            mensagens.append("APOS %s MULTA DE R$ %s" % (_format_datetime(invoice_payment.date_maturity), _format_decimal_2(amount * l10n_br_cobranca_id.l10n_br_percentual_multa / 100.00)))
                        else:
                            boleto["TituloValorMultaTaxa"] = _format_decimal_2(l10n_br_cobranca_id.l10n_br_percentual_multa)
                            mensagens.append("APOS %s MULTA DE %s%%" % (_format_datetime(invoice_payment.date_maturity), _format_decimal_2(l10n_br_cobranca_id.l10n_br_percentual_multa)))

                if l10n_br_cobranca_id.l10n_br_codigo_baixa:
                    boleto["TituloCodBaixaDevolucao"] = l10n_br_cobranca_id.l10n_br_codigo_baixa
                    if l10n_br_cobranca_id.l10n_br_codigo_baixa == "1":
                        boleto["TituloPrazoBaixa"] = l10n_br_cobranca_id.l10n_br_dias_baixa
                        mensagens.append("DEVOLVER EM %s" % _format_datetime(invoice_payment.date_maturity+timedelta(l10n_br_cobranca_id.l10n_br_dias_baixa)))

                if l10n_br_cobranca_id.l10n_br_codigo_protesto:
                    boleto["TituloCodProtesto"] = l10n_br_cobranca_id.l10n_br_codigo_protesto
                    if l10n_br_cobranca_id.l10n_br_dias_protesto > 0:
                        boleto["TituloPrazoProtesto"] = l10n_br_cobranca_id.l10n_br_dias_protesto
                        mensagens.append("PROTESTAR %s DIAS APOS VENCIMENTO" % str(l10n_br_cobranca_id.l10n_br_dias_protesto))

                boleto["TituloLocalPagamento"] = l10n_br_cobranca_id.l10n_br_mensagem_pagamento

                if l10n_br_cobranca_id.l10n_br_mensagem_01:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_01)
                if l10n_br_cobranca_id.l10n_br_mensagem_02:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_02)
                if l10n_br_cobranca_id.l10n_br_mensagem_03:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_03)
                if l10n_br_cobranca_id.l10n_br_mensagem_04:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_04)
                if l10n_br_cobranca_id.l10n_br_mensagem_05:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_05)
                if l10n_br_cobranca_id.l10n_br_mensagem_06:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_06)
                if l10n_br_cobranca_id.l10n_br_mensagem_07:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_07)
                if l10n_br_cobranca_id.l10n_br_mensagem_08:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_08)
                if l10n_br_cobranca_id.l10n_br_mensagem_09:
                    mensagens.append(l10n_br_cobranca_id.l10n_br_mensagem_09)

                for idx, msg in enumerate(mensagens):
                    boleto["TituloMensagem" + str(idx+1).zfill(2)] = msg

                boletos.append(boleto)

        return boletos

    def action_gerar_boleto_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):

            if invoice_payment.date_maturity == invoice_payment.move_id.invoice_date:
                continue
            
            data_to_update = {}
            
            data_to_update["l10n_br_cobranca_parcela"] = nItem+1
            if l10n_br_cobranca_id and l10n_br_cobranca_id.l10n_br_nosso_numero_id:
                if not invoice_payment.l10n_br_cobranca_nossonumero:
                    data_to_update["l10n_br_cobranca_nossonumero"] = l10n_br_cobranca_id.l10n_br_nosso_numero_id.next_by_id()
                    
                if invoice_payment.l10n_br_cobranca_situacao == 'REJEITADO':
                    data_to_update["l10n_br_cobranca_nossonumero"] = l10n_br_cobranca_id.l10n_br_nosso_numero_id.next_by_id()
                    data_to_update["l10n_br_cobranca_situacao"] = False
                    data_to_update["l10n_br_cobranca_situacao_mensagem"] = False
                    data_to_update["l10n_br_cobranca_idintegracao"] = False
                    data_to_update["l10n_br_cobranca_protocolo"] = False
            
            invoice_payment.write(data_to_update)
            self.env.cr.commit()

        boletos = invoice._gerar_cobranca_escritural()
        payload = json.dumps(boletos)
        _logger.info(payload)
        
        if len(boletos) == 0:
            invoice.action_boleto_nfe_situacao()

        else:

            url = "%s/api/v1/boletos/lote" % (
                l10n_br_cobranca_id.l10n_br_url,
            )

            headers = {
                'Content-Type': "application/json",
                'cnpj-cedente': _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
                'cnpj-sh': "28653792000112",
                'token-sh': l10n_br_cobranca_id.l10n_br_token,
            }

            try:

                response = requests.post(url, headers=headers, data=payload)
                #_logger.info(response.text)
                json_data = json.loads(response.text)

                if '_status' in json_data:
                    if json_data['_status'] == 'sucesso':
                        for item in json_data['_dados']['_sucesso']:
                            for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
                                
                                if invoice_payment.l10n_br_cobranca_nossonumero == item["TituloNossoNumero"]:
                                    data_to_update = {}
                                    data_to_update["l10n_br_cobranca_transmissao"] = l10n_br_cobranca_id.l10n_br_transmissao
                                    data_to_update["l10n_br_cobranca_idintegracao"] = item["idintegracao"]
                                    data_to_update["l10n_br_cobranca_situacao"] = item["situacao"]
                                    invoice_payment.write(data_to_update)
                                    self.env.cr.commit()
                                    time.sleep(5)
                                    invoice.action_boleto_nfe_situacao()

                        for item in json_data['_dados']['_falha']:
                            for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
                                
                                if invoice_payment.l10n_br_cobranca_nossonumero == item["_dados"]["TituloNossoNumero"]:
                                    data_to_update = {}
                                    data_to_update["l10n_br_cobranca_idintegracao"] = item["_dados"]["idintegracao"]
                                    data_to_update["l10n_br_cobranca_situacao_mensagem"] = item["_erro"]["erros"]["boleto"]
                                    data_to_update["l10n_br_cobranca_situacao"] = item["_dados"]["situacao"]
                                    invoice_payment.write(data_to_update)
                                    self.env.cr.commit()

                        for item in json_data['_dados']['_falha']:
                            #_logger.info(item)
                            raise UserError(item['_erro']['erros'])
                    else:
                        raise UserError(json_data)
                else:
                    raise UserError(json_data)

            except Exception as e:
                invoice.message_post(body=e)
                raise UserError(e)

    def _check_boleto_naodisponivel(self):
        
        invoice_payments = self.env['account.move.line'].search([('l10n_br_cobranca_situacao','in',['SALVO','PENDENTE_RETENTATIVA','EMITIDO']),('account_internal_type','=','receivable'),('date_maturity','!=',False),('l10n_br_cobranca_idintegracao','!=',False)])
        invoices = invoice_payments.mapped('move_id')
        for invoice in invoices:
            invoice.action_boleto_nfe_situacao()

    def _check_boleto_liquidado(self):
        
        invoice_payments = self.env['account.move.line'].search([('l10n_br_cobranca_situacao','=','REGISTRADO'),('account_internal_type','=','receivable'),('date_maturity','!=',False),('l10n_br_cobranca_idintegracao','!=',False)])
        invoices = invoice_payments.mapped('move_id')
        for invoice in invoices:
            invoice.action_boleto_nfe_situacao()

    def action_boleto_nfe_situacao(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self

        ir_config = self.sudo().env['ir.config_parameter']
        if not ir_config.get_param('l10n_br_ciel_it_account.baixar_boleto_data_credito'):
            ir_config.sudo().set_param('l10n_br_ciel_it_account.baixar_boleto_data_credito', "0")
        l_baixa_data_credito = ir_config.get_param('l10n_br_ciel_it_account.baixar_boleto_data_credito') == "1"
        
        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        IdIntegracao = ""
        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
            if invoice_payment.l10n_br_cobranca_idintegracao and invoice_payment.l10n_br_cobranca_situacao not in ["REJEITADO","BAIXADO","LIQUIDADO"]:
                IdIntegracao += ("," if IdIntegracao else "") + invoice_payment.l10n_br_cobranca_idintegracao

        if IdIntegracao:
            url = "%s/api/v1/boletos?%s" % (
                l10n_br_cobranca_id.l10n_br_url,
                ("IdIntegracao=%s" % IdIntegracao)
            )

            headers = {
                'Content-Type': "application/json",
                'cnpj-cedente': _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
                'cnpj-sh': "28653792000112",
                'token-sh': l10n_br_cobranca_id.l10n_br_token,
            }

            try:

                response = requests.get(url, headers=headers)
                json_data = json.loads(response.text)
                
                if '_status' in json_data:
                    if json_data['_status'] == 'sucesso':
                        for item in json_data['_dados']:
                            for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
                                
                                if invoice_payment.l10n_br_cobranca_idintegracao == item["IdIntegracao"]:
    
                                    if item["situacao"] == "LIQUIDADO" and l_baixa_data_credito and (not item.get("PagamentoDataCredito") or not item["PagamentoDataCredito"] or item["PagamentoDataCredito"] == None):
                                        continue

                                    data_to_update = {}
                                    data_to_update["l10n_br_cobranca_situacao"] = item["situacao"]
                                    if "motivo" in item:
                                        data_to_update["l10n_br_cobranca_situacao_mensagem"] = item["motivo"]
                                    invoice_payment.write(data_to_update)
                                    self.env.cr.commit()
                                    
                                    if item["situacao"] == "LIQUIDADO":
                                        payment_values = self.env['account.payment'].with_context(active_ids=self.id, active_model='account.move', active_id=self.id).default_get({})
                                        payment_values["journal_id"] = l10n_br_cobranca_id.journal_id.id
                                        payment_values["payment_method_id"] = l10n_br_cobranca_id.journal_id.inbound_payment_method_ids[0].id
                                        amount = float(str(item["PagamentoValorPago"]).replace(".","").replace(",","."))
                                        if payment_values.get("amount") and amount > payment_values["amount"]:
                                            payment_values["payment_difference_handling"] = 'reconcile'
                                            payment_values["writeoff_account_id"] = l10n_br_cobranca_id.journal_id.writeoff_account_id.id
                                        payment_values["amount"] = amount
                                        
                                        if l_baixa_data_credito:
                                            payment_values["payment_date"] = datetime.strptime(str(item["PagamentoDataCredito"])[0:10],'%d/%m/%Y')

                                        self.env['account.payment'].create(payment_values).post()
                                        self.env.cr.commit()

                                        data_to_update = {}
                                        data_to_update["l10n_br_paga"] = True
                                        invoice_payment.write(data_to_update)

                                        self.env.cr.commit()

                                    if item["situacao"] in ["EMITIDO","REGISTRADO"]:
                                        invoice.action_boleto_nfe_imprimir()
    

            except Exception as e:
                invoice.message_post(body=e)
                raise UserError(e)

    def action_boleto_nfe_arquivo_remessa(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""
        
        for l10n_br_cobranca_id in self.env['l10n_br_ciel_it_account.tipo.cobranca'].search([]):
            IdIntegracao = []
            
            for invoice in self.env['account.move.line'].search([('l10n_br_cobranca_transmissao','=','automatico'), ('l10n_br_cobranca_arquivo_remessa','!=',True)]).mapped('move_id'):
                cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
                if not cobranca_id:
                    continue
                if cobranca_id != l10n_br_cobranca_id:
                    continue

                for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
                    if invoice_payment.l10n_br_cobranca_idintegracao and invoice_payment.l10n_br_cobranca_situacao == "EMITIDO":
                        IdIntegracao.append(invoice_payment.l10n_br_cobranca_idintegracao)

            _logger.info(IdIntegracao)
            if IdIntegracao:
                payload = json.dumps(IdIntegracao)

                url = "%s/api/v1/remessas/lote" % (
                    l10n_br_cobranca_id.l10n_br_url
                )

                headers = {
                    'Content-Type': "application/json",
                    'cnpj-cedente': _format_cnpj_cpf(l10n_br_cobranca_id.company_id.l10n_br_cnpj),
                    'cnpj-sh': "28653792000112",
                    'token-sh': l10n_br_cobranca_id.l10n_br_token,
                }

                try:

                    _logger.info([url, headers, payload])
                    response = requests.post(url, headers=headers, data=payload)
                    _logger.info(response.text)
                    json_data = json.loads(response.text)
                    _logger.info(json_data)
                    
                    if '_status' in json_data:
                        if json_data['_status'] == 'sucesso':
                            for item in json_data['_dados']['_sucesso']:
                                data_to_update = {}
                                data_to_update["l10n_br_cobranca_arquivo_remessa"] = item["arquivo"]
                                IdIntegracao = []
                                for titulo in item['titulos']:
                                    IdIntegracao.append(titulo['idintegracao'])
                                invoice_payments = self.env['account.move.line'].search([('l10n_br_cobranca_idintegracao','in',IdIntegracao)])
                                invoice_payments.write(data_to_update)
                                self.env.cr.commit()

                except Exception as e:
                    raise UserError(e)

    def action_boleto_nfe_descarte(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        IdIntegracao = []
        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
            if invoice_payment.l10n_br_cobranca_idintegracao:
                IdIntegracao.append(invoice_payment.l10n_br_cobranca_idintegracao)

        if IdIntegracao:
            payload = json.dumps(IdIntegracao)
            
            url = "%s/api/v1/boletos/descarta/lote" % (
                l10n_br_cobranca_id.l10n_br_url,
            )

            headers = {
                'Content-Type': "application/json",
                'cnpj-cedente': _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
                'cnpj-sh': "28653792000112",
                'token-sh': l10n_br_cobranca_id.l10n_br_token,
            }

            try:

                response = requests.post(url, headers=headers, data=payload)
                json_data = json.loads(response.text)
                
                if '_status' in json_data:
                    if json_data['_status'] == 'sucesso':
                        for item in json_data['_dados']['_sucesso']:
                            for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
                                
                                if invoice_payment.l10n_br_cobranca_idintegracao == item["idintegracao"]:
                                    data_to_update = {}
                                    data_to_update["l10n_br_cobranca_idintegracao"] = ""
                                    data_to_update["l10n_br_cobranca_situacao"] = ""
                                    data_to_update["l10n_br_cobranca_situacao_mensagem"] = ""
                                    invoice_payment.write(data_to_update)
                                    self.env.cr.commit()

            except Exception as e:
                invoice.message_post(body=e)
                raise UserError(e)

    def action_boleto_nfe_imprimir(self, force_download_pdf=False):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        invoice_payments = [line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity]
        if force_download_pdf:
            for invoice_payment in invoice_payments:
                invoice_payment.write({"l10n_br_cobranca_protocolo": False, "l10n_br_pdf_boleto": False})
            self.env.cr.commit()

        for nItem, invoice_payment in enumerate(sorted(invoice_payments, key=lambda l: l[0].date_maturity)):
            if invoice_payment.l10n_br_cobranca_idintegracao:
                if invoice_payment.l10n_br_cobranca_protocolo and not force_download_pdf:
                    invoice.action_boleto_nfe_download(force_download_pdf)

                else:
                    IdIntegracao = invoice_payment.l10n_br_cobranca_idintegracao

                    payload = json.dumps({"TipoImpressao": "99", "Boletos": [IdIntegracao]})
                    url = "%s/api/v1/boletos/impressao/lote" % (
                        l10n_br_cobranca_id.l10n_br_url,
                    )

                    headers = {
                        'Content-Type': "application/json",
                        'cnpj-cedente': _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
                        'cnpj-sh': "28653792000112",
                        'token-sh': l10n_br_cobranca_id.l10n_br_token,
                    }

                    try:

                        response = requests.post(url, headers=headers, data=payload)
                        json_data = json.loads(response.text)
                        
                        if '_status' in json_data:
                            if json_data['_status'] == 'sucesso':
                                data_to_update = {}
                                data_to_update["l10n_br_cobranca_protocolo"] = json_data['_dados']['protocolo']
                                invoice_payment.write(data_to_update)
                                self.env.cr.commit()
                                time.sleep(5)
                                invoice.action_boleto_nfe_download(force_download_pdf)

                    except Exception as e:
                        invoice.message_post(body=e)
                        raise UserError(e)

    def action_boleto_nfe_download(self, force_download_pdf = False):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity)):
            if invoice_payment.l10n_br_cobranca_protocolo and (not invoice_payment.l10n_br_pdf_boleto or force_download_pdf):

                url = "%s/api/v1/boletos/impressao/lote/%s" % (
                    l10n_br_cobranca_id.l10n_br_url,
                    invoice_payment.l10n_br_cobranca_protocolo
                )

                headers = {
                    'Content-Type': "application/json",
                }

                try:

                    response = requests.get(url, headers=headers)
                    #_logger.info([url, response.content])

                    if 'application/pdf' in response.headers.get('content-type'):
                        invoice_payment.write({
                            'l10n_br_pdf_boleto': base64.b64encode(response.content)
                        })
                        self.env.cr.commit()
                    
                except Exception as e:
                    invoice.message_post(body=e)
                    raise UserError(e)

    def action_nfe_sent_all(self):
        
        for record in self:
            record.action_nfe_sent()
    
    def _get_email_nfe_layout(self):
        return 'l10n_br_ciel_it_account.email_template_nfe'
    
    def action_nfe_sent(self):
    
        self.ensure_one()

        template_id = self.env.ref(self._get_email_nfe_layout())

        attachment_ids = []
        attachment_ids.append({"name": self.l10n_br_pdf_aut_nfe_fname, "type": "binary", "datas": self.l10n_br_pdf_aut_nfe, "store_fname": self.l10n_br_pdf_aut_nfe_fname})
        attachment_ids.append({"name": self.l10n_br_xml_aut_nfe_fname, "type": "binary", "datas": self.l10n_br_xml_aut_nfe, "store_fname": self.l10n_br_xml_aut_nfe_fname})

        if self.l10n_br_xml_cce_nfe:
            attachment_ids.append({"name": self.l10n_br_pdf_cce_nfe_fname, "type": "binary", "datas": self.l10n_br_pdf_cce_nfe, "store_fname": self.l10n_br_pdf_cce_nfe_fname})
            attachment_ids.append({"name": self.l10n_br_xml_cce_nfe_fname, "type": "binary", "datas": self.l10n_br_xml_cce_nfe, "store_fname": self.l10n_br_xml_cce_nfe_fname})

        if self.l10n_br_xml_can_nfe:
            attachment_ids.append({"name": self.l10n_br_pdf_can_nfe_fname, "type": "binary", "datas": self.l10n_br_pdf_can_nfe, "store_fname": self.l10n_br_pdf_can_nfe_fname})
            attachment_ids.append({"name": self.l10n_br_xml_can_nfe_fname, "type": "binary", "datas": self.l10n_br_xml_can_nfe, "store_fname": self.l10n_br_xml_can_nfe_fname})

        ir_config = self.sudo().env['ir.config_parameter']
        if not ir_config.get_param('l10n_br_ciel_it_account.enviar_boleto_nfe_juntos'):
            ir_config.sudo().set_param('l10n_br_ciel_it_account.enviar_boleto_nfe_juntos', "1")

        if ir_config.get_param('l10n_br_ciel_it_account.enviar_boleto_nfe_juntos') == "1":
            for invoice_payment in sorted([line for line in self.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity):
                if invoice_payment.l10n_br_pdf_boleto:
                    attachment_ids.append({"name": invoice_payment.l10n_br_pdf_boleto_fname, "type": "binary", "datas": invoice_payment.l10n_br_pdf_boleto, "store_fname": invoice_payment.l10n_br_pdf_boleto_fname})

        if not ir_config.get_param('l10n_br_ciel_it_account.abrir_form_email_nfe'):
            ir_config.sudo().set_param('l10n_br_ciel_it_account.abrir_form_email_nfe', "0")

        if ir_config.get_param('l10n_br_ciel_it_account.abrir_form_email_nfe') == "1":
            attachment_id = self.env['ir.attachment'].create(attachment_ids)
            ctx = {
                'default_model': 'account.move',
                'default_res_id': self.id,
                'default_use_template': bool(template_id.id),
                'default_template_id': template_id.id,
                'default_composition_mode': 'comment',
                'default_attachment_ids': attachment_id.ids,
                'custom_layout': "l10n_br_ciel_it_account.mail_notification_nfe",
                'force_email': True,
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
           
        else:
            attachments = []
            for attachment_id in attachment_ids:
                attachments.append( (0,0,attachment_id) )
            self.message_post_with_template(template_id.id, composition_mode='comment', model='account.move', res_id=self.id, email_layout_xmlid='l10n_br_ciel_it_account.mail_notification_nfe', attachment_ids=attachments)

    def action_boleto_sent(self):
    
        self.ensure_one()

        template_id = self.env.ref('l10n_br_ciel_it_account.email_template_boleto')

        attachment_ids = []
        for invoice_payment in sorted([line for line in self.line_ids if line.account_internal_type == 'receivable' and line.date_maturity], key=lambda l: l[0].date_maturity):
            if not invoice_payment.l10n_br_pdf_boleto:
                raise UserError("Boleto ainda não esta disponível.")
            attachment_ids.append((0,0,{"name": invoice_payment.l10n_br_pdf_boleto_fname, "type": "binary", "datas": invoice_payment.l10n_br_pdf_boleto, "store_fname": invoice_payment.l10n_br_pdf_boleto_fname}))

        self.message_post_with_template(template_id.id, composition_mode='comment', model='account.move', res_id=self.id, email_layout_xmlid='l10n_br_ciel_it_account.mail_notification_boleto', attachment_ids=attachment_ids)

    def _gerar_cce_nfe_tx2(self):

        self.ensure_one()

        def _format_datetime(date):
            return datetime.strftime(date,'%Y-%m-%d')+'T'+datetime.strftime(date,'%H:%M:%S')

        def _format_timezone(date):
            return datetime.strftime(date,'%z')[0:3]+':00'

        invoice = self
        invoice_vals = {}

        invoice_vals['Documento'] = 'CCE'
        invoice_vals['ChaveNota'] = invoice.l10n_br_chave_nf
        invoice_date_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        invoice_vals['dhEvento'] = _format_datetime(invoice_date_br)
        invoice_vals['Orgao'] = invoice.company_id.state_id.l10n_br_codigo_ibge
        invoice_vals['SeqEvento'] = invoice.l10n_br_sequencia_evento + 1
        invoice_vals['Correcao'] = invoice.l10n_br_correcao.replace("\n", " ")
        invoice_vals['Lote'] = 1
        invoice_vals['Fuso'] = _format_timezone(invoice_date_br)

        nfetx2 = ""
        for key, value in invoice_vals.items():
            if nfetx2:
                nfetx2 += "%0A"
            nfetx2 += key + "%3D" + str(value)
        
        return nfetx2

    def _gerar_nfe_tx2(self, gerar_nf = True):
    
        self.ensure_one()

        def _format_nDup(valor):
            return str(valor).zfill(3)

        def _format_decimal_2(valor):
            return "{:.2f}".format(valor)

        def _format_decimal_3(valor):
            return "{:.3f}".format(valor)

        def _format_decimal_4(valor):
            return "{:.4f}".format(valor)

        def _format_decimal_10(valor):
            return "{:.10f}".format(valor)

        def _format_desc(desc):
            return desc.replace("\n"," ")

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_datetime_timezone(date):
            return datetime.strftime(date,'%Y-%m-%d')+'T'+datetime.strftime(date,'%H:%M:%S')+datetime.strftime(date,'%z')[0:3]+':00'

        def _format_datetime(date):
            return datetime.strftime(date,'%Y-%m-%d')
    
        def _format_obs(texto):
            return str(texto).replace('"',' ').replace("¬"," ").replace("§","").replace("°","").replace("º","").replace("ª","").replace("\n"," ").replace("&","E").replace("%","")

        def _format_cep(texto):
            return str(texto).replace("-","").replace(".","")

        invoice = self

        if not invoice.l10n_br_numero_nf and gerar_nf:
            if not invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_numero_nfe_id:
                raise UserError('Operação Fiscal não informada.')
            invoice.l10n_br_numero_nf = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_numero_nfe_id.next_by_id()

        if not invoice.l10n_br_serie_nf:
            invoice.l10n_br_serie_nf = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_serie_nfe

        invoice_vals = {}

        invoice_vals['Id_A03'] = 0
        invoice_vals['versao_A02'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_versao
        invoice_vals['cUF_B02'] = invoice.company_id.state_id.l10n_br_codigo_ibge
        invoice_vals['cNF_B03'] = invoice.id
        invoice_vals['natOp_B04'] = invoice.l10n_br_operacao_id.descricao_nf
        invoice_vals['mod_B06'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_modelo
        invoice_vals['serie_B07'] = invoice.l10n_br_serie_nf
        invoice_vals['nNF_B08'] = invoice.l10n_br_numero_nf or 0
        
        invoice_date_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        invoice_vals['DHEMI_B09'] = _format_datetime_timezone(invoice_date_br)
        invoice_vals['DHSAIENT_B10'] = _format_datetime_timezone(invoice_date_br)

        invoice_vals['tpNF_B11'] =  TIPO_NF[invoice.type]
        invoice_vals['IDDEST_B11A'] = invoice.l10n_br_cfop_id.l10n_br_destino_operacao
        invoice_vals['cMunFG_B12'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge
        invoice_vals['tpImp_B21'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_formato_impressao
        invoice_vals['tpEmis_B22'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_tipo_emissao
        invoice_vals['tpAmb_B24'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_ambiente
        invoice_vals['finNFe_B25'] = invoice.l10n_br_operacao_id.l10n_br_finalidade
        invoice_vals['INDFINAL_B25A'] = invoice.l10n_br_operacao_consumidor
        invoice_vals['INDPRES_B25B'] = invoice.l10n_br_indicador_presenca
        invoice_vals['procEmi_B26'] = '0'
        invoice_vals['verProc_B27'] = 'Odoo 13.0e'

        if invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_tipo_emissao != "1":
            l10n_br_data_contingencia = pytz.timezone('America/Sao_Paulo').localize(invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_data_contingencia)
            invoice_vals['dhCont_B28'] = _format_datetime_timezone(l10n_br_data_contingencia)
            invoice_vals['xJust_B29'] = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_motivo_contingencia

        invoice_vals['CRT_C21'] = invoice.company_id.l10n_br_regime_tributario
        invoice_vals['CNPJ_C02'] = _format_cnpj_cpf(invoice.company_id.l10n_br_cnpj)
        invoice_vals['xNome_C03'] = invoice.company_id.l10n_br_razao_social or invoice.company_id.name
        invoice_vals['xFant_C04'] = invoice.company_id.name
        invoice_vals['xLgr_C06'] = invoice.company_id.street
        invoice_vals['nro_C07'] = invoice.company_id.l10n_br_endereco_numero or ""
        invoice_vals['xBairro_C09'] = invoice.company_id.l10n_br_endereco_bairro or ""
        invoice_vals['cMun_C10'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge
        invoice_vals['xMun_C11'] = invoice.company_id.l10n_br_municipio_id.name
        invoice_vals['UF_C12'] = invoice.company_id.state_id.code
        invoice_vals['CEP_C13'] = _format_cep(invoice.company_id.zip)
        invoice_vals['cPais_C14'] = invoice.company_id.country_id.l10n_br_codigo_bacen
        invoice_vals['xPais_C15'] = invoice.company_id.country_id.name
        invoice_vals['fone_C16'] = _format_fone(invoice.company_id.phone or "")
        invoice_vals['IE_C17'] = invoice.company_id.l10n_br_ie or ""
        if invoice.partner_id.l10n_br_cnpj:
            invoice_vals['CNPJ_E02'] = _format_cnpj_cpf(invoice.partner_id.l10n_br_cnpj)
        elif invoice.partner_id.l10n_br_cpf:
            invoice_vals['CPF_E03'] = _format_cnpj_cpf(invoice.partner_id.l10n_br_cpf)
        invoice_vals['IDESTRANGEIRO_E03A'] = invoice.partner_id.l10n_br_id_estrangeiro or ""
        
        if invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_ambiente == "2":
            invoice_vals['xNome_E04'] = "NF-E EMITIDA EM AMBIENTE DE HOMOLOGACAO - SEM VALOR FISCAL"
        else:
            invoice_vals['xNome_E04'] = _format_obs(invoice.partner_id.l10n_br_razao_social)
        
        invoice_vals['xLgr_E06'] = invoice.partner_id.street
        invoice_vals['xCpl_E08'] = invoice.partner_id.street2 or ""
        invoice_vals['nro_E07'] = invoice.partner_id.l10n_br_endereco_numero or ""
        invoice_vals['xBairro_E09'] = invoice.partner_id.l10n_br_endereco_bairro or ""

        if invoice.partner_id.country_id.code == "BR":
            invoice_vals['cMun_E10'] = invoice.partner_id.l10n_br_municipio_id.codigo_ibge
            invoice_vals['xMun_E11'] = invoice.partner_id.l10n_br_municipio_id.name
            invoice_vals['UF_E12'] = invoice.partner_id.state_id.code
            invoice_vals['CEP_E13'] = _format_cep(invoice.partner_id.zip)
        else:
            invoice_vals['cMun_E10'] = "9999999"
            invoice_vals['xMun_E11'] = invoice.partner_id.state_id.name
            invoice_vals['UF_E12'] = "EX"

        invoice_vals['cPais_E14'] = invoice.partner_id.country_id.l10n_br_codigo_bacen
        invoice_vals['xPais_E15'] = invoice.partner_id.country_id.name
        invoice_vals['fone_E16'] = _format_fone(invoice.partner_id.phone or "")
        invoice_vals['INDIEDEST_E16A'] = invoice.partner_id.l10n_br_indicador_ie
        invoice_vals['IE_E17'] = invoice.partner_id.l10n_br_ie or ""
        invoice_vals['IM_E18A'] = invoice.partner_id.l10n_br_im or ""
        invoice_vals['email_e19'] = invoice.partner_id.email or ""

        if invoice.company_id.state_id.code == "BA":
            invoice_vals['CNPJ_GA02'] = _format_cnpj_cpf(invoice.company_id.l10n_br_contador_partner_id.l10n_br_cnpj)

        if invoice.partner_id.id != invoice.partner_shipping_id.id and invoice.partner_shipping_id:
            if invoice.partner_shipping_id.l10n_br_cnpj:
                invoice_vals['CNPJ_G02'] = _format_cnpj_cpf(invoice.partner_shipping_id.l10n_br_cnpj)
            elif invoice.partner_shipping_id.l10n_br_cpf:
                invoice_vals['CPF_G02a'] = _format_cnpj_cpf(invoice.partner_shipping_id.l10n_br_cpf)
            elif invoice.partner_shipping_id.parent_id.l10n_br_cnpj:
                invoice_vals['CNPJ_G02'] = _format_cnpj_cpf(invoice.partner_shipping_id.parent_id.l10n_br_cnpj)
            elif invoice.partner_shipping_id.parent_id.l10n_br_cpf:
                invoice_vals['CPF_G02a'] = _format_cnpj_cpf(invoice.partner_shipping_id.parent_id.l10n_br_cpf)
            invoice_vals['xNome_G02b'] = invoice.partner_shipping_id.l10n_br_razao_social or invoice.partner_shipping_id.parent_id.l10n_br_razao_social
            invoice_vals['xLgr_G03'] = invoice.partner_shipping_id.street + " " + invoice.partner_shipping_id.l10n_br_endereco_numero # TODO: Rafael Petrella - 26/08/2020 - O Campo número do endereço já esta sendo enviado na tag correta porem o layout de impressão não esta funcionando;
            invoice_vals['xCpl_G05'] = invoice.partner_shipping_id.street2 or ""
            invoice_vals['nro_G04'] = invoice.partner_shipping_id.l10n_br_endereco_numero or ""
            invoice_vals['xBairro_G06'] = invoice.partner_shipping_id.l10n_br_endereco_bairro or ""
            invoice_vals['cMun_G07'] = invoice.partner_shipping_id.l10n_br_municipio_id.codigo_ibge
            invoice_vals['xMun_G08'] = invoice.partner_shipping_id.l10n_br_municipio_id.name
            invoice_vals['UF_G09'] = invoice.partner_shipping_id.state_id.code
            invoice_vals['CEP_G10'] = _format_cep(invoice.partner_shipping_id.zip)
            invoice_vals['cPais_G11'] = invoice.partner_shipping_id.country_id.l10n_br_codigo_bacen
            invoice_vals['xPais_G12'] = invoice.partner_shipping_id.country_id.name
            invoice_vals['fone_G13'] = _format_fone(invoice.partner_shipping_id.phone or "")
            invoice_vals['IE_G15'] = (invoice.partner_shipping_id.l10n_br_ie or "") if invoice.partner_shipping_id.l10n_br_cnpj else (invoice.partner_shipping_id.l10n_br_ie or invoice.partner_shipping_id.parent_id.l10n_br_ie or "")
            invoice_vals['email_G14'] = invoice.partner_shipping_id.email or ""

        if invoice.l10n_br_carrier_id.l10n_br_partner_id:
            if invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_cnpj:
                invoice_vals['CNPJ_X04'] = _format_cnpj_cpf(invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_cnpj)
            elif invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_cpf:
                invoice_vals['CPF_X05'] = _format_cnpj_cpf(invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_cpf)
            invoice_vals['xNome_X06'] = invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_razao_social or ""
            invoice_vals['IE_X07'] = invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_ie or ""
            invoice_vals['xEnder_X08'] = ((invoice.l10n_br_carrier_id.l10n_br_partner_id.street or "") + " " + (invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_endereco_numero or "") + " " + (invoice.l10n_br_carrier_id.l10n_br_partner_id.street2 or "")).replace("  ", " ").strip()
            invoice_vals['xMun_X09'] = invoice.l10n_br_carrier_id.l10n_br_partner_id.l10n_br_municipio_id.name or ""
            invoice_vals['UF_X10'] = invoice.l10n_br_carrier_id.l10n_br_partner_id.state_id.code or ""
        
        invoice_vals['placa_X19'] = invoice.l10n_br_veiculo_placa or ""
        invoice_vals['UF_X20'] = invoice.l10n_br_veiculo_uf or ""
        invoice_vals['RNTC_X21'] = invoice.l10n_br_veiculo_rntc or ""

        invoice_vals['UFSaidaPais_ZA02'] = invoice.l10n_br_uf_saida_pais or ""
        invoice_vals['xLocExporta_ZA03'] = invoice.l10n_br_local_despacho or ""
        invoice_vals['xLocDespacho_ZA04'] = invoice.l10n_br_local_embarque or ""

        invoice_vals['infAdFisco_Z02'] = urllib.parse.quote(_format_obs(invoice.l10n_br_informacao_fiscal or ""))
        invoice_vals['infCpl_Z03'] = urllib.parse.quote(_format_obs(invoice.l10n_br_informacao_complementar or ""))

        invoice_vols = []
        invoice_vol_vals = {}
        invoice_vol_vals['qVol_X27'] = invoice.l10n_br_volumes
        invoice_vol_vals['esp_X28'] = invoice.l10n_br_especie or ""
        invoice_vol_vals['pesoL_X31'] = _format_decimal_3(invoice.l10n_br_peso_liquido)
        invoice_vol_vals['pesoB_X32'] = _format_decimal_3(invoice.l10n_br_peso_bruto)
        invoice_vols.append(invoice_vol_vals)

        lots = invoice._get_invoiced_lot_values()
        #_logger.info(['Nr. Serie NF', lots])

        invoice_lines = []
        invoice_line_dis = []
        invoice_line_adis = []
        invoice_line_lotes = []
        invoice_line_ids = invoice.invoice_line_ids.filtered(lambda l: not l.display_type)
        for nItem, invoice_line in enumerate(sorted(invoice_line_ids, key=lambda l: l[0].sequence)):
            
            invoice_line_vals = {}

            invoice_line_vals['nItem_H02'] = nItem + 1
            invoice_line_vals['cProd_I02'] = invoice_line.product_id.default_code or ""

            ir_config = self.sudo().env['ir.config_parameter']
            if not ir_config.get_param('l10n_br_ciel_it_account.ean_xml_nfe'):
                ir_config.sudo().set_param('l10n_br_ciel_it_account.ean_xml_nfe', "1")
            l_ean_xml_nfe = ir_config.get_param('l10n_br_ciel_it_account.ean_xml_nfe') == "1"

            if not l_ean_xml_nfe:
                invoice_line_vals['cEAN_I03'] = 'SEM GTIN'
            else:
                invoice_line_vals['cEAN_I03'] = invoice_line.product_id.barcode or 'SEM GTIN'
            
            invoice_line_vals['xProd_I04'] = urllib.parse.quote(_format_desc(str(invoice_line.name or invoice_line.product_id.name)[0:120].replace('[%s] '% invoice_line.product_id.default_code or "", "")))
            
            lote_str = ''
            validate_str = ''
            lote_label = 'Nr. Série: ' if invoice_line.product_id.tracking == 'serial' else 'Lote: '
            lote_qty = invoice_line.quantity
            lotes = []
            while lote_qty > 0:
                pending_lots = [lot for lot in lots if lot['product_name'] in invoice_line.name and lot['quantity'] > 0]
                if not pending_lots:
                    break
                for sl_item in pending_lots:
                    
                    lote_str += (', ' if lote_str else lote_label) + sl_item['lot_name']
                    
                    if 'use_expiration_date' in self.env['product.template']._fields:
                        if invoice_line.product_id.use_expiration_date:
                            lote = {}
                    
                            lote['nLote_I81'] = sl_item['lot_name']
                            lote['qLote_I82'] = sl_item['quantity']

                            lot_id = self.env['stock.production.lot'].search([('product_id','=',invoice_line.product_id.id),('name','=',sl_item['lot_name'])])
                            if lot_id and lot_id.expiration_date:
                                validate_str += (', ' if validate_str else 'Data de Validade:') + (datetime.strftime(lot_id.expiration_date, '%d/%m/%Y'))
                                if lot_id.manufacturing_date:
                                    lote['dFab_I83'] = _format_datetime(lot_id.manufacturing_date)
                                lote['dVal_I84'] = _format_datetime(lot_id.expiration_date)

                            lotes.append(lote)
                    lote_qty -= sl_item['quantity']
            
            invoice_line_lotes.append(lotes)

            invoice_line_vals['infAdProd_V01'] = urllib.parse.quote((invoice_line.l10n_br_informacao_adicional or "") + (" " + lote_str if lote_str else "") + (" " + validate_str if validate_str else ""))
            invoice_line_vals['NCM_I05'] = invoice_line.product_id.l10n_br_ncm_id.codigo_ncm
            invoice_line_vals['nFCI_I70'] = invoice_line.product_id.l10n_br_fci or ""
            invoice_line_vals['cBenef_I05f'] = invoice_line.l10n_br_codigo_beneficio or ""
            if invoice_line.product_id.l10n_br_ncm_id.codigo_cest:
                invoice_line_vals['CEST_I05c'] = invoice_line.product_id.l10n_br_ncm_id.codigo_cest
                invoice_line_vals['indEscala_I05d'] = 'S' if invoice_line.product_id.l10n_br_indescala else 'N'
                if not invoice_line.product_id.l10n_br_indescala and invoice_line.product_id.l10n_br_cnpj_fabricante:
                    invoice_line_vals['CNPJFab_I05e'] = invoice_line.product_id.l10n_br_cnpj_fabricante

            invoice_line_vals['CFOP_I08'] = invoice_line.l10n_br_cfop_id.codigo_cfop
            invoice_line_vals['uCom_I09'] = invoice_line.product_uom_id.l10n_br_codigo_sefaz
            invoice_line_vals['qCom_I10'] = _format_decimal_4(invoice_line.quantity)

            if invoice.l10n_br_operacao_id.l10n_br_finalidade != '2':
                invoice_line_vals['vUnCom_I10a'] = _format_decimal_10(invoice_line.price_unit)
                invoice_line_vals['vProd_I11'] = _format_decimal_2(invoice_line.l10n_br_prod_valor)
            else:
                if invoice_line.price_unit > 0.00:
                    invoice_line_vals['vUnCom_I10a'] = _format_decimal_10(invoice_line.price_unit)
                    invoice_line_vals['vProd_I11'] = _format_decimal_2(invoice_line.l10n_br_prod_valor)
                else:
                    invoice_line_vals['vUnCom_I10a'] = _format_decimal_10(0.00)
                    invoice_line_vals['vProd_I11'] = _format_decimal_2(0.00)

            if invoice_line.l10n_br_desc_valor:
                invoice_line_vals['vDesc_I17'] = _format_decimal_2(invoice_line.l10n_br_desc_valor)

            if invoice_line.l10n_br_frete:
                invoice_line_vals['vFrete_I15'] = _format_decimal_2(invoice_line.l10n_br_frete)

            if invoice_line.l10n_br_seguro:
                invoice_line_vals['vSeg_I16'] = _format_decimal_2(invoice_line.l10n_br_seguro)

            if invoice_line.l10n_br_despesas_acessorias:
                invoice_line_vals['vOutro_I17a'] = _format_decimal_2(invoice_line.l10n_br_despesas_acessorias)

            if not l_ean_xml_nfe:
                invoice_line_vals['cEANTrib_I12'] = 'SEM GTIN'
            else:
                invoice_line_vals['cEANTrib_I12'] = invoice_line.product_id.barcode or 'SEM GTIN'

            if invoice_line.l10n_br_cfop_id.codigo_cfop in ['7101','7102','5501','5502','6501','6502']:
                uom_id = invoice_line.product_id.l10n_br_ncm_id.uom_id or invoice_line.product_id.uom_id
                invoice_line_vals['uTrib_I13'] = uom_id.l10n_br_codigo_comex_sefaz
                invoice_line_vals['qTrib_I14'] = _format_decimal_4(invoice_line.quantity * invoice_line.product_id.l10n_br_fator_utrib)
            else:
                invoice_line_vals['uTrib_I13'] = invoice_line.product_id.uom_id.l10n_br_codigo_sefaz
                invoice_line_vals['qTrib_I14'] = _format_decimal_4(invoice_line.quantity)
            if invoice.l10n_br_operacao_id.l10n_br_finalidade != '2':
                invoice_line_vals['vUnTrib_I14a'] = _format_decimal_10(invoice_line.price_unit)
            else:
                if sum(invoice_line_ids.mapped('price_unit')) > 0.00:
                    invoice_line_vals['vUnTrib_I14a'] = _format_decimal_10(invoice_line.price_unit)
                else:    
                    invoice_line_vals['vUnTrib_I14a'] = _format_decimal_10(0.00)
            invoice_line_vals['indTot_I17b'] = 1

            if invoice_line.l10n_br_pedido_compra or invoice_line.move_id.l10n_br_pedido_compra:
                invoice_line_vals['xPed_I60'] = invoice_line.l10n_br_pedido_compra or invoice_line.move_id.l10n_br_pedido_compra

            if invoice_line.l10n_br_item_pedido_compra or invoice_line.move_id.l10n_br_item_pedido_compra:
                invoice_line_vals['nItemPed_I61'] = invoice_line.l10n_br_item_pedido_compra or invoice_line.move_id.l10n_br_item_pedido_compra                

            invoice_line_vals['orig_N11'] = invoice_line.product_id.l10n_br_origem

            # ICMS
            if invoice_line.l10n_br_icms_cst in ['10','30','201','202']:
                invoice_line_vals['modBCST_N18'] = invoice_line.l10n_br_icmsst_modalidade_base
                invoice_line_vals['vBCST_N21'] = _format_decimal_2(invoice_line.l10n_br_icmsst_base)
                invoice_line_vals['pICMSST_N22'] = _format_decimal_2(invoice_line.l10n_br_icmsst_aliquota)
                invoice_line_vals['pMVAST_N19'] = _format_decimal_2(invoice_line.l10n_br_icmsst_mva)
                invoice_line_vals['vICMSST_N23'] = _format_decimal_2(invoice_line.l10n_br_icmsst_valor)
                if invoice_line.l10n_br_fcp_st_aliquota > 0.00:
                    invoice_line_vals['vBCFCPST_N23a'] = _format_decimal_2(invoice_line.l10n_br_fcp_st_base)
                    invoice_line_vals['pFCPST_N23b'] = _format_decimal_2(invoice_line.l10n_br_fcp_st_aliquota)
                    invoice_line_vals['vFCPST_N23d'] = _format_decimal_2(invoice_line.l10n_br_fcp_st_valor)

            if invoice_line.l10n_br_icms_cst and len(invoice_line.l10n_br_icms_cst) == 3:
                invoice_line_vals['CSOSN_N12a'] = invoice_line.l10n_br_icms_cst
            else:
                invoice_line_vals['CST_N12'] = invoice_line.l10n_br_icms_cst
            
            invoice_line_vals['modBC_N13'] = invoice_line.l10n_br_icms_modalidade_base
            invoice_line_vals['vBC_N15'] = _format_decimal_2(invoice_line.l10n_br_icms_base)
            invoice_line_vals['pICMS_N16'] = _format_decimal_2(invoice_line.l10n_br_icms_aliquota)
            
            # Quando ICMS40 não deve ser enviado a tag vICMS #17044
            if invoice_line.l10n_br_icms_cst not in ['40','41','50']:
                invoice_line_vals['vICMS_N17'] = _format_decimal_2(invoice_line.l10n_br_icms_valor)

            if invoice_line.l10n_br_icms_cst in ['20','30','40','41','50']:
                if invoice_line.l10n_br_icms_motivo_desonerado:
                    invoice_line_vals['motDesICMS_N28'] = invoice_line.l10n_br_icms_motivo_desonerado
                    invoice_line_vals['VICMSDESON_N28A'] = _format_decimal_2(invoice_line.l10n_br_icms_valor_desonerado)

            if invoice_line.l10n_br_icms_cst in ['20']:
                invoice_line_vals['pRedBC_N14'] = _format_decimal_2(invoice_line.l10n_br_icms_reducao_base)

            if invoice_line.l10n_br_icms_cst in ['51']:
                invoice_line_vals['vICMSOp_N16a'] = _format_decimal_2(invoice_line.l10n_br_icms_diferido_valor_operacao)
                invoice_line_vals['pDif_N16b'] = _format_decimal_2(invoice_line.l10n_br_icms_diferido_aliquota)
                invoice_line_vals['vICMSDif_N16c'] = _format_decimal_2(invoice_line.l10n_br_icms_diferido_valor)

            if invoice_line.l10n_br_icms_cst in ['60']:
                invoice_line_vals['vBCSTRet_N26'] = _format_decimal_2(invoice_line.l10n_br_icmsst_retido_base)
                invoice_line_vals['pST_N26a'] = _format_decimal_2(invoice_line.l10n_br_icmsst_retido_aliquota)
                invoice_line_vals['vICMSSubstituto_N26b'] = _format_decimal_2(invoice_line.l10n_br_icmsst_substituto_valor)
                invoice_line_vals['vICMSSTRet_N27'] = _format_decimal_2(invoice_line.l10n_br_icmsst_retido_valor)

            if invoice_line.l10n_br_icms_cst in ['70']:
                invoice_line_vals['pBCOp_N25'] = _format_decimal_2(invoice_line.l10n_br_icmsst_base_propria_aliquota)
                invoice_line_vals['UFST_N24'] = invoice_line.l10n_br_icmsst_uf

            if invoice_line.l10n_br_icms_cst in ['101','201','900']:
                invoice_line_vals['pCredSN_N29'] = _format_decimal_2(invoice_line.l10n_br_icms_credito_aliquota)
                invoice_line_vals['vCredICMSSN_N30'] = _format_decimal_2(invoice_line.l10n_br_icms_credito_valor)

            # II
            if invoice.l10n_br_cfop_id.l10n_br_destino_operacao == '3' and invoice_line.l10n_br_di_adicao_id:

                invoice_line_di_vals = {}
                invoice_line_di_vals['nDI_I19'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.name
                invoice_line_di_vals['dDI_I20'] = _format_datetime(invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_data_di)
                invoice_line_di_vals['xLocDesemb_I21'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_local_desembaraco
                invoice_line_di_vals['UFDesemb_I22'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_uf_desembaraco
                invoice_line_di_vals['dDesemb_I23'] = _format_datetime(invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_data_desembaraco)
                invoice_line_di_vals['tpViaTransp_I23a'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_via_transporte
                invoice_line_di_vals['vAFRMM_I23b'] = _format_decimal_2(0.00)
                invoice_line_di_vals['tpIntermedio_I23c'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.l10n_br_tipo_importacao
                invoice_line_di_vals['cExportador_I24'] = invoice.partner_id.id
                invoice_line_dis.append(invoice_line_di_vals)

                invoice_line_adi_vals = {}
                invoice_line_adi_vals['nAdicao_I26'] = invoice_line.l10n_br_di_adicao_id.l10n_br_di_id.name
                invoice_line_adi_vals['nSeqAdic_I27'] = '1'
                invoice_line_adi_vals['cFabricante_I28'] = invoice.partner_id.id
                invoice_line_adis.append(invoice_line_adi_vals)

                invoice_line_vals['vBC_P02'] = _format_decimal_2(invoice_line.l10n_br_ii_base)
                invoice_line_vals['vDespAdu_P03'] = _format_decimal_2(invoice_line.l10n_br_ii_valor_aduaneira)
                invoice_line_vals['vII_P04'] = _format_decimal_2(invoice_line.l10n_br_ii_valor)
                invoice_line_vals['vIOF_P05'] = _format_decimal_2(0.00)

            # IPI
            if invoice_line.l10n_br_ipi_cst in ['00','49','50','99']:
                if invoice_line.l10n_br_ipi_cst in ['49','99'] or invoice_line.l10n_br_ipi_valor > 0.00:
                    invoice_line_vals['CST_O09'] = invoice_line.l10n_br_ipi_cst
                    invoice_line_vals['vBC_O10'] = _format_decimal_2(invoice_line.l10n_br_ipi_base)
                    invoice_line_vals['pIPI_O13'] = _format_decimal_2(invoice_line.l10n_br_ipi_aliquota)
                    invoice_line_vals['vIPI_O14'] = _format_decimal_2(invoice_line.l10n_br_ipi_valor)
            elif invoice_line.l10n_br_ipi_cst == '01':
                invoice_line_vals['CST_O09'] = invoice_line.l10n_br_ipi_cst

            # PIS
            invoice_line_vals['CST_Q06'] = invoice_line.l10n_br_pis_cst
            invoice_line_vals['vBC_Q07'] = _format_decimal_2(invoice_line.l10n_br_pis_base)
            invoice_line_vals['pPIS_Q08'] = _format_decimal_2(invoice_line.l10n_br_pis_aliquota)
            invoice_line_vals['vPIS_Q09'] = _format_decimal_2(invoice_line.l10n_br_pis_valor)

            # COFINS
            invoice_line_vals['CST_S06'] = invoice_line.l10n_br_cofins_cst
            invoice_line_vals['vBC_S07'] = _format_decimal_2(invoice_line.l10n_br_cofins_base)
            invoice_line_vals['pCOFINS_S08'] = _format_decimal_2(invoice_line.l10n_br_cofins_aliquota)
            invoice_line_vals['vCOFINS_S11'] = _format_decimal_2(invoice_line.l10n_br_cofins_valor)

            # IPI
            if invoice_line.l10n_br_ipi_cst in ['00','01','49','50','99']:
                if invoice_line.l10n_br_ipi_cnpj: 
                    invoice_line_vals['CNPJProd_O03'] = _format_cnpj_cpf(invoice_line.l10n_br_ipi_cnpj)

                if invoice_line.l10n_br_ipi_selo_codigo:
                    invoice_line_vals['cSelo_O04'] = invoice_line.l10n_br_ipi_selo_codigo
                    invoice_line_vals['qSelo_O05'] = invoice_line.l10n_br_ipi_selo_quantidade

                invoice_line_vals['cEnq_O06'] = invoice_line.l10n_br_ipi_enq

            if invoice.partner_id.state_id.code != invoice.company_id.state_id.code and \
                invoice.l10n_br_operacao_consumidor == '1' and \
                invoice.partner_id.l10n_br_indicador_ie == '9' and \
                invoice_line.l10n_br_icms_inter_aliquota > 0.00:

                invoice_line_vals['vBCFCPUFDest_NA04'] = _format_decimal_2(invoice_line.l10n_br_fcp_base)
                invoice_line_vals['pFCPUFDest_NA05'] = _format_decimal_2(invoice_line.l10n_br_fcp_dest_aliquota)
                invoice_line_vals['vFCPUFDest_NA13'] = _format_decimal_2(invoice_line.l10n_br_fcp_dest_valor)

                invoice_line_vals['vBCUFDest_NA03'] = _format_decimal_2(invoice_line.l10n_br_icms_dest_base)
                invoice_line_vals['pICMSUFDest_NA07'] = _format_decimal_2(invoice_line.l10n_br_icms_dest_aliquota)
                invoice_line_vals['pICMSInter_NA09'] = _format_decimal_2(invoice_line.l10n_br_icms_inter_aliquota)
                invoice_line_vals['pICMSInterPart_NA11'] = _format_decimal_2(invoice_line.l10n_br_icms_inter_participacao)
                invoice_line_vals['vICMSUFDest_NA15'] = _format_decimal_2(invoice_line.l10n_br_icms_dest_valor)
                invoice_line_vals['vICMSUFRemet_NA17'] = _format_decimal_2(invoice_line.l10n_br_icms_remet_valor)

            invoice_lines.append(invoice_line_vals)

        if invoice.l10n_br_icmsst_valor > 0.00:
            iest_id = self.env["l10n_br_ciel_it_account.iest.uf"].search([('state_de_id','=',self.company_id.state_id.id),('state_para_id','=',self.partner_id.state_id.id),('company_id','=',self.company_id.id)],limit=1)
            if iest_id and iest_id.l10n_br_iest:
                invoice_vals['IEST_C18'] = iest_id.l10n_br_iest or ""

        invoice_vals['vBC_W03'] = _format_decimal_2(invoice.l10n_br_icms_base)
        invoice_vals['vICMS_W04'] = _format_decimal_2(invoice.l10n_br_icms_valor)
        invoice_vals['vICMSDeson_W04a'] = _format_decimal_2(invoice.l10n_br_icms_valor_desonerado)
        invoice_vals['vFCPUFDest_W04c'] = _format_decimal_2(invoice.l10n_br_fcp_dest_valor)
        invoice_vals['vICMSUFDest_W04e'] = _format_decimal_2(invoice.l10n_br_icms_dest_valor)
        invoice_vals['vICMSUFRemet_W04g'] = _format_decimal_2(invoice.l10n_br_icms_remet_valor)
        invoice_vals['vFCP_W04h'] = _format_decimal_2(0.00)
        invoice_vals['vBCST_W05'] = _format_decimal_2(invoice.l10n_br_icmsst_base)
        invoice_vals['vST_W06'] = _format_decimal_2(invoice.l10n_br_icmsst_valor)
        invoice_vals['vFCPST_W06a'] = _format_decimal_2(invoice.l10n_br_fcp_st_valor)
        invoice_vals['vFCPSTRet_W06b'] = _format_decimal_2(invoice.l10n_br_fcp_st_ant_valor)
        if invoice.l10n_br_operacao_id.l10n_br_finalidade != '2':
            invoice_vals['vProd_W07'] = _format_decimal_2(invoice.l10n_br_prod_valor)
        else:
            if invoice_line.price_unit > 0.00:
                invoice_vals['vProd_W07'] = _format_decimal_2(invoice.l10n_br_prod_valor)
            else:
                invoice_vals['vProd_W07'] = _format_decimal_2(0.00)
        invoice_vals['vFrete_W08'] = _format_decimal_2(invoice.l10n_br_frete)
        invoice_vals['vSeg_W09'] = _format_decimal_2(invoice.l10n_br_seguro)
        invoice_vals['vOutro_W15'] = _format_decimal_2(invoice.l10n_br_despesas_acessorias)
        invoice_vals['vDesc_W10'] = _format_decimal_2(invoice.l10n_br_desc_valor)
        invoice_vals['vII_W11'] = _format_decimal_2(invoice.l10n_br_ii_valor)
        invoice_vals['vIPI_W12'] = _format_decimal_2(invoice.l10n_br_ipi_valor)
        invoice_vals['vIPIDevol_W12a'] = _format_decimal_2(0.00)
        invoice_vals['vPIS_W13'] = _format_decimal_2(invoice.l10n_br_pis_valor)
        invoice_vals['vCOFINS_W14'] = _format_decimal_2(invoice.l10n_br_cofins_valor)
        invoice_vals['vNF_W16'] = _format_decimal_2(invoice.amount_total)

        invoice_vals['modFrete_X02'] = invoice.invoice_incoterm_id.l10n_br_modalidade_frete

        invoice_payments = []
        invoice_duplicates = []
        for nItem, invoice_payment in enumerate(sorted([line for line in invoice.line_ids if line.account_internal_type == 'receivable' and line.debit > 0.00 and line.date_maturity], key=lambda l: l[0].date_maturity)):

            if invoice.type != 'out_refund':
                invoice_duplicate_vals = {}
                invoice_duplicate_vals['nDup_Y08'] = _format_nDup(nItem + 1)
                invoice_duplicate_vals['vDup_Y10'] = _format_decimal_2(invoice_payment.debit)
                invoice_duplicate_vals['dVenc_Y09'] = datetime.strftime(invoice_payment.date_maturity,'%Y-%m-%d')
                invoice_duplicates.append(invoice_duplicate_vals)

            invoice_payment_vals = {}
            invoice_payment_vals['indPag_YA01b'] = invoice.invoice_payment_term_id.l10n_br_indicador or '1'
            invoice_payment_vals['tPag_YA02'] = invoice.payment_acquirer_id.l10n_br_meio if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_meio
            invoice_payment_vals['vPag_YA03'] = _format_decimal_2(invoice_payment.debit)
            invoice_payments.append(invoice_payment_vals)

        if invoice_payments:
            invoice_vals['nFat_Y03'] = invoice.l10n_br_numero_nf
            invoice_vals['vOrig_Y04'] = _format_decimal_2(invoice.amount_total+invoice.l10n_br_desc_valor)
            invoice_vals['vLiq_Y06'] = _format_decimal_2(invoice.amount_total)
            invoice_vals['vDesc_Y05'] = _format_decimal_2(invoice.l10n_br_desc_valor)
        else:
            invoice_payment_vals = {}
            invoice_payment_vals['indPag_YA01b'] = invoice.invoice_payment_term_id.l10n_br_indicador or '1'
            invoice_payment_vals['tPag_YA02'] = invoice.payment_acquirer_id.l10n_br_meio if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_meio
            invoice_payment_vals['vPag_YA03'] = _format_decimal_2(0.00)
            invoice_payments.append(invoice_payment_vals)

        invoice_referencias = []
        for invoice_ref in invoice.referencia_ids:
            invoice_referencia = {}
            invoice_referencia["refNFe_BA02"] = invoice_ref.l10n_br_chave_nf
            invoice_referencias.append(invoice_referencia)

        nfetx2 = "INCLUIR"
        for key, value in invoice_vals.items():
            nfetx2 += "%0A" + key + "%3D" + str(value)

        for idx, invoice_line_vals in enumerate(invoice_lines):
            nfetx2 += "%0AINCLUIRITEM"
            for key, value in invoice_line_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)

            if invoice_line_lotes:
                invoice_line_lotes_vals = invoice_line_lotes[idx]
                for invoice_line_lote_vals in invoice_line_lotes_vals:
                    nfetx2 += "%0AINCLUIRPARTE%3DI80"

                    for key2, value2 in invoice_line_lote_vals.items():
                        nfetx2 += "%0A" + key2 + "%3D" + str(value2)

                    nfetx2 += "%0ASALVARPARTE%3DI80"

            if invoice_line_dis:
                nfetx2 += "%0AINCLUIRPARTE%3DDI"
                invoice_line_di_vals = invoice_line_dis[idx]
                for key2, value2 in invoice_line_di_vals.items():
                    nfetx2 += "%0A" + key2 + "%3D" + str(value2)

                if invoice_line_adis:
                    nfetx2 += "%0AINCLUIRPARTE%3DADI"
                    invoice_line_adi_vals = invoice_line_adis[idx]
                    for key3, value3 in invoice_line_adi_vals.items():
                        nfetx2 += "%0A" + key3 + "%3D" + str(value3)
                    nfetx2 += "%0ASALVARPARTE%3DADI"

                nfetx2 += "%0ASALVARPARTE%3DDI"

            nfetx2 += "%0ASALVARITEM"

        for invoice_duplicate_vals in invoice_duplicates:
            nfetx2 += "%0AINCLUIRCOBRANCA"
            for key, value in invoice_duplicate_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0ASALVARCOBRANCA"

        for invoice_payment_vals in invoice_payments:
            nfetx2 += "%0AINCLUIRPARTE%3DYA"
            for key, value in invoice_payment_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0ASALVARPARTE%3DYA"
        
        for invoice_vol_vals in invoice_vols:
            nfetx2 += "%0AINCLUIRPARTE%3DVOL"
            for key, value in invoice_vol_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0ASALVARPARTE%3DVOL"
        
        for invoice_referencia_vals in invoice_referencias:
            nfetx2 += "%0AINCLUIRPARTE%3DNREF"
            for key, value in invoice_referencia_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0ASALVARPARTE%3DNREF"

        nfetx2 += "%0ASALVAR"
        return nfetx2

    def _gerar_nfse_tx2(self, gerar_nf=True):

        self.ensure_one()

        def _format_int(valor):
            return '{:d}'.format(int(round(valor,0)))

        def _format_decimal_2(valor):
            return "{:.2f}".format(valor)

        def _format_decimal_4(valor):
            return "{:.4f}".format(valor)

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/", "").replace("-", "").replace(".", "")
            else:
                return ""

        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_datetime_timezone(date):
            return datetime.strftime(date, '%Y-%m-%d') + 'T' + datetime.strftime(date, '%H:%M:%S')

        def _format_datetime(date):
            return datetime.strftime(date, '%Y-%m-%d')

        def _format_obs(texto):
            return str(texto).replace('"', ' ').replace("¬", " ").replace("§", "").replace("°", "").replace("º",
                                                                                                            "").replace(
                "ª", "").replace("\n", " ").replace("&", "E").replace("%", "")

        def _format_cep(texto):
            return str(texto).replace("-", "").replace(".", "")

        invoice = self
        invoice_vals = {}
        
        invoice_line_ids = invoice.invoice_line_ids.filtered(lambda l: not l.display_type)
        if len(invoice_line_ids) > 1:
            raise UserError("Nota Fiscal de Serviço não pode ter mais de 1 item.")
        
        invoice_line_id = invoice_line_ids[0]
        
        invoice_vals['SituacaoNota'] = 1
        invoice_vals['TipoRps'] = 1

        if not invoice.l10n_br_numero_rps and gerar_nf:
            if not invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_numero_nfe_id:
                raise UserError('Operação Fiscal não informada.')
            invoice.l10n_br_numero_rps = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_numero_nfe_id.next_by_id()

        if not invoice.l10n_br_serie_nf:
            invoice.l10n_br_serie_nf = invoice.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_serie_nfe

        invoice_vals['SerieRps'] = invoice.l10n_br_serie_nf
        invoice_vals['NumeroRps'] = invoice.l10n_br_numero_rps

        invoice_date_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        invoice_vals['DataEmissao'] = _format_datetime_timezone(invoice_date_br)
        invoice_vals['Competencia'] = _format_datetime(fields.Date.today())
        invoice_vals['CpfCnpjPrestador'] = _format_cnpj_cpf(invoice.company_id.l10n_br_cnpj)
        invoice_vals['InscricaoMunicipalPrestador'] = invoice.company_id.l10n_br_im or ""
        invoice_vals['RazaoSocialPrestador'] = _format_obs(invoice.company_id.l10n_br_razao_social) or _format_obs(invoice.company_id.name)
        invoice_vals['InscricaoEstadualPrestador'] = invoice.company_id.l10n_br_ie or ""
        invoice_vals['TipoLogradouroPrestador'] = ""
        invoice_vals['EnderecoPrestador'] = invoice.company_id.street or ""
        invoice_vals['NumeroPrestador'] = invoice.company_id.l10n_br_endereco_numero or ""
        invoice_vals['ComplementoPrestador'] = invoice.company_id.street2 or ""
        invoice_vals['TipoBairroPrestador'] = ""
        invoice_vals['BairroPrestador'] = invoice.company_id.l10n_br_endereco_bairro or ""
        invoice_vals['CodigoCidadePrestador'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge or ""
        invoice_vals['DescricaoCidadePrestador'] = invoice.company_id.l10n_br_municipio_id.name or ""
        invoice_vals['TelefonePrestador'] = _format_fone(invoice.company_id.phone or "")
        invoice_vals['EmailPrestador'] = invoice.company_id.email or ""
        invoice_vals['CepPrestador'] = _format_cep(invoice.company_id.zip)

        invoice_vals['OptanteSimplesNacional'] = "1" if invoice.company_id.l10n_br_regime_tributario != "3" else "2"

        #invoice_vals['IncentivadorCultural'] = 2
        #invoice_vals['RegimeEspecialTributacao'] = 0
        #invoice_vals['NaturezaTributacao'] = 0
        invoice_vals['IncentivoFiscal'] = 2

        invoice_vals['TipoTributacao'] = 6

        invoice_vals['ExigibilidadeISS'] = 1
        #invoice_vals['Operacao'] = 'A'
        invoice_vals['MunicipioIncidencia'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge or ""
        invoice_vals['CodigoCidadePrestacao'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge or ""
        #invoice_vals['DescricaoCidadePrestacao'] = ""

        invoice_vals['CpfCnpjTomador'] = _format_cnpj_cpf(invoice.partner_id.l10n_br_cnpj or invoice.partner_id.l10n_br_cpf)
        invoice_vals['RazaoSocialTomador'] = _format_obs(invoice.partner_id.l10n_br_razao_social) or _format_obs(invoice.partner_id.name)
        invoice_vals['InscricaoEstadualTomador'] = invoice.partner_id.l10n_br_ie or ""
        invoice_vals['InscricaoMunicipalTomador'] = invoice.partner_id.l10n_br_im or ""
        invoice_vals['TipoLogradouroTomador'] = ""
        invoice_vals['EnderecoTomador'] = invoice.partner_id.street or ""
        invoice_vals['NumeroTomador'] = invoice.partner_id.l10n_br_endereco_numero or ""
        invoice_vals['ComplementoTomador'] = invoice.partner_id.street2 or ""
        invoice_vals['BairroTomador'] = invoice.partner_id.l10n_br_endereco_bairro or ""
        invoice_vals['CodigoCidadeTomador'] = invoice.partner_id.l10n_br_municipio_id.codigo_ibge or ""
        invoice_vals['DescricaoCidadeTomador'] = invoice.partner_id.l10n_br_municipio_id.name or ""
        invoice_vals['UfTomador'] = invoice.partner_id.state_id.code or ""
        invoice_vals['CepTomador'] = _format_cep(invoice.partner_id.zip)
        invoice_vals['PaisTomador'] = invoice.partner_id.country_id.code or ""
        invoice_vals['EmailTomador'] = invoice.partner_id.email or ""
        #invoice_vals['DDDTomador'] = ""
        #invoice_vals['TelefoneTomador'] = ""

        invoice_vals['CodigoCnae'] = (invoice.company_id.l10n_br_cnae or "")[:7]
        invoice_vals['CodigoItemListaServico'] = invoice_line_id.product_id.l10n_br_codigo_servico or ""
        invoice_vals['CodigoTributacaoMunicipio'] = invoice_line_id.product_id.l10n_br_codigo_tributacao_servico or ""
        invoice_vals['DiscriminacaoServico'] = invoice_line_id.name or ""

        invoice_vals['AliquotaISS'] = invoice_line_id.l10n_br_iss_aliquota or 0.00
        invoice_vals['ValorIss'] = invoice_line_id.l10n_br_iss_valor or 0.00

        invoice_vals['IssRetido'] = 1 if invoice_line_id.l10n_br_iss_ret_valor > 0 else 2
        invoice_vals['ValorIssRetido'] = invoice_line_id.l10n_br_iss_ret_valor or 0.00

        if invoice.l10n_br_iss_municipio_id:
            invoice_vals['MunicipioIncidencia'] = invoice.l10n_br_iss_municipio_id.codigo_ibge or ""

        invoice_vals['AliquotaPIS'] = invoice_line_id.l10n_br_pis_ret_aliquota or 0.00
        invoice_vals['ValorPIS'] = invoice_line_id.l10n_br_pis_ret_valor or 0.00

        invoice_vals['AliquotaCOFINS'] = invoice_line_id.l10n_br_cofins_ret_aliquota or 0.00
        invoice_vals['ValorCOFINS'] = invoice_line_id.l10n_br_cofins_ret_valor or 0.00

        invoice_vals['AliquotaINSS'] = invoice_line_id.l10n_br_inss_ret_aliquota or 0.00
        invoice_vals['ValorINSS'] = invoice_line_id.l10n_br_inss_ret_valor or 0.00

        invoice_vals['AliquotaIR'] = invoice_line_id.l10n_br_irpj_ret_aliquota or 0.00
        invoice_vals['ValorIR'] = invoice_line_id.l10n_br_irpj_ret_valor or 0.00

        invoice_vals['AliquotaCSLL'] = invoice_line_id.l10n_br_csll_ret_aliquota or 0.00
        invoice_vals['ValorCSLL'] = invoice_line_id.l10n_br_csll_ret_valor or 0.00

        #invoice_vals['OutrasRetencoes'] = 0.00
        #invoice_vals['DescontoIncondicionado'] = 0.00
        #invoice_vals['DescontoCondicionado'] = 0.00
        #invoice_vals['ValorDeducoes'] = 0.00
        
        total_retido = invoice_line_id.l10n_br_pis_ret_valor + invoice_line_id.l10n_br_cofins_ret_valor + invoice_line_id.l10n_br_inss_ret_valor + invoice_line_id.l10n_br_irpj_ret_valor + invoice_line_id.l10n_br_csll_ret_valor

        invoice_vals['ValorServicos'] = _format_decimal_2(invoice_line_id.l10n_br_total_nfe)
        invoice_vals['BaseCalculo'] = _format_decimal_2(invoice_line_id.l10n_br_total_nfe)
        invoice_vals['QuantidadeServicos'] = _format_int(invoice_line_id.quantity)
        invoice_vals['ValorLiquidoNfse'] = _format_decimal_2(invoice_line_id.l10n_br_total_nfe - total_retido)

        invoice_emit_vals = {}
        invoice_emit_vals['IdLote'] = invoice.l10n_br_numero_rps
        invoice_emit_vals['NumeroLote'] = invoice.l10n_br_numero_rps
        invoice_emit_vals['CPFCNPJRemetente'] = _format_cnpj_cpf(invoice.company_id.l10n_br_cnpj)
        invoice_emit_vals['InscricaoMunicipalRemetente'] = invoice.company_id.l10n_br_im or ""
        invoice_emit_vals['ValorTotalServicos'] = _format_decimal_2(invoice_line_id.l10n_br_total_nfe)
        #invoice_emit_vals['ValorTotalDeducoes'] = ''
        invoice_emit_vals['ValorTotalBaseCalculo'] = _format_decimal_2(invoice_line_id.l10n_br_total_nfe)

        nfsetx2 = "%0AINCLUIR"
        for key, value in invoice_emit_vals.items():
            nfsetx2 += "%0A" + key + "%3D" + str(value)
        nfsetx2 += "%0ASALVAR"

        nfsetx2 += "%0AINCLUIRRPS"
        for key, value in invoice_vals.items():
            nfsetx2 += "%0A" + key + "%3D" + str(value)
        nfsetx2 += "%0ASALVARRPS"

        return nfsetx2

    def action_previsualizar_danfe_nfe(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )

        nfetx2 += self._gerar_nfe_tx2(False)
        nfetx2 += "&URL=0"

        url = "%s/ManagerAPIWeb/nfe/prever" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

        new_record = {}
        new_record["name"] = self.l10n_br_pdf_aut_nfe_fname
        new_record["type"] = "binary"
        new_record["datas"] = base64.b64encode(response.content)
        new_record["store_fname"] = self.l10n_br_pdf_aut_nfe_fname
        attach_id = self.env["ir.attachment"].create(new_record)

        url_attach = '/web/content/ir.attachment/%s/datas/%s?download=true' % (attach_id.id,self.l10n_br_pdf_aut_nfe_fname)

        return {
            'name': self.l10n_br_pdf_aut_nfe_fname,
            'type': 'ir.actions.act_url',
            'url': url_attach,
        }

    def action_descartar_rps_nfse(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()

        if not self.l10n_br_handle_nfse:
            return

        url = "%s/ManagerAPIWeb/nfse/descarta?encode=true&Grupo=%s&CNPJ=%s&NomeCidade=%s&Handle=%s" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_cidadeuf,
            self.l10n_br_handle_nfse,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.post(url, auth=basic_auth, headers=headers)

    def action_parse_xml_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )
        nfetx2 += self._gerar_nfe_tx2(False)
        nfetx2 += "&Converter=1&Assinado=1&URL=0"

        url = "%s/ManagerAPIWeb/nfe/exportaxml" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )
        
        response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

        # response.content contem o XML que precisa ser validado
        # adicionar regra pra validar o XML e exibir mensages de erro
        # o arquivo XSD esta no path static/schema/PL_009/nfe_v4.00.xsd

    def action_previsualizar_xml_nfe(self):

        pass

    def action_previsualizar_xml_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )
        nfetx2 += self._gerar_nfe_tx2(False)
        nfetx2 += "&Converter=1&Assinado=1&URL=0"

        url = "%s/ManagerAPIWeb/nfe/exportaxml" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )
        
        response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

        new_record = {}
        new_record["name"] = self.l10n_br_xml_aut_nfe_fname
        new_record["type"] = "binary"
        new_record["datas"] = base64.b64encode(response.content)
        new_record["store_fname"] = self.l10n_br_xml_aut_nfe_fname
        attach_id = self.env["ir.attachment"].create(new_record)

        url_attach = '/web/content/ir.attachment/%s/datas/%s?download=true' % (attach_id.id,self.l10n_br_xml_aut_nfe_fname)

        return {
            'name': self.l10n_br_xml_aut_nfe_fname,
            'type': 'ir.actions.act_url',
            'url': url_attach,
        }

    def action_validar_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )
        nfetx2 += self._gerar_nfe_tx2()

        url = "%s/ManagerAPIWeb/nfe/valida" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Validar NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))
            self.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))

        except Exception as e:
            self.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_gerar_xmldanfe_nfe(self):
        self.ensure_one()
        invoice = self
        invoice.action_gerar_xml_nfe()
        invoice.action_gerar_danfe_nfe()
        if invoice.l10n_br_situacao_nf == "cancelado":
            self.action_gerar_xml_cancelado_nfe()
            self.action_gerar_danfe_cancelado_nfe()            

    def action_gerar_xmlrps_nfse(self):
        self.ensure_one()
        invoice = self
        invoice.action_gerar_rps_nfse()

    def action_gerar_nfe(self):
        """
        Transmite NF-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self
        
        if invoice.invoice_payment_term_id.is_advpay and invoice.invoice_payment_state != 'paid':
            raise UserError("Condição de pagamento 'ANTECIPADO' exige que a fatura esteja paga para geração da NF-e!")
        
        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )
        nfetx2 += invoice._gerar_nfe_tx2()

        _logger.info('action_gerar_nfe, GET TX2 DATA 1')
        _logger.info(nfetx2.encode('utf-8'))
        _logger.info('action_gerar_nfe, GET TX2 DATA 2')

        url = "%s/ManagerAPIWeb/nfe/envia" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Gerar NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

            invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))
            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if "Autorizado o uso da NF-e" in response.text:
                invoice.update({
                    'l10n_br_chave_nf': response_values[1],
                    'l10n_br_cstat_nf': response_values[2],
                    'l10n_br_xmotivo_nf': response_values[3],
                    'l10n_br_situacao_nf': 'autorizado',
                })
                self.env.cr.commit()

                invoice.action_gerar_xml_nfe()
                invoice.action_gerar_danfe_nfe()

            else:
                invoice.update({
                    'l10n_br_situacao_nf': 'excecao_autorizado',
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1]
                })
                self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_gerar_nfse(self):
        """
        Transmite NFS-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/", "").replace("-", "").replace(".", "")
            else:
                return ""

        self.ensure_one()
        invoice = self

        if invoice.invoice_payment_term_id.is_advpay and invoice.invoice_payment_state != 'paid':
            raise UserError("Condição de pagamento 'ANTECIPADO' exige que a fatura esteja paga para geração da NF-e!")

        if invoice.l10n_br_handle_nfse:
            invoice.action_descartar_rps_nfse()

        nfsetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "formato%3Dtx2%0Apadrao%3DTecnoNFSe%0A",
            "NomeCidade%3D" + self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_cidadeuf + "%0A"
        )

        nfsetx2 += self._gerar_nfse_tx2()

        url = "%s/ManagerAPIWeb/nfse/envia" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Gerar NFSe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            _logger.info(nfsetx2)
            response = requests.post(url, auth=basic_auth, headers=headers, data=nfsetx2.encode('utf-8'))

            invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter', ' ')))
            response_values = response.content.decode('utf-8').replace('\delimiter', ' ').split(",")
            if "Autorizada​" in response.content.decode('utf-8'):
                invoice.update({
                    'l10n_br_handle_nfse': response_values[0],
                    'l10n_br_numero_nfse': response_values[2],
                    'l10n_br_xmotivo_nf': response_values[3],
                    'l10n_br_situacao_nf': 'autorizado',
                })
                self.env.cr.commit()

                invoice.action_gerar_rps_nfse()

            else:
                invoice.update({
                    'l10n_br_handle_nfse': response_values[0],
                    'l10n_br_situacao_nf': 'excecao_autorizado',
                    'l10n_br_xmotivo_nf': response_values
                })
                self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_resolver_nfe(self):
        """
        Resolver NF-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()
        invoice = self
        
        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        url = "%s/ManagerAPIWeb/nfe/resolve" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Resolver NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

            invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))
            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if invoice.l10n_br_situacao_nf != 'excecao_cancelado':
                if "Autorizado o uso da NF-e" in response.text:
                    invoice.update({
                        'l10n_br_chave_nf': response_values[1],
                        'l10n_br_cstat_nf': response_values[2],
                        'l10n_br_xmotivo_nf': response_values[3],
                        'l10n_br_situacao_nf': 'autorizado',
                    })
                    self.env.cr.commit()

                    invoice.action_gerar_xml_nfe()
                    invoice.action_gerar_danfe_nfe()

                else:
                    invoice.update({
                        'l10n_br_situacao_nf': 'excecao_autorizado',
                        'l10n_br_xmotivo_nf': response_values[len(response_values)-1]
                    })
                    self.env.cr.commit()
            else:
                if "Evento registrado e vinculado a NF-e" in response.text or "Cancelamento homologado fora de prazo" in response.text or "Cancelamento de NF-e homologado" in response.text:
                    self.update({
                        'l10n_br_cstat_nf': response_values[len(response_values)-2],
                        'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                        'l10n_br_situacao_nf': 'cancelado',
                    })
                    self.env.cr.commit()
                    self.action_gerar_xml_cancelado_nfe()
                    self.action_gerar_danfe_cancelado_nfe()
                else:
                    invoice.update({
                        'l10n_br_situacao_nf': 'excecao_cancelado',
                        'l10n_br_xmotivo_nf': response_values[len(response_values)-1]
                    })
                    self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_gerar_rps_nfse(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()

        _logger.info(self.l10n_br_handle_nfse)
        if not self.l10n_br_handle_nfse:
            return

        url = "%s/ManagerAPIWeb/nfse/imprime?encode=true&Grupo=%s&CNPJ=%s&NomeCidade=%s&Handle=%s&URL=0" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_cidadeuf,
            self.l10n_br_handle_nfse,
        )
        
        _logger.info(url)

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)

        _logger.info(response.content)

        self.update({
            'l10n_br_pdf_aut_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_danfe_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()

        if not self.l10n_br_chave_nf:
            return

        url = "%s/ManagerAPIWeb/nfe/imprime?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&URL=0" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)

        self.update({
            'l10n_br_pdf_aut_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_xml_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()

        if not self.l10n_br_chave_nf:
            return

        url = "%s/ManagerAPIWeb/nfe/xml?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        self.update({
            'l10n_br_xml_aut_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_danfe_cancelado_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/nfe/imprime?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&URL=0" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        self.update({
            'l10n_br_pdf_can_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_xml_cancelado_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/nfe/xml?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&Documento=Cancelamento" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        self.update({
            'l10n_br_xml_can_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_cancelar_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/nfe/cancela?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&Justificativa=%s" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
            self.l10n_br_motivo,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Cancelar NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers)
            self.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))

            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if "Evento registrado e vinculado a NF-e" in response.text or "Cancelamento homologado fora de prazo" in response.text:
                self.update({
                    'l10n_br_cstat_nf': response_values[len(response_values)-2],
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                    'l10n_br_situacao_nf': 'cancelado',
                })
                self.env.cr.commit()
                self.action_gerar_xml_cancelado_nfe()
                self.action_gerar_danfe_cancelado_nfe()
            else:
                self.update({
                    'l10n_br_cstat_nf': response_values[len(response_values)-2],
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                    'l10n_br_situacao_nf': 'excecao_cancelado',
                })
                self.env.cr.commit()

        except Exception as e:
            self.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_gerar_danfe_cce_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/nfe/imprime?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&URL=0&Documento=CCe" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        self.update({
            'l10n_br_pdf_cce_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_xml_cce_nfe(self):
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/nfe/xml?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&Documento=CCe" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_nf,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        self.update({
            'l10n_br_xml_cce_nfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_cce_nfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()
        invoice = self

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=" % ( 
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
        )

        nfetx2 += invoice._gerar_cce_nfe_tx2()

        url = "%s/ManagerAPIWeb/nfe/envia" % (
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_usuario,
            self.l10n_br_operacao_id.l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Gerar CCe NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))
            
            try:
                invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))
            except:
                invoice.message_post(body=_format_message(response.text))

            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if "AUTORIZADA" in response.text:
                invoice.update({
                    'l10n_br_cstat_nf': response_values[len(response_values)-2],
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                    'l10n_br_sequencia_evento': invoice.l10n_br_sequencia_evento + 1,
                    'l10n_br_situacao_nf': 'cce',
                })
                self.env.cr.commit()

                invoice.action_gerar_xml_cce_nfe()
                invoice.action_gerar_danfe_cce_nfe()
            elif "Duplicidade de Evento" in response.text:
                invoice.update({
                    'l10n_br_cstat_nf': response_values[len(response_values)-2],
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                    'l10n_br_sequencia_evento': invoice.l10n_br_sequencia_evento + 1,
                    'l10n_br_situacao_nf': 'excecao_cce',
                })
                self.env.cr.commit()
            else:
                invoice.update({
                    'l10n_br_cstat_nf': response_values[len(response_values)-2],
                    'l10n_br_xmotivo_nf': response_values[len(response_values)-1],
                    'l10n_br_situacao_nf': 'excecao_cce',
                })
                self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def _set_provisorio(self):
        
        self.ensure_one()        
        if self.state == 'draft':
            self.update({'name': '/'})

    @api.onchange('l10n_br_numero_nf')
    def onchange_l10n_br_numero_nf(self):
        for item in self:
            item.write({'invoice_payment_ref': item.l10n_br_numero_nf})

    @api.onchange('l10n_br_calcular_imposto')
    def onchange_l10n_br_calcular_imposto(self):
        for item in self:
            if self._context.get('check_rateio_frete', True):
                item._do_rateio_frete()
            invoice_line_ids = item.invoice_line_ids.filtered(lambda l: not l.display_type)
            for line in invoice_line_ids:
                line._onchange_price_subtotal()
                line._do_calculate_l10n_br_impostos()
            item._do_calculate_l10n_br_impostos()
            item.line_ids.with_context(check_move_validity=False)._onchange_price_subtotal()
            item.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True)

    def _do_rateio_frete(self):

        self.ensure_one()
        
        if not self._context.get('update_tax', True):
            return

        invoice_line_ids = self.invoice_line_ids.filtered(lambda l: not l.display_type)
        for line in invoice_line_ids:
            values_to_update = {}
            values_to_update['l10n_br_frete'] = 0.00
            values_to_update['l10n_br_seguro'] = 0.00
            values_to_update['l10n_br_despesas_acessorias'] = 0.00

            line.update(values_to_update)

        l10n_br_frete = self.l10n_br_frete
        l10n_br_seguro = self.l10n_br_seguro
        l10n_br_despesas_acessorias = self.l10n_br_despesas_acessorias

        for idx, line in enumerate(invoice_line_ids):
            values_to_update = {}

            fator = (line.l10n_br_prod_valor - line.l10n_br_desc_valor) / ((self.l10n_br_prod_valor - self.l10n_br_desc_valor) or 1.00)

            values_to_update['l10n_br_frete'] = round(l10n_br_frete * fator,2)
            values_to_update['l10n_br_seguro'] = round(l10n_br_seguro * fator,2)
            values_to_update['l10n_br_despesas_acessorias'] = round(l10n_br_despesas_acessorias * fator,2)

            l10n_br_frete -= values_to_update['l10n_br_frete']
            l10n_br_seguro -= values_to_update['l10n_br_seguro']
            l10n_br_despesas_acessorias -= values_to_update['l10n_br_despesas_acessorias']

            if idx == len(invoice_line_ids)-1:
                values_to_update['l10n_br_frete'] += l10n_br_frete
                values_to_update['l10n_br_seguro'] += l10n_br_seguro
                values_to_update['l10n_br_despesas_acessorias'] += l10n_br_despesas_acessorias

            line.update(values_to_update)

    def _get_l10n_br_informacao_fiscal(self, l10n_br_informacao_fiscal):
        # Função criada para que seja possivel alterar a observação fiscal da nota fiscal
        return l10n_br_informacao_fiscal

    def _do_calculate_l10n_br_impostos(self):

        if self.company_id.country_id != self.env.ref('base.br'):
            return

        def _format_decimal_2(valor):
            return "{:.2f}".format(valor).replace(".",",")

        self.ensure_one()

        if not self.l10n_br_imposto_auto:
            return

        #############################
        ##### INFORMAÇÃO FISCAL #####
        #############################
        values_to_update = {}

        l10n_br_mensagem_fiscal_ids = []
        for line in self.invoice_line_ids.filtered(lambda l: not l.display_type):
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
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%invoice_origin%%',self.invoice_origin or "")
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_pedido_compra%%',"Pedido de Compra: " + self.l10n_br_pedido_compra + "." if self.l10n_br_pedido_compra else "")
        
        # Simples Nacional
        if self.company_id.l10n_br_regime_tributario != '3':
            l10n_br_icms_credito_valor = sum(self.invoice_line_ids.mapped('l10n_br_icms_credito_valor'))
            l10n_br_icms_credito_aliquota = 0.00
            if self.invoice_line_ids:
                l10n_br_icms_credito_aliquota = max(self.invoice_line_ids.mapped('l10n_br_icms_credito_aliquota'))
            if l10n_br_icms_credito_valor > 0.00 and l10n_br_icms_credito_aliquota > 0.00:
                l10n_br_informacao_fiscal += (" " if l10n_br_informacao_fiscal else "") + "PERMITE O APROVEITAMENTO DO CRÉDITO DE ICMS NO VALOR DE (R$ {0}) CORRESPONDENTE À ALIQUOTA DE ({1}%), NOS TERMOS DO ART 23, DA LEI COMPLEMENTAR Nº 123 DE 2006.".format( _format_decimal_2(l10n_br_icms_credito_valor), _format_decimal_2(l10n_br_icms_credito_aliquota) )
            else:
                l10n_br_informacao_fiscal += (" " if l10n_br_informacao_fiscal else "") + "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL NÃO GERA CRÉDITO FISCAL DE ICMS/IPI, NOS TERMOS DO ART 23, DA LEI COMPLEMENTAR Nº 123 DE 2006."

        l10n_br_informacao_fiscal = self._get_l10n_br_informacao_fiscal(l10n_br_informacao_fiscal)

        values_to_update['l10n_br_informacao_fiscal'] = l10n_br_informacao_fiscal

        self.update(values_to_update)

    @api.onchange('invoice_line_ids', 'line_ids','l10n_br_tipo_pedido','l10n_br_tipo_pedido_entrada','l10n_br_operacao_consumidor','partner_id','company_id','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias')
    def onchange_l10n_br_imposto(self):
        for item in self:
            item.l10n_br_calcular_imposto = not item.l10n_br_calcular_imposto

    @api.depends('invoice_line_ids.l10n_br_icms_base','invoice_line_ids.l10n_br_icms_valor','invoice_line_ids.l10n_br_icms_valor_isento','invoice_line_ids.l10n_br_icms_valor_outros','invoice_line_ids.l10n_br_icms_valor_desonerado',
        'invoice_line_ids.l10n_br_icmsst_base','invoice_line_ids.l10n_br_icmsst_valor','invoice_line_ids.l10n_br_icmsst_valor_outros','invoice_line_ids.l10n_br_prod_valor','invoice_line_ids.l10n_br_frete','invoice_line_ids.l10n_br_seguro','invoice_line_ids.l10n_br_despesas_acessorias',
        'invoice_line_ids.l10n_br_desc_valor','invoice_line_ids.l10n_br_ipi_valor','invoice_line_ids.l10n_br_ipi_valor_isento','invoice_line_ids.l10n_br_ipi_valor_outros','invoice_line_ids.l10n_br_pis_valor',
        'invoice_line_ids.l10n_br_pis_valor_isento','invoice_line_ids.l10n_br_pis_valor_outros','invoice_line_ids.l10n_br_cofins_valor','invoice_line_ids.l10n_br_cofins_valor_isento',
        'invoice_line_ids.l10n_br_cofins_valor_outros','invoice_line_ids.l10n_br_ii_valor','invoice_line_ids.l10n_br_ii_valor_aduaneira','invoice_line_ids.l10n_br_total_nfe','invoice_line_ids.l10n_br_total_tributos','invoice_line_ids.l10n_br_icms_dest_valor',
        'invoice_line_ids.l10n_br_icms_remet_valor','invoice_line_ids.l10n_br_fcp_dest_valor','invoice_line_ids.l10n_br_fcp_st_valor','invoice_line_ids.l10n_br_fcp_st_ant_valor','invoice_line_ids.l10n_br_iss_valor','invoice_line_ids.l10n_br_irpj_valor','invoice_line_ids.l10n_br_csll_valor',
        'invoice_line_ids.l10n_br_irpj_ret_valor','invoice_line_ids.l10n_br_inss_ret_valor','invoice_line_ids.l10n_br_iss_ret_valor','invoice_line_ids.l10n_br_csll_ret_valor','invoice_line_ids.l10n_br_pis_ret_valor','invoice_line_ids.l10n_br_cofins_ret_valor', 'invoice_line_ids.l10n_br_icmsst_substituto_valor',
        'invoice_line_ids.l10n_br_icmsst_substituto_valor_outros', 'invoice_line_ids.l10n_br_icmsst_retido_valor', 'invoice_line_ids.l10n_br_icmsst_retido_valor_outros')

    def _l10n_br_amount_all(self):
        """
        Compute the total amounts of the Account Move.
        """
        for order in self:
            l10n_br_icms_base = sum(order.invoice_line_ids.mapped('l10n_br_icms_base'))
            l10n_br_icms_valor = sum(order.invoice_line_ids.mapped('l10n_br_icms_valor'))
            l10n_br_icms_valor_isento = sum(order.invoice_line_ids.mapped('l10n_br_icms_valor_isento'))
            l10n_br_icms_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_icms_valor_outros'))
            l10n_br_icms_valor_desonerado = sum(order.invoice_line_ids.mapped('l10n_br_icms_valor_desonerado'))
            l10n_br_icms_valor = sum(order.invoice_line_ids.mapped('l10n_br_icms_valor'))
            l10n_br_icms_dest_valor = sum(order.invoice_line_ids.mapped('l10n_br_icms_dest_valor'))
            l10n_br_icms_remet_valor = sum(order.invoice_line_ids.mapped('l10n_br_icms_remet_valor'))
            l10n_br_fcp_dest_valor = sum(order.invoice_line_ids.mapped('l10n_br_fcp_dest_valor'))
            l10n_br_fcp_st_valor = sum(order.invoice_line_ids.mapped('l10n_br_fcp_st_valor'))
            l10n_br_fcp_st_ant_valor = sum(order.invoice_line_ids.mapped('l10n_br_fcp_st_ant_valor'))
            l10n_br_icmsst_base = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_base'))
            l10n_br_icmsst_valor = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_valor'))
            l10n_br_icmsst_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_valor_outros'))
            l10n_br_icmsst_substituto_valor = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_substituto_valor'))
            l10n_br_icmsst_substituto_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_substituto_valor_outros'))
            l10n_br_icmsst_retido_valor = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_retido_valor'))
            l10n_br_icmsst_retido_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_icmsst_retido_valor_outros'))
            l10n_br_prod_valor = sum(order.invoice_line_ids.mapped('l10n_br_prod_valor'))
            l10n_br_frete = sum(order.invoice_line_ids.mapped('l10n_br_frete'))
            l10n_br_seguro = sum(order.invoice_line_ids.mapped('l10n_br_seguro'))
            l10n_br_despesas_acessorias = sum(order.invoice_line_ids.mapped('l10n_br_despesas_acessorias'))
            l10n_br_desc_valor = sum(order.invoice_line_ids.mapped('l10n_br_desc_valor'))
            l10n_br_ipi_valor = sum(order.invoice_line_ids.mapped('l10n_br_ipi_valor'))
            l10n_br_ipi_valor_isento = sum(order.invoice_line_ids.mapped('l10n_br_ipi_valor_isento'))
            l10n_br_ipi_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_ipi_valor_outros'))
            l10n_br_pis_valor = sum(order.invoice_line_ids.mapped('l10n_br_pis_valor'))
            l10n_br_pis_valor_isento = sum(order.invoice_line_ids.mapped('l10n_br_pis_valor_isento'))
            l10n_br_pis_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_pis_valor_outros'))
            l10n_br_cofins_valor = sum(order.invoice_line_ids.mapped('l10n_br_cofins_valor'))
            l10n_br_cofins_valor_isento = sum(order.invoice_line_ids.mapped('l10n_br_cofins_valor_isento'))
            l10n_br_cofins_valor_outros = sum(order.invoice_line_ids.mapped('l10n_br_cofins_valor_outros'))
            l10n_br_ii_valor = sum(order.invoice_line_ids.mapped('l10n_br_ii_valor'))
            l10n_br_ii_valor_aduaneira = sum(order.invoice_line_ids.mapped('l10n_br_ii_valor_aduaneira'))
            l10n_br_iss_valor = sum(order.invoice_line_ids.mapped('l10n_br_iss_valor'))
            l10n_br_irpj_valor = sum(order.invoice_line_ids.mapped('l10n_br_irpj_valor'))
            l10n_br_csll_valor = sum(order.invoice_line_ids.mapped('l10n_br_csll_valor'))
            l10n_br_irpj_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_irpj_ret_valor'))
            l10n_br_inss_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_inss_ret_valor'))
            l10n_br_iss_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_iss_ret_valor'))
            l10n_br_csll_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_csll_ret_valor'))
            l10n_br_pis_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_pis_ret_valor'))
            l10n_br_cofins_ret_valor = sum(order.invoice_line_ids.mapped('l10n_br_cofins_ret_valor'))
            l10n_br_total_nfe = sum(order.invoice_line_ids.mapped('l10n_br_total_nfe'))
            l10n_br_total_tributos = sum(order.invoice_line_ids.mapped('l10n_br_total_tributos'))

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
                'l10n_br_frete': l10n_br_frete,
                'l10n_br_seguro': l10n_br_seguro,
                'l10n_br_despesas_acessorias': l10n_br_despesas_acessorias,
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
                'l10n_br_iss_valor': l10n_br_iss_valor,
                'l10n_br_irpj_valor': l10n_br_irpj_valor,
                'l10n_br_csll_valor': l10n_br_csll_valor,
                'l10n_br_irpj_ret_valor': l10n_br_irpj_ret_valor,
                'l10n_br_inss_ret_valor': l10n_br_inss_ret_valor,
                'l10n_br_iss_ret_valor': l10n_br_iss_ret_valor,
                'l10n_br_csll_ret_valor': l10n_br_csll_ret_valor,
                'l10n_br_pis_ret_valor': l10n_br_pis_ret_valor,
                'l10n_br_cofins_ret_valor': l10n_br_cofins_ret_valor,
                'l10n_br_total_nfe': l10n_br_total_nfe,
                'l10n_br_total_tributos': l10n_br_total_tributos,
            })

    def _get_default_journal(self):

        journal_id = super(AccountMove, self)._get_default_journal()
        if self.company_id.country_id != self.env.ref('base.br'):
            return journal_id

        journal = None
        
        if self.l10n_br_tipo_pedido in TIPO_PEDIDO_SAIDA_NO_PAYMENT or self.l10n_br_tipo_pedido_entrada in TIPO_PEDIDO_ENTRADA_NO_PAYMENT:
            move_type = self._context.get('default_type', 'entry')
            journal_type = 'general'
            if move_type in self.get_sale_types(include_receipts=True):
                journal_type = 'sale'
            elif move_type in self.get_purchase_types(include_receipts=True):
                journal_type = 'purchase'

            company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', journal_type), ('l10n_br_no_payment', '=', True), ('l10n_br_tipo_pedido', '=', self.l10n_br_tipo_pedido), ('l10n_br_tipo_pedido_entrada', '=', self.l10n_br_tipo_pedido_entrada)]

            if self._context.get('default_currency_id'):
                currency_domain = domain + [('currency_id', '=', self._context['default_currency_id'])]
                journal = self.env['account.journal'].search(currency_domain, limit=1)

            if not journal:
                journal = self.env['account.journal'].search(domain, limit=1)

        return journal or journal_id

    @api.onchange('l10n_br_tipo_pedido','l10n_br_tipo_pedido_entrada')
    def _onchange_l10n_br_tipo_pedido(self):
        self.journal_id = self._get_default_journal().id
        self.fiscal_position_id = self.journal_id.fiscal_position_id.id
        self._onchange_recompute_dynamic_lines()

    @api.onchange('l10n_br_situacao_nf')
    def change_l10n_br_situacao_nf(self):
        for move in self:
            if move.l10n_br_situacao_nf == 'cancelado':
                move.state = 'cancel'

    def _recompute_payment_terms_lines(self):
        
        if self.company_id.country_id != self.env.ref('base.br'):
            return super(AccountMove, self)._recompute_payment_terms_lines()

        #_logger.info('_recompute_payment_terms_lines')

        
        ''' Compute the dynamic payment term lines of the journal entry.'''
        self.ensure_one()
        in_draft_mode = self != self._origin
        today = fields.Date.context_today(self)
        self = self.with_context(force_company=self.journal_id.company_id.id)

        def _get_payment_terms_computation_date(self):

            #_logger.info('_recompute_payment_terms_lines._get_payment_terms_computation_date')

            ''' Get the date from invoice that will be used to compute the payment terms.
            :param self:    The current account.move record.
            :return:        A datetime.date object.
            '''
            if self.invoice_payment_term_id:
                return self.invoice_date or today
            else:
                return self.invoice_date_due or self.invoice_date or today

        def _get_payment_terms_account(self, payment_terms_lines):

            #_logger.info('_recompute_payment_terms_lines._get_payment_terms_account')

            ''' Get the account from invoice that will be set as receivable / payable account.
            :param self:                    The current account.move record.
            :param payment_terms_lines:     The current payment terms lines.
            :return:                        An account.account record.
            '''
            if self.journal_id.l10n_br_no_payment:
                return self.journal_id.account_no_payment_id
            elif payment_terms_lines:
                # Retrieve account from previous payment terms lines in order to allow the user to set a custom one.
                return payment_terms_lines[0].account_id
            elif self.partner_id:
                # Retrieve account from partner.
                if self.is_sale_document(include_receipts=True):
                    return self.partner_id.property_account_receivable_id
                else:
                    return self.partner_id.property_account_payable_id
            else:
                # Search new account.
                domain = [
                    ('company_id', '=', self.company_id.id),
                    ('internal_type', '=', 'receivable' if self.type in ('out_invoice', 'out_refund', 'out_receipt') else 'payable'),
                ]
                return self.env['account.account'].search(domain, limit=1)

        def _compute_payment_terms(self, date, total_balance, total_amount_currency):

            #_logger.info('_recompute_payment_terms_lines._compute_payment_terms')

            ''' Compute the payment terms.
            :param self:                    The current account.move record.
            :param date:                    The date computed by '_get_payment_terms_computation_date'.
            :param total_balance:           The invoice's total in company's currency.
            :param total_amount_currency:   The invoice's total in invoice's currency.
            :return:                        A list <to_pay_company_currency, to_pay_invoice_currency, due_date>.
            '''
            result = []
            if self.dfe_id and len(self.dfe_id.dups_ids) > 0:
                for idx, dup_id in enumerate(self.dfe_id.dups_ids):
                    cobr_dup_vdup = dup_id.cobr_dup_vdup
                    total_balance -= cobr_dup_vdup
                    if idx == len(self.dfe_id.dups_ids)-1 and total_balance > 0.00 and total_balance < 0.1:
                        cobr_dup_vdup += total_balance
                    result.append((fields.Date.to_string(dup_id.cobr_dup_dvenc), cobr_dup_vdup, cobr_dup_vdup))

            elif self.invoice_payment_term_id:
                if self.currency_id != self.company_id.currency_id:
                    to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.currency_id)
                    # Multi-currencies.
                    to_compute_currency = self.invoice_payment_term_id.compute(total_amount_currency, date_ref=date, currency=self.currency_id)
                    result = [(b[0], b[1], ac[1]) for b, ac in zip(to_compute, to_compute_currency)]
                else:
                    # Single-currency.
                    # remove ICMSST do rateio das parcelas
                    l10n_br_icmsst_valor = self.l10n_br_icmsst_valor
                    l10n_br_icmsst_valor *= -1 if total_balance<0 else 1
                    total_balance -= l10n_br_icmsst_valor
                    to_compute = self.invoice_payment_term_id.compute(total_balance, date_ref=date, currency=self.currency_id)
                    # adiciona ICMSST na primeira parcela
                    result = [(b[0], b[1] + (l10n_br_icmsst_valor if i == 0 else 0.0), 0.0) for i, b in enumerate(to_compute)]
            else:
                result = [(fields.Date.to_string(date), total_balance, total_amount_currency)]

            return result

        def _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute):

            #_logger.info('_recompute_payment_terms_lines._compute_diff_payment_terms_lines')

            ''' Process the result of the '_compute_payment_terms' method and creates/updates corresponding invoice lines.
            :param self:                    The current account.move record.
            :param existing_terms_lines:    The current payment terms lines.
            :param account:                 The account.account record returned by '_get_payment_terms_account'.
            :param to_compute:              The list returned by '_compute_payment_terms'.
            '''
            # As we try to update existing lines, sort them by due date.
            existing_terms_lines = existing_terms_lines.sorted(lambda line: line.date_maturity or today)
            existing_terms_lines_index = 0

            # Recompute amls: update existing line or create new one for each payment term.
            new_terms_lines = self.env['account.move.line']
            for date_maturity, balance, amount_currency in to_compute:
                if self.journal_id.company_id.currency_id.is_zero(balance) and len(to_compute) > 1:
                    continue

                date_maturity = False if self.journal_id.l10n_br_no_payment else date_maturity
                if existing_terms_lines_index < len(existing_terms_lines):
                    # Update existing line.
                    candidate = existing_terms_lines[existing_terms_lines_index]
                    existing_terms_lines_index += 1
                    candidate.update({
                        'date_maturity': date_maturity,
                        'amount_currency': -amount_currency,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                    })
                else:
                    # Create new line.
                    create_method = in_draft_mode and self.env['account.move.line'].new or self.env['account.move.line'].create
                    candidate = create_method({
                        'name': self.invoice_payment_ref or '',
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'quantity': 1.0,
                        'amount_currency': -amount_currency,
                        'date_maturity': date_maturity,
                        'move_id': self.id,
                        'currency_id': self.currency_id.id if self.currency_id != self.company_id.currency_id else False,
                        'account_id': account.id,
                        'partner_id': self.commercial_partner_id.id,
                        'exclude_from_invoice_tab': True,
                    })
                new_terms_lines += candidate
                if in_draft_mode:
                    candidate._onchange_amount_currency()
                    candidate._onchange_balance()
            return new_terms_lines

        existing_terms_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
        others_lines = self.line_ids.filtered(lambda line: line.account_id.user_type_id.type not in ('receivable', 'payable'))
        company_currency_id = self.company_id.currency_id
        total_balance = sum(others_lines.mapped(lambda l: company_currency_id.round(l.balance)))
        total_amount_currency = sum(others_lines.mapped('amount_currency'))

        if not others_lines:
            self.line_ids -= existing_terms_lines
            return

        computation_date = _get_payment_terms_computation_date(self)
        account = _get_payment_terms_account(self, existing_terms_lines)
        to_compute = _compute_payment_terms(self, computation_date, total_balance, total_amount_currency)
        #_logger.info([to_compute,self.dfe_id])
        new_terms_lines = _compute_diff_payment_terms_lines(self, existing_terms_lines, account, to_compute)

        # Remove old terms lines that are no longer needed.
        self.line_ids -= existing_terms_lines - new_terms_lines

        if new_terms_lines:
            self.invoice_payment_ref = new_terms_lines[-1].name or ''
            self.invoice_date_due = new_terms_lines[-1].date_maturity

class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = ['account.move.line','mail.thread']

    dfe_line_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe.line', string='Item Documento Fiscal', check_company=True )
    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', check_company=True )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP' )
    l10n_br_cfop_codigo = fields.Char( related='l10n_br_cfop_id.codigo_cfop' )
    l10n_br_frete = fields.Float( string='Frete' )
    l10n_br_seguro = fields.Float( string='Seguro' )
    l10n_br_despesas_acessorias = fields.Float( string='Despesas Acessórias' )
    l10n_br_desc_valor = fields.Float( string='Valor do Desconto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_prod_valor = fields.Float( string='Valor do Produto', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_nfe = fields.Float( string='Valor do Item do Pedido', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_total_tributos = fields.Float( string='Valor dos Tributos', store=True, readonly=True, compute_sudo=False, compute='_l10n_br_amount_all' )
    l10n_br_informacao_adicional = fields.Text( string='Informações Adicionais' )
    l10n_br_pedido_compra = fields.Char( string='Pedido de Compra do Cliente', default=lambda self: self.move_id.l10n_br_pedido_compra )
    l10n_br_item_pedido_compra = fields.Char( string='Item Pedido de Compra do Cliente', default=lambda self: self.move_id.l10n_br_item_pedido_compra )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )
    l10n_br_mensagem_fiscal_ids = fields.Many2many( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal' )

    l10n_br_imposto_auto = fields.Boolean( related='move_id.l10n_br_imposto_auto' )
    l10n_br_calcular_imposto = fields.Boolean( related='move_id.l10n_br_calcular_imposto' )

    l10n_br_tipo_pedido_str = fields.Char( string='Tipo de Pedido', compute='_get_l10n_br_tipo_pedido_str', store=True )
    l10n_br_tipo_pedido = fields.Selection( related='move_id.l10n_br_tipo_pedido', store=True )
    l10n_br_tipo_pedido_entrada = fields.Selection( related='move_id.l10n_br_tipo_pedido_entrada', store=True )

    l10n_br_icms_modalidade_base = fields.Selection( MODALIDADE_ICMS, string='Modalidade de Determinação da BC do ICMS' )
    l10n_br_icms_reducao_base = fields.Float( string='Aliquota de Redução da BC do ICMS (%)', digits = (12,4) )
    l10n_br_icms_diferido_valor_operacao = fields.Float( string='Valor do ICMS da Operação' )
    l10n_br_icms_diferido_aliquota = fields.Float( string='Aliquota do ICMS Diferido (%)' )
    l10n_br_icms_diferido_valor = fields.Float( string='Valor do ICMS Diferido' )

    l10n_br_icms_cst = fields.Selection( ICMS_CST, string='Código de Situação Tributária do ICMS' )
    l10n_br_icms_base = fields.Float( string='Valor da Base de Cálculo do ICMS' )
    l10n_br_icms_aliquota = fields.Float( string='Aliquota do ICMS (%)' )
    l10n_br_icms_valor = fields.Float( string='Valor do ICMS (Tributável)' )
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
    l10n_br_ipi_valor = fields.Float( string='Valor do IPI (Tributável)' )
    l10n_br_ipi_valor_isento = fields.Float( string='Valor do IPI (Isento/Não Tributável)' )
    l10n_br_ipi_valor_outros = fields.Float( string='Valor do IPI (Outros)' )

    l10n_br_ipi_cnpj = fields.Char( string='CNPJ do produtor da mercadoria' )
    l10n_br_ipi_selo_codigo = fields.Char( string='Código do selo de controle IPI' )
    l10n_br_ipi_selo_quantidade = fields.Integer( string='Quantidade de selo de controle' )
    l10n_br_ipi_enq = fields.Char( string='Código Enquadramento' )

    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_pis_base = fields.Float( string='Valor da Base de Cálculo do PIS' )
    l10n_br_pis_aliquota = fields.Float( string='Aliquota do PIS (%)' )
    l10n_br_pis_valor = fields.Float( string='Valor do PIS (Tributável)' )
    l10n_br_pis_valor_isento = fields.Float( string='Valor do PIS (Isento/Não Tributável)' )
    l10n_br_pis_valor_outros = fields.Float( string='Valor do PIS (Outros)' )

    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )
    l10n_br_cofins_base = fields.Float( string='Valor da Base de Cálculo do Cofins' )
    l10n_br_cofins_aliquota = fields.Float( string='Aliquota do Cofins (%)' )
    l10n_br_cofins_valor = fields.Float( string='Valor do Cofins (Tributável)' )
    l10n_br_cofins_valor_isento = fields.Float( string='Valor do Cofins (Isento/Não Tributável)' )
    l10n_br_cofins_valor_outros = fields.Float( string='Valor do Cofins (Outros)' )

    l10n_br_ii_base = fields.Float( string='Valor da Base de Cálculo do II' )
    l10n_br_ii_aliquota = fields.Float( string='Aliquota do II (%)' )
    l10n_br_ii_valor = fields.Float( string='Valor do II (Tributável)' )
    l10n_br_ii_valor_aduaneira = fields.Float( string='Valor do II (Aduaneira)' )
    l10n_br_di_adicao_id = fields.Many2one('l10n_br_ciel_it_account.di.adicao', string='DI/Adição')
    
    l10n_br_iss_base = fields.Float( string='Valor da Base de Cálculo do ISS' )
    l10n_br_iss_aliquota = fields.Float( string='Aliquota do ISS (%)' )
    l10n_br_iss_valor = fields.Float( string='Valor do ISS' )

    l10n_br_irpj_base = fields.Float( string='Valor da Base de Cálculo do IRPJ' )
    l10n_br_irpj_aliquota = fields.Float( string='Aliquota do IRPJ (%)' )
    l10n_br_irpj_valor = fields.Float( string='Valor do IRPJ' )

    l10n_br_csll_base = fields.Float( string='Valor da Base de Cálculo do CSLL' )
    l10n_br_csll_aliquota = fields.Float( string='Aliquota do CSLL (%)' )
    l10n_br_csll_valor = fields.Float( string='Valor do CSLL' )

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

    l10n_br_cobranca_idintegracao = fields.Char( string='Id Integração', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_transmissao = fields.Selection( TIPO_TRANSMISSAO, string='Tipo Transmissão', default='webservice', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_arquivo_remessa = fields.Char( string='Arquivo Remessa', default='', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_protocolo = fields.Char( string='Protocolo', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_parcela = fields.Integer( string='Parcela', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_nossonumero = fields.Char( string='Nosso Numero', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_situacao = fields.Selection( SITUACAO_COBRANCA, string='Situação', copy=False, track_visibility='onchange' )
    l10n_br_cobranca_situacao_mensagem = fields.Char( string='Mensagem', copy=False, track_visibility='onchange' )

    l10n_br_pdf_boleto = fields.Binary( string="Boleto", copy=False )
    l10n_br_pdf_boleto_fname = fields.Char( string="Arquivo Boleto", compute="_get_l10n_br_pdf_boleto_fname" )
    
    l10n_br_paga = fields.Boolean( string='Parcela Paga?', default=False, copy=False )

    def pagar_boleto(self):
        return

    @api.depends('l10n_br_tipo_pedido', 'l10n_br_tipo_pedido_entrada')
    def _get_l10n_br_tipo_pedido_str(self):
        for record in self:
            l10n_br_tipo_pedido_str = ""
            if record.l10n_br_tipo_pedido:
                l10n_br_tipo_pedido_str = dict(TIPO_PEDIDO_SAIDA)[record.l10n_br_tipo_pedido] 
            if record.l10n_br_tipo_pedido_entrada:
                l10n_br_tipo_pedido_str = dict(TIPO_PEDIDO_ENTRADA)[record.l10n_br_tipo_pedido_entrada] 
            record.l10n_br_tipo_pedido_str = l10n_br_tipo_pedido_str

    def _get_l10n_br_pdf_boleto_fname(self):
        for record in self:
            record.l10n_br_pdf_boleto_fname = "%s-%s-boleto.pdf" % (record.move_id.l10n_br_numero_nf,str(record.l10n_br_cobranca_parcela).zfill(3))

    @api.model
    def _handle_taxes(self, name, tax_key, price_include, amount, fixed):

        type_tax_use = 'sale' if TIPO_NF_OPERACAO[self.move_id.type] == 'saida' else 'purchase'
        amount_type = 'fixed_total' if fixed else 'percent'

        company = self.env.company
        tax_master = self.env['account.tax'].sudo().search([
            ('name', '=', name+'[*]'),
            ('amount_type', '=', amount_type),
            ('amount', '=', 0.00),
            ('company_id', '=', company.id),
            ('price_include', '=', price_include),
            ('type_tax_use', '=', type_tax_use)], limit=1)
        if not tax_master:
            tax_master = self.env['account.tax'].sudo().create({
                'name': name+'[*]',
                'amount': 0.00,
                'amount_type': amount_type,
                'type_tax_use': type_tax_use,
                'description': name,
                'company_id': company.id,
                'price_include': price_include,
                'active': True,
            })

        tax = self.env['account.tax'].sudo().search([
            ('name', '=', name+'['+tax_key+']'),
            ('company_id', '=', company.id),
            ('price_include', '=', price_include),
            ('type_tax_use', '=', type_tax_use)], limit=1)
        if not tax:
            tax = tax_master.copy()
        tax.update({'name': name+'['+tax_key+']', 'description': name, 'amount_type': amount_type, 'amount': amount})

        return tax

    def l10n_br_compute_tax_id(self):
        for line in self.with_context(check_move_validity=False):

            tax_key = str(uuid.uuid4())[:8]
            line.update({'tax_ids': [(5,)]})

            if line.move_id.l10n_br_tipo_pedido_entrada == 'importacao':
                ## ICMS ##
                amount = line.l10n_br_icms_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    # Lucro Presumido remove ICMS do Total da NF
                    if line.move_id.company_id.l10n_br_incidencia_cumulativa == '2' and line.move_id.company_id.l10n_br_regime_tributario == '3':
                        tax_icms_id = line._handle_taxes('ICMS EX', tax_key, True, amount, True)
                        line.update({'tax_ids': [(4, tax_icms_id.id)]})
                    else:
                        tax_icms_id = line._handle_taxes('ICMS EX', tax_key, False, amount, True)
                        line.update({'tax_ids': [(4, tax_icms_id.id)]})
            else:
                ## ICMS ##
                amount = line.l10n_br_icms_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_icms_id = line._handle_taxes('ICMS', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_isento # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS ISENTO', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_outros # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS OUTROS', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icms_id.id)]})

            amount = line.l10n_br_icms_valor_desonerado # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS DESONERADO', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icms_id.id)]})

            ## ICMSST ##
            amount = line.l10n_br_icmsst_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_valor_outros # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST OUTROS', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_substituto_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST SUB', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_substituto_valor_outros # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST SUB OUTROS', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_retido_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST RET', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            amount = line.l10n_br_icmsst_retido_valor_outros # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST RET OUTROS', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_icmsst_id.id)]})

            ## IPI ##
            amount = line.l10n_br_ipi_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_ipi_id.id)]})

            amount = line.l10n_br_ipi_valor_isento # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI ISENTO', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_ipi_id.id)]})

            amount = line.l10n_br_ipi_valor_outros # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI OUTROS', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_ipi_id.id)]})

            if line.move_id.l10n_br_tipo_pedido_entrada == 'importacao':
                ## PIS ##
                amount = line.l10n_br_pis_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_isento # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS ISENTO EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_outros # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS OUTROS EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                ## COFINS ##
                amount = line.l10n_br_cofins_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_isento # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS ISENTO EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_outros # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS OUTROS EX', tax_key, False, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

            else:

                ## PIS ##
                amount = line.l10n_br_pis_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_isento # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS ISENTO', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                amount = line.l10n_br_pis_valor_outros # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_pis_id = line._handle_taxes('PIS OUTROS', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_pis_id.id)]})

                ## COFINS ##
                amount = line.l10n_br_cofins_valor # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_isento # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS ISENTO', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

                amount = line.l10n_br_cofins_valor_outros # / (line.quantity or 1.00)
                if amount != 0.00:
                    tax_cofins_id = line._handle_taxes('COFINS OUTROS', tax_key, True, amount, True)
                    line.update({'tax_ids': [(4, tax_cofins_id.id)]})

            ## II ##
            amount = line.l10n_br_ii_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_ii_id = line._handle_taxes('II', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_ii_id.id)]})

            ## ADUANEIRA ##
            amount = line.l10n_br_ii_valor_aduaneira # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_ii_id = line._handle_taxes('ADUANEIRA', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_ii_id.id)]})

            ## ISS ##
            amount = line.l10n_br_iss_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_iss_id = line._handle_taxes('ISS', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_iss_id.id)]})

            ## IRPJ ##
            amount = line.l10n_br_irpj_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_irpj_id = line._handle_taxes('IRPJ', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_irpj_id.id)]})

            ## CSLL ##
            amount = line.l10n_br_csll_valor # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_csll_id = line._handle_taxes('CSLL', tax_key, True, amount, True)
                line.update({'tax_ids': [(4, tax_csll_id.id)]})

            ## CSLL RET ##
            amount = line.l10n_br_csll_ret_aliquota
            if amount != 0.00:
                tax_csll_ret_id = line._handle_taxes('CSLL RET', tax_key, False, amount, False)
                line.update({'tax_ids': [(4, tax_csll_ret_id.id)]})

            ## IRPJ RET ##
            amount = line.l10n_br_irpj_ret_aliquota
            if amount != 0.00:
                tax_irpj_ret_id = line._handle_taxes('IRPJ RET', tax_key, False, amount, False)
                line.update({'tax_ids': [(4, tax_irpj_ret_id.id)]})

            ## INSS RET ##
            amount = line.l10n_br_inss_ret_aliquota
            if amount != 0.00:
                tax_inss_ret_id = line._handle_taxes('INSS RET', tax_key, False, amount, False)
                line.update({'tax_ids': [(4, tax_inss_ret_id.id)]})

            ## PIS RET ##
            amount = line.l10n_br_pis_ret_aliquota
            if amount != 0.00:
                tax_pis_ret_id = line._handle_taxes('PIS RET', tax_key, False, amount, False)
                line.update({'tax_ids': [(4, tax_pis_ret_id.id)]})

            ## COFINS RET ##
            amount = line.l10n_br_cofins_ret_aliquota
            if amount != 0.00:
                tax_cofins_ret_id = line._handle_taxes('COFINS RET', tax_key, False, amount, False)
                line.update({'tax_ids': [(4, tax_cofins_ret_id.id)]})

            ## FRETE ##
            amount = line.l10n_br_frete # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_frete_id = line._handle_taxes('FRETE', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_frete_id.id)]})

            ## SEGURO ##
            amount = line.l10n_br_seguro # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_seguro_id = line._handle_taxes('SEGURO', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_seguro_id.id)]})

            ## DESPESAS ##
            amount = line.l10n_br_despesas_acessorias # / (line.quantity or 1.00)
            if amount != 0.00:
                tax_despesas_id = line._handle_taxes('DESPESAS', tax_key, False, amount, True)
                line.update({'tax_ids': [(4, tax_despesas_id.id)]})

    @api.onchange('product_id')
    def l10n_br_onchange_product_id(self):
        for item in self:
            item._do_update_l10n_br_informacao_adicional()

    def _do_update_l10n_br_informacao_adicional(self):

        ################################
        ##### INFORMAÇÃO ADICIONAL #####
        ################################
        values_to_update = {}
        values_to_update['l10n_br_informacao_adicional'] = self.product_id.l10n_br_informacao_adicional
        self.update(values_to_update)

    def _do_calculate_l10n_br_impostos(self):

        self.ensure_one()

        if self.l10n_br_imposto_auto:
            
            ##############################
            ##### DETERMINA OPERAÇÃO #####
            ##############################
            values_to_update = {}

            values_to_update['l10n_br_operacao_id'] = False

            l10n_br_tipo_operacao = TIPO_NF_OPERACAO[self.move_id.type]

            if l10n_br_tipo_operacao == 'saida':
                domain = [('l10n_br_tipo_operacao','=',l10n_br_tipo_operacao),('l10n_br_tipo_pedido','=',self.move_id.l10n_br_tipo_pedido)]
            else:
                domain = [('l10n_br_tipo_operacao','=',l10n_br_tipo_operacao),('l10n_br_tipo_pedido_entrada','=',self.move_id.l10n_br_tipo_pedido_entrada)]

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
            if self.move_id.partner_id.l10n_br_cpf:
                l10n_br_tipo_cliente = 'pf'
            if self.move_id.company_id.country_id != self.move_id.partner_id.country_id:
                l10n_br_tipo_cliente = 'ex'
            if self.move_id.partner_id.l10n_br_is:
                l10n_br_tipo_cliente = 'zf'
        
            domain_aux = expression.OR([
                [('l10n_br_tipo_cliente','=',l10n_br_tipo_cliente)],
                [('l10n_br_tipo_cliente','=',False)],
                [('l10n_br_tipo_cliente','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            domain_aux = expression.OR([
                [('l10n_br_indicador_ie','=',self.move_id.partner_id.l10n_br_indicador_ie)],
                [('l10n_br_indicador_ie','=',False)],
                [('l10n_br_indicador_ie','=','')],
            ])
            domain = expression.AND([domain,domain_aux])

            l10n_br_destino_operacao = ''
            if self.move_id.company_id.state_id == self.move_id.partner_id.state_id:
                l10n_br_destino_operacao = '1' # 1 - Operação interna
            elif self.move_id.company_id.country_id != self.move_id.partner_id.country_id:
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

            ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
            ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.move_id.partner_id.id)],limit=1)
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
                [('partner_ids','in',self.move_id.partner_id.id)],
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
                if self.move_id.company_id.state_id == self.move_id.partner_id.state_id:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_intra_cfop_id.id
                elif self.move_id.company_id.country_id != self.move_id.partner_id.country_id:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_ext_cfop_id.id
                else:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_inter_cfop_id.id

            self.update(values_to_update)
            self.move_id.update(values_to_update)

            #############################
            ##### OBSERVAÇÃO FISCAL #####
            #############################
            if self.l10n_br_operacao_id.l10n_br_mensagem_fiscal_id:
                values_to_update = {}
                
                values_to_update['l10n_br_mensagem_fiscal_ids'] = [(6, 0, [self.l10n_br_operacao_id.l10n_br_mensagem_fiscal_id.id])]

                self.update(values_to_update)

            if self._context.get('update_tax', True):

                if self.move_id.l10n_br_tipo_pedido_entrada:
                    ################
                    ###### IPI #####
                    ################
                    #values_to_update = {}
                    #
                    #values_to_update['l10n_br_ipi_cst'] = False
                    #values_to_update['l10n_br_ipi_base'] = False
                    #values_to_update['l10n_br_ipi_aliquota'] = False
                    #values_to_update['l10n_br_ipi_valor'] = False
                    #values_to_update['l10n_br_ipi_valor_isento'] = False
                    #values_to_update['l10n_br_ipi_valor_outros'] = False
                    #values_to_update['l10n_br_ipi_enq'] = False
                    #
                    #self.update(values_to_update)

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

                        elif values_to_update['l10n_br_icms_cst'] == '900':
                            values_to_update['l10n_br_icms_modalidade_base'] = '3'

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

                    ###################
                    ##### ISS RET #####
                    ###################
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
        
                elif self.move_id.l10n_br_tipo_pedido:

                    #_logger.info(['_do_calculate_l10n_br_impostos','PASSO 4'])

                    ###############
                    ##### IPI #####
                    ###############
                    values_to_update = {}

                    # Simples Nacional ou Simples Nacional, excesso sublimite de receita bruta
                    values_to_update['l10n_br_ipi_cst'] = '99'
                    values_to_update['l10n_br_ipi_base'] = 0.00
                    values_to_update['l10n_br_ipi_aliquota'] = 0.00
                    values_to_update['l10n_br_ipi_valor'] = 0.00
                    values_to_update['l10n_br_ipi_valor_isento'] = 0.00
                    values_to_update['l10n_br_ipi_valor_outros'] = 0.00
                    values_to_update['l10n_br_ipi_enq'] = ''

                    if self.product_id.l10n_br_ncm_id.l10n_br_ipi_cst:
                        values_to_update['l10n_br_ipi_cst'] = self.product_id.l10n_br_ncm_id.l10n_br_ipi_cst

                    if self.l10n_br_cfop_id.l10n_br_ipi_cst:
                        values_to_update['l10n_br_ipi_cst'] = self.l10n_br_cfop_id.l10n_br_ipi_cst
                    if self.l10n_br_operacao_id.l10n_br_ipi_cst:
                        values_to_update['l10n_br_ipi_cst'] = self.l10n_br_operacao_id.l10n_br_ipi_cst

                    values_to_update['l10n_br_ipi_base'] = 0.00
                    if values_to_update['l10n_br_ipi_cst'] == '50':
                        values_to_update['l10n_br_ipi_base'] = self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor

                    values_to_update['l10n_br_ipi_aliquota'] = 0.00
                    if values_to_update['l10n_br_ipi_cst'] == '50':
                        values_to_update['l10n_br_ipi_aliquota'] = self.product_id.l10n_br_ncm_id.l10n_br_ipi_aliquota

                    values_to_update['l10n_br_ipi_valor'] = round(values_to_update['l10n_br_ipi_base'] * values_to_update['l10n_br_ipi_aliquota'] / 100.00, 2)
                    values_to_update['l10n_br_ipi_valor_isento'] = 0.00
                    values_to_update['l10n_br_ipi_valor_outros'] = 0.00

                    ipi_enquadramento = self.env["l10n_br_ciel_it_account.ipi.enquadramento"].search([('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('l10n_br_cfop_id','=',self.l10n_br_cfop_id.id),('l10n_br_ipi_cst','=',values_to_update['l10n_br_ipi_cst'])],limit=1)
                    values_to_update['l10n_br_ipi_enq'] = ipi_enquadramento.l10n_br_codigo_enquadramento if ipi_enquadramento else self.product_id.l10n_br_ncm_id.l10n_br_ipi_enq

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

                    l10n_br_icms_modalidade_base = '3'
                    l10n_br_icms_aliquota = 0.00
                    l10n_br_icms_reducao_base = 0.00
                    l10n_br_icms_diferido_aliquota = 0.00

                    l10n_br_icmsst_modalidade_base = ''
                    l10n_br_icmsst_mva = 0.00
                    l10n_br_icmsst_reducao_base = 0.00
                    l10n_br_icmsst_aliquota = 0.00
                    l10n_br_icmsst_icmsfora = False

                    l10n_br_mensagem_fiscal_id = False

                    # Regime Normal
                    if self.move_id.company_id.l10n_br_regime_tributario == '3':
                        values_to_update['l10n_br_icms_cst'] = '00'
                        icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id)],limit=1)
                        if icms_uf:
                            if self.move_id.company_id.state_id != self.move_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
                                l10n_br_icms_aliquota = icms_uf.l10n_br_icms_ext_aliquota
                            else:
                                l10n_br_icms_aliquota = icms_uf.l10n_br_icms_aliquota
                    else:
                        values_to_update['l10n_br_icms_cst'] = '101'

                    ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
                    ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.move_id.partner_id.id)],limit=1)
                    if ncm_cliente_uf:
                        ncm_uf = ncm_cliente_uf

                    if ncm_uf:
                        values_to_update['l10n_br_icms_cst'] = ncm_uf.l10n_br_icms_cst
                        if ncm_uf.l10n_br_icms_modalidade_base:
                            l10n_br_icms_modalidade_base = ncm_uf.l10n_br_icms_modalidade_base
                            l10n_br_icms_aliquota = ncm_uf.l10n_br_icms_aliquota
                            if values_to_update['l10n_br_icms_cst'] == '51':
                                l10n_br_icms_diferido_aliquota = ncm_uf.l10n_br_icms_reducao_base
                            else:
                                l10n_br_icms_reducao_base = ncm_uf.l10n_br_icms_reducao_base
                        if ncm_uf.l10n_br_icmsst_modalidade_base:
                            l10n_br_icmsst_modalidade_base = ncm_uf.l10n_br_icmsst_modalidade_base
                            l10n_br_icmsst_mva = ncm_uf.l10n_br_icmsst_mva
                            l10n_br_icmsst_reducao_base = ncm_uf.l10n_br_icmsst_reducao_base
                            l10n_br_icmsst_aliquota = ncm_uf.l10n_br_icmsst_aliquota
                            l10n_br_icmsst_icmsfora = ncm_uf.l10n_br_icmsst_icmsfora
                        l10n_br_mensagem_fiscal_id = ncm_uf.l10n_br_mensagem_fiscal_id.id

                    if self.l10n_br_operacao_id.l10n_br_icms_cst:
                        values_to_update['l10n_br_icms_cst'] = self.l10n_br_operacao_id.l10n_br_icms_cst
                        if self.l10n_br_operacao_id.l10n_br_icms_modalidade_base:
                            l10n_br_icms_modalidade_base = self.l10n_br_operacao_id.l10n_br_icms_modalidade_base
                            l10n_br_icms_aliquota = self.l10n_br_operacao_id.l10n_br_icms_aliquota
                            if values_to_update['l10n_br_icms_cst'] == '51':
                                l10n_br_icms_diferido_aliquota = self.l10n_br_operacao_id.l10n_br_icms_reducao_base
                            else:
                                l10n_br_icms_reducao_base = self.l10n_br_operacao_id.l10n_br_icms_reducao_base

                        else:
                            icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id)],limit=1)
                            if icms_uf:
                                if self.move_id.company_id.state_id != self.move_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
                                    l10n_br_icms_aliquota = icms_uf.l10n_br_icms_ext_aliquota
                                else:
                                    l10n_br_icms_aliquota = icms_uf.l10n_br_icms_aliquota

                        if self.l10n_br_operacao_id.l10n_br_icmsst_modalidade_base:
                            l10n_br_icmsst_modalidade_base = self.l10n_br_operacao_id.l10n_br_icmsst_modalidade_base
                            l10n_br_icmsst_mva = self.l10n_br_operacao_id.l10n_br_icmsst_mva
                            l10n_br_icmsst_reducao_base = self.l10n_br_operacao_id.l10n_br_icmsst_reducao_base
                            l10n_br_icmsst_aliquota = self.l10n_br_operacao_id.l10n_br_icmsst_aliquota
                            l10n_br_icmsst_icmsfora = self.l10n_br_operacao_id.l10n_br_icmsst_icmsfora

                    l10n_br_icms_base = self.l10n_br_total_nfe - self.l10n_br_icmsst_valor
                    if self.move_id.l10n_br_operacao_consumidor == '0' and \
                    self.move_id.partner_id.l10n_br_indicador_ie != '9' and \
                    (self.l10n_br_compra_indcom and self.l10n_br_compra_indcom != 'uso'):
                        l10n_br_icms_base -= self.l10n_br_ipi_valor
                    l10n_br_icms_base = round(l10n_br_icms_base * (1.00 - (l10n_br_icms_reducao_base/100.00)), 2)
                    l10n_br_icms_valor = round(l10n_br_icms_base * l10n_br_icms_aliquota / 100.00, 2)

                    l10n_br_icmsst_base = self.l10n_br_total_nfe - self.l10n_br_icmsst_valor
                    l10n_br_icmsst_base = round(l10n_br_icmsst_base * (1.00 + (l10n_br_icmsst_mva/100.00)), 2)
                    l10n_br_icmsst_base = round(l10n_br_icmsst_base * (1.00 - (l10n_br_icmsst_reducao_base/100.00)), 2)
                    l10n_br_icmsst_valor = round(l10n_br_icmsst_base * l10n_br_icmsst_aliquota / 100.00, 2)
                    if l10n_br_icmsst_valor > 0.00:
                        if not l10n_br_icmsst_icmsfora:
                            l10n_br_icmsst_valor -= l10n_br_icms_valor

                        # Se Simples Nacional subtrai valor ICMS Teorico do valor do ICMS-ST
                        if self.move_id.company_id.l10n_br_regime_tributario != '3':
                            l10n_br_icms_aliquota_sn = 0.00
                            icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id)],limit=1)
                            if icms_uf:
                                if self.move_id.company_id.state_id != self.move_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
                                    l10n_br_icms_aliquota_sn = icms_uf.l10n_br_icms_ext_aliquota
                                else:
                                    l10n_br_icms_aliquota_sn = icms_uf.l10n_br_icms_aliquota
                            
                            if l10n_br_icms_aliquota_sn > 0.00:
                                l10n_br_icms_base_sn = self.l10n_br_total_nfe - self.l10n_br_icmsst_valor
                                l10n_br_icms_valor_sn = round(l10n_br_icms_base_sn * l10n_br_icms_aliquota_sn / 100.00, 2)
                                l10n_br_icmsst_valor -= l10n_br_icms_valor_sn

                    if l10n_br_mensagem_fiscal_id:
                        values_to_update['l10n_br_mensagem_fiscal_ids'] = [(4, l10n_br_mensagem_fiscal_id)]

                    if values_to_update['l10n_br_icms_cst'] == '00':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor

                    elif values_to_update['l10n_br_icms_cst'] == '10':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor
                
                    elif values_to_update['l10n_br_icms_cst'] == '20':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor
                        values_to_update['l10n_br_icms_reducao_base'] = l10n_br_icms_reducao_base
                        values_to_update['l10n_br_icms_valor_desonerado'] = ''
                        values_to_update['l10n_br_icms_motivo_desonerado'] = ''

                    elif values_to_update['l10n_br_icms_cst'] == '30':
                        values_to_update['l10n_br_icms_valor_desonerado'] = ''
                        values_to_update['l10n_br_icms_motivo_desonerado'] = ''

                    elif values_to_update['l10n_br_icms_cst'] in ['40','41','50']:
                        values_to_update['l10n_br_icms_valor_desonerado'] = ''
                        values_to_update['l10n_br_icms_motivo_desonerado'] = ''
                
                    elif values_to_update['l10n_br_icms_cst'] == '51':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_diferido_valor_operacao'] = l10n_br_icms_valor
                        values_to_update['l10n_br_icms_diferido_aliquota'] = l10n_br_icms_diferido_aliquota
                        values_to_update['l10n_br_icms_diferido_valor'] = round(l10n_br_icms_valor * l10n_br_icms_diferido_aliquota / 100, 2)
                        values_to_update['l10n_br_icms_valor'] = round(l10n_br_icms_valor - values_to_update['l10n_br_icms_diferido_valor'], 2)

                    elif values_to_update['l10n_br_icms_cst'] == '60':
                        pass

                    elif values_to_update['l10n_br_icms_cst'] == '70':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor
                        values_to_update['l10n_br_icms_reducao_base'] = l10n_br_icms_reducao_base
                        values_to_update['l10n_br_icms_valor_desonerado'] = ''
                        values_to_update['l10n_br_icms_motivo_desonerado'] = ''

                    elif values_to_update['l10n_br_icms_cst'] == '90':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor
                        values_to_update['l10n_br_icms_reducao_base'] = l10n_br_icms_reducao_base
                        values_to_update['l10n_br_icms_valor_desonerado'] = ''
                        values_to_update['l10n_br_icms_motivo_desonerado'] = ''

                    elif values_to_update['l10n_br_icms_cst'] == '101':
                        values_to_update['l10n_br_icms_credito_aliquota'] = self.move_id.company_id.l10n_br_icms_credito_aliquota
                        values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self.move_id.company_id.l10n_br_icms_credito_aliquota / 100.00,2)
                
                    elif values_to_update['l10n_br_icms_cst'] == '102':
                        pass

                    elif values_to_update['l10n_br_icms_cst'] == '201':
                        values_to_update['l10n_br_icms_credito_aliquota'] = self.move_id.company_id.l10n_br_icms_credito_aliquota
                        values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self.move_id.company_id.l10n_br_icms_credito_aliquota / 100.00,2)

                    elif values_to_update['l10n_br_icms_cst'] == '202':
                        pass

                    elif values_to_update['l10n_br_icms_cst'] == '500':
                        pass

                    elif values_to_update['l10n_br_icms_cst'] == '900':
                        values_to_update['l10n_br_icms_modalidade_base'] = l10n_br_icms_modalidade_base
                        values_to_update['l10n_br_icms_base'] = l10n_br_icms_base
                        values_to_update['l10n_br_icms_aliquota'] = l10n_br_icms_aliquota
                        values_to_update['l10n_br_icms_valor'] = l10n_br_icms_valor
                        values_to_update['l10n_br_icms_reducao_base'] = l10n_br_icms_reducao_base
                        values_to_update['l10n_br_icms_credito_aliquota'] = self.move_id.company_id.l10n_br_icms_credito_aliquota
                        values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self.move_id.company_id.l10n_br_icms_credito_aliquota / 100.00,2)

                    icms_beneficio = self.env["l10n_br_ciel_it_account.icms.beneficio"].search(['|',('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('l10n_br_ncm_id','=',False),('l10n_br_cfop_id','=',self.l10n_br_cfop_id.id),('l10n_br_icms_cst','=',values_to_update['l10n_br_icms_cst'])],limit=1)
                    values_to_update['l10n_br_codigo_beneficio'] = icms_beneficio.l10n_br_codigo_beneficio if icms_beneficio else ''

                    self.update(values_to_update)

                    ##################
                    ##### ICMSST #####
                    ##################
                    values_to_update = {}

                    values_to_update['l10n_br_icmsst_modalidade_base'] = False
                    values_to_update['l10n_br_icmsst_reducao_base'] = False
                    values_to_update['l10n_br_icmsst_mva'] = False
                    values_to_update['l10n_br_icmsst_base'] = False
                    values_to_update['l10n_br_icmsst_aliquota'] = False
                    values_to_update['l10n_br_icmsst_valor'] = False
                    values_to_update['l10n_br_icmsst_retido_base'] = False
                    values_to_update['l10n_br_icmsst_retido_aliquota'] = False
                    values_to_update['l10n_br_icmsst_substituto_valor'] = False
                    values_to_update['l10n_br_icmsst_retido_valor'] = False

                    if self.l10n_br_icms_cst == '10':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor

                    elif self.l10n_br_icms_cst == '30':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor
                
                    elif self.l10n_br_icms_cst == '60':
                        values_to_update['l10n_br_icmsst_retido_base'] = ''
                        values_to_update['l10n_br_icmsst_retido_valor'] = ''

                    elif self.l10n_br_icms_cst == '70':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor

                    elif self.l10n_br_icms_cst == '90':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor

                    elif self.l10n_br_icms_cst == '201':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor
                
                    elif self.l10n_br_icms_cst == '202':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor

                    elif self.l10n_br_icms_cst == '500':
                        values_to_update['l10n_br_icmsst_retido_base'] = ''
                        values_to_update['l10n_br_icmsst_retido_valor'] = ''

                    elif self.l10n_br_icms_cst == '900':
                        values_to_update['l10n_br_icmsst_modalidade_base'] = l10n_br_icmsst_modalidade_base
                        values_to_update['l10n_br_icmsst_mva'] = l10n_br_icmsst_mva
                        values_to_update['l10n_br_icmsst_reducao_base'] = l10n_br_icmsst_reducao_base
                        values_to_update['l10n_br_icmsst_base'] = l10n_br_icmsst_base
                        values_to_update['l10n_br_icmsst_aliquota'] = l10n_br_icmsst_aliquota
                        values_to_update['l10n_br_icmsst_valor'] = l10n_br_icmsst_valor

                    self.update(values_to_update)

                    #########################
                    ##### ICMS PARTILHA #####
                    #########################
                    values_to_update = {}

                    values_to_update['l10n_br_icmsst_base_propria_aliquota'] = False
                    values_to_update['l10n_br_icmsst_uf'] = False
                    values_to_update['l10n_br_icms_dest_base'] = False
                    values_to_update['l10n_br_icms_dest_aliquota'] = False
                    values_to_update['l10n_br_icms_inter_aliquota'] = False
                    values_to_update['l10n_br_icms_inter_participacao'] = False
                    values_to_update['l10n_br_icms_dest_valor'] = False
                    values_to_update['l10n_br_icms_remet_valor'] = False

                    if self.l10n_br_icms_cst in ['00','10','20','51','70','90']:
                        if self.l10n_br_cfop_id.l10n_br_destino_operacao == '2' and \
                        self.move_id.l10n_br_operacao_consumidor == '1' and \
                        self.move_id.partner_id.l10n_br_indicador_ie == '9':

                            l10n_br_icms_dest_aliquota = 0.00
                            icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self.move_id.partner_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id)],limit=1)
                            if icms_uf:
                                l10n_br_icms_dest_aliquota = icms_uf.l10n_br_icms_aliquota

                            values_to_update['l10n_br_icmsst_base_propria_aliquota'] = ''
                            values_to_update['l10n_br_icmsst_uf'] = ''

                            values_to_update['l10n_br_icms_dest_base'] = self.l10n_br_icms_base
                            values_to_update['l10n_br_icms_dest_aliquota'] = l10n_br_icms_dest_aliquota
                            values_to_update['l10n_br_icms_dest_valor'] = (self.l10n_br_icms_base * l10n_br_icms_dest_aliquota / 100.00) - self.l10n_br_icms_valor
                            values_to_update['l10n_br_icms_remet_valor'] = 0.00
                            values_to_update['l10n_br_icms_inter_aliquota'] = self.l10n_br_icms_aliquota
                            values_to_update['l10n_br_icms_inter_participacao'] = 100.00

                    self.update(values_to_update)

                    ###################
                    ####### FCP #######
                    ###################
                    values_to_update = {}

                    values_to_update['l10n_br_fcp_base'] = False
                    values_to_update['l10n_br_fcp_dest_aliquota'] = False
                    values_to_update['l10n_br_fcp_dest_valor'] = False
                    values_to_update['l10n_br_fcp_st_base'] = False
                    values_to_update['l10n_br_fcp_st_aliquota'] = False
                    values_to_update['l10n_br_fcp_st_valor'] = False
                    values_to_update['l10n_br_fcp_st_ant_base'] = False
                    values_to_update['l10n_br_fcp_st_ant_aliquota'] = False
                    values_to_update['l10n_br_fcp_st_ant_valor'] = False

                    l10n_br_fcp_aliquota = self.move_id.partner_id.state_id.l10n_br_fcp_aliquota
                    ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
                    ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self.move_id.company_id.state_id.id),('state_para_id','=',self.move_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.move_id.partner_id.id)],limit=1)
                    if ncm_cliente_uf:
                        ncm_uf = ncm_cliente_uf

                    if ncm_uf and ncm_uf.l10n_br_fcp_aliquota > 0.00:
                        l10n_br_fcp_aliquota = ncm_uf.l10n_br_fcp_aliquota

                    # Simples Nacional ou Simples Nacional, excesso sublimite de receita bruta
                    values_to_update['l10n_br_fcp_base'] = 0.0
                    values_to_update['l10n_br_fcp_dest_aliquota'] = 0.0
                    values_to_update['l10n_br_fcp_dest_valor'] = 0.0

                    if self.l10n_br_icms_cst in ['201','202','900'] and self.l10n_br_icmsst_base > 0.00:
                        values_to_update['l10n_br_fcp_st_base'] = self.l10n_br_icmsst_base
                        values_to_update['l10n_br_fcp_st_aliquota'] = l10n_br_fcp_aliquota
                        values_to_update['l10n_br_fcp_st_valor'] = round(self.l10n_br_icmsst_base * l10n_br_fcp_aliquota / 100.00, 2)

                    values_to_update['l10n_br_fcp_st_ant_base'] = 0.0
                    values_to_update['l10n_br_fcp_st_ant_aliquota'] = 0.0
                    values_to_update['l10n_br_fcp_st_ant_valor'] = 0.0

                    # Regime Normal
                    if self.move_id.company_id.l10n_br_regime_tributario == '3':

                        bIncideFCP = False
                        # operação interna
                        if self.l10n_br_cfop_id.l10n_br_destino_operacao == '1':
                            # operação é consumidor final e estado incide para consumidor final
                            if self.move_id.company_id.l10n_br_fcp_interno_consumidor_final and \
                            self.move_id.l10n_br_operacao_consumidor == '1' and \
                            self.move_id.partner_id.l10n_br_indicador_ie == '9':
                                if self.l10n_br_icms_cst in ['00','10','20','51','70','90']:
                                    bIncideFCP = True

                        # operação interestadual
                        if self.l10n_br_cfop_id.l10n_br_destino_operacao == '2' and \
                            self.move_id.l10n_br_operacao_consumidor == '1' and \
                            self.move_id.partner_id.l10n_br_indicador_ie == '9':
                            bIncideFCP = True   

                        if bIncideFCP:
                            
                            if l10n_br_fcp_aliquota > 0.00:
                                l10n_br_fcp_dest_valor = round(self.l10n_br_icms_base * l10n_br_fcp_aliquota / 100.00, 2)
                                values_to_update['l10n_br_fcp_base'] = self.l10n_br_icms_base
                                values_to_update['l10n_br_fcp_dest_aliquota'] = l10n_br_fcp_aliquota
                                values_to_update['l10n_br_fcp_dest_valor'] = l10n_br_fcp_dest_valor

                                if self.l10n_br_icms_cst in ['10','30','70','90'] and self.l10n_br_icmsst_base > 0.00:
                                    values_to_update['l10n_br_fcp_st_base'] = self.l10n_br_icmsst_base
                                    values_to_update['l10n_br_fcp_st_aliquota'] = l10n_br_fcp_aliquota
                                    values_to_update['l10n_br_fcp_st_valor'] = round(self.l10n_br_icmsst_base * l10n_br_fcp_aliquota / 100.00, 2) - l10n_br_fcp_dest_valor

                        values_to_update['l10n_br_fcp_st_ant_base'] = False
                        values_to_update['l10n_br_fcp_st_ant_aliquota'] = False
                        values_to_update['l10n_br_fcp_st_ant_valor'] = False

                    self.update(values_to_update)

                    ###############
                    ##### PIS #####
                    ###############
                    values_to_update = {}

                    # Simples Nacional ou Simples Nacional, excesso sublimite de receita bruta
                    values_to_update['l10n_br_pis_cst'] = '99'
                    values_to_update['l10n_br_pis_base'] = 0.00
                    values_to_update['l10n_br_pis_aliquota'] = 0.00
                    values_to_update['l10n_br_pis_valor'] = 0.00
                    values_to_update['l10n_br_pis_valor_isento'] = 0.00
                    values_to_update['l10n_br_pis_valor_outros'] = 0.00

                    # Regime Normal
                    if self.move_id.company_id.l10n_br_regime_tributario == '3':
                        values_to_update['l10n_br_pis_cst'] = '01'

                    if self.product_id.l10n_br_ncm_id.l10n_br_pis_cst:
                        values_to_update['l10n_br_pis_cst'] = self.product_id.l10n_br_ncm_id.l10n_br_pis_cst
                    if self.l10n_br_cfop_id.l10n_br_pis_cst:
                        values_to_update['l10n_br_pis_cst'] = self.l10n_br_cfop_id.l10n_br_pis_cst
                    if self.l10n_br_operacao_id.l10n_br_pis_cst:
                        values_to_update['l10n_br_pis_cst'] = self.l10n_br_operacao_id.l10n_br_pis_cst

                    values_to_update['l10n_br_pis_base'] = 0.00
                    if values_to_update['l10n_br_pis_cst'] in ['01','02']:

                        l10n_br_pis_reducao_base = 0.00
                        if self.product_id.l10n_br_ncm_id.l10n_br_pis_reducao_base > 0.00:
                            l10n_br_pis_reducao_base = self.product_id.l10n_br_ncm_id.l10n_br_pis_reducao_base
                        if self.l10n_br_operacao_id.l10n_br_pis_reducao_base > 0.00:
                            l10n_br_pis_reducao_base = self.l10n_br_operacao_id.l10n_br_pis_reducao_base
                        values_to_update['l10n_br_pis_base'] = (self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor)
                        if self.move_id.company_id.l10n_br_exclui_icms_piscofins:
                            values_to_update['l10n_br_pis_base'] -= self.l10n_br_icms_valor
                        values_to_update['l10n_br_pis_base'] = values_to_update['l10n_br_pis_base'] * (1.00 - (l10n_br_pis_reducao_base/100.00))

                    values_to_update['l10n_br_pis_aliquota'] = 0.00
                    if values_to_update['l10n_br_pis_cst'] == '01':
                        # Lucro Presumido
                        if self.move_id.company_id.l10n_br_incidencia_cumulativa == '2':
                            values_to_update['l10n_br_pis_aliquota'] = 0.65
                        # Lucro Real
                        else:
                            values_to_update['l10n_br_pis_aliquota'] = 1.65

                    elif values_to_update['l10n_br_pis_cst'] in ['02','03']:
                        if self.product_id.l10n_br_ncm_id.l10n_br_pis_cst:
                            values_to_update['l10n_br_pis_aliquota'] = self.product_id.l10n_br_ncm_id.l10n_br_pis_aliquota
                        if self.l10n_br_operacao_id.l10n_br_pis_cst:
                            values_to_update['l10n_br_pis_aliquota'] = self.l10n_br_operacao_id.l10n_br_pis_aliquota

                    elif values_to_update['l10n_br_pis_cst'] == '49':
                        values_to_update['l10n_br_pis_aliquota'] = self.l10n_br_operacao_id.l10n_br_pis_aliquota

                    values_to_update['l10n_br_pis_valor'] = round(values_to_update['l10n_br_pis_base'] * values_to_update['l10n_br_pis_aliquota'] / 100.00, 2)
                    values_to_update['l10n_br_pis_valor_isento'] = 0.00
                    values_to_update['l10n_br_pis_valor_outros'] = 0.00
                    
                    self.update(values_to_update)

                    ##################
                    ##### COFINS #####
                    ##################
                    values_to_update = {}

                    # Simples Nacional ou Simples Nacional, excesso sublimite de receita bruta
                    values_to_update['l10n_br_cofins_cst'] = '99'
                    values_to_update['l10n_br_cofins_base'] = 0.00
                    values_to_update['l10n_br_cofins_aliquota'] = 0.00
                    values_to_update['l10n_br_cofins_valor'] = 0.00
                    values_to_update['l10n_br_cofins_valor_isento'] = 0.00
                    values_to_update['l10n_br_cofins_valor_outros'] = 0.00

                    # Regime Normal
                    if self.move_id.company_id.l10n_br_regime_tributario == '3':
                        values_to_update['l10n_br_cofins_cst'] = '01'

                    if self.product_id.l10n_br_ncm_id.l10n_br_cofins_cst:
                        values_to_update['l10n_br_cofins_cst'] = self.product_id.l10n_br_ncm_id.l10n_br_cofins_cst
                    if self.l10n_br_cfop_id.l10n_br_cofins_cst:
                        values_to_update['l10n_br_cofins_cst'] = self.l10n_br_cfop_id.l10n_br_cofins_cst
                    if self.l10n_br_operacao_id.l10n_br_cofins_cst:
                        values_to_update['l10n_br_cofins_cst'] = self.l10n_br_operacao_id.l10n_br_cofins_cst

                    values_to_update['l10n_br_cofins_base'] = 0.00
                    if values_to_update['l10n_br_cofins_cst'] in ['01','02']:

                        l10n_br_cofins_reducao_base = 0.00
                        if self.product_id.l10n_br_ncm_id.l10n_br_cofins_reducao_base > 0.00:
                            l10n_br_cofins_reducao_base = self.product_id.l10n_br_ncm_id.l10n_br_cofins_reducao_base
                        if self.l10n_br_operacao_id.l10n_br_cofins_reducao_base > 0.00:
                            l10n_br_cofins_reducao_base = self.l10n_br_operacao_id.l10n_br_cofins_reducao_base
                        values_to_update['l10n_br_cofins_base'] = (self.l10n_br_total_nfe - self.l10n_br_icmsst_valor - self.l10n_br_ipi_valor)
                        if self.move_id.company_id.l10n_br_exclui_icms_piscofins:
                            values_to_update['l10n_br_cofins_base'] -= self.l10n_br_icms_valor
                        values_to_update['l10n_br_cofins_base'] = values_to_update['l10n_br_cofins_base'] * (1.00 - (l10n_br_cofins_reducao_base/100.00))

                    values_to_update['l10n_br_cofins_aliquota'] = 0.00
                    if values_to_update['l10n_br_cofins_cst'] == '01':
                        # Lucro Presumido
                        if self.move_id.company_id.l10n_br_incidencia_cumulativa == '2':
                            values_to_update['l10n_br_cofins_aliquota'] = 3.00
                        # Lucro Real
                        else:
                            values_to_update['l10n_br_cofins_aliquota'] = 7.60

                    elif values_to_update['l10n_br_cofins_cst'] in ['02','03']:
                        if self.product_id.l10n_br_ncm_id.l10n_br_cofins_cst:
                            values_to_update['l10n_br_cofins_aliquota'] = self.product_id.l10n_br_ncm_id.l10n_br_cofins_aliquota
                        if self.l10n_br_operacao_id.l10n_br_cofins_cst:
                            values_to_update['l10n_br_cofins_aliquota'] = self.l10n_br_operacao_id.l10n_br_cofins_aliquota

                    elif values_to_update['l10n_br_cofins_cst'] == '49':
                        values_to_update['l10n_br_cofins_aliquota'] = self.l10n_br_operacao_id.l10n_br_cofins_aliquota

                    values_to_update['l10n_br_cofins_valor'] = round(values_to_update['l10n_br_cofins_base'] * values_to_update['l10n_br_cofins_aliquota'] / 100.00, 2)
                    values_to_update['l10n_br_cofins_valor_isento'] = 0.00
                    values_to_update['l10n_br_cofins_valor_outros'] = 0.00
                    
                    self.update(values_to_update)

                    ###############
                    ##### ISS #####
                    ###############
                    values_to_update = {}

                    if self.l10n_br_operacao_id.l10n_br_iss_aliquota > 0.00:
                        values_to_update['l10n_br_iss_base'] = self.l10n_br_total_nfe
                        values_to_update['l10n_br_iss_aliquota'] = self.l10n_br_operacao_id.l10n_br_iss_aliquota
                        values_to_update['l10n_br_iss_valor'] = round(values_to_update['l10n_br_iss_base'] * values_to_update['l10n_br_iss_aliquota'] / 100.00, 2)

                    self.update(values_to_update)

                    ################
                    ##### IRPJ #####
                    ################
                    values_to_update = {}

                    if self.l10n_br_operacao_id.l10n_br_irpj_aliquota > 0.00:
                        values_to_update['l10n_br_irpj_base'] = self.l10n_br_total_nfe
                        values_to_update['l10n_br_irpj_aliquota'] = self.l10n_br_operacao_id.l10n_br_irpj_aliquota
                        values_to_update['l10n_br_irpj_aliquota'] = round(values_to_update['l10n_br_irpj_base'] * values_to_update['l10n_br_irpj_aliquota'] / 100.00, 2)

                    self.update(values_to_update)

                    ################
                    ##### CSLL #####
                    ################
                    values_to_update = {}

                    if self.l10n_br_operacao_id.l10n_br_csll_aliquota > 0.00:
                        values_to_update['l10n_br_csll_base'] = self.l10n_br_total_nfe
                        values_to_update['l10n_br_csll_aliquota'] = self.l10n_br_operacao_id.l10n_br_csll_aliquota
                        values_to_update['l10n_br_csll_aliquota'] = round(values_to_update['l10n_br_csll_base'] * values_to_update['l10n_br_csll_aliquota'] / 100.00, 2)

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

                    ###################
                    ##### ISS RET #####
                    ###################
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

    @api.depends('l10n_br_icms_valor','l10n_br_icmsst_valor','l10n_br_icmsst_valor_outros','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias','l10n_br_ipi_valor','l10n_br_ipi_valor_isento','l10n_br_ipi_valor_outros','price_unit','discount','quantity','l10n_br_pis_valor','l10n_br_cofins_valor',
                 'l10n_br_icmsst_substituto_valor', 'l10n_br_icmsst_substituto_valor_outros', 'l10n_br_icmsst_retido_valor', 'l10n_br_icmsst_retido_valor_outros',
                 'l10n_br_ii_valor','l10n_br_ii_valor_aduaneira','l10n_br_iss_valor','l10n_br_irpj_valor','l10n_br_csll_valor','l10n_br_csll_ret_valor','l10n_br_irpj_ret_valor','l10n_br_inss_ret_valor','l10n_br_iss_ret_valor','l10n_br_pis_ret_valor','l10n_br_cofins_ret_valor')
    def _l10n_br_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for line in self:

            price_unit_discount = line.price_unit - line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            l10n_br_desc_valor = round(price_unit_discount * line.quantity,2)

            l10n_br_prod_valor = round(line.price_unit * line.quantity,2)

            l10n_br_total_nfe = l10n_br_prod_valor - l10n_br_desc_valor + line.l10n_br_icmsst_valor + line.l10n_br_icmsst_valor_outros + line.l10n_br_frete + line.l10n_br_seguro + line.l10n_br_despesas_acessorias + line.l10n_br_ipi_valor + line.l10n_br_ipi_valor_isento + line.l10n_br_ipi_valor_outros + line.l10n_br_ii_valor + line.l10n_br_ii_valor_aduaneira
            if line.move_id.l10n_br_tipo_pedido_entrada == 'importacao':
                l10n_br_total_nfe += line.l10n_br_pis_valor + line.l10n_br_cofins_valor
                # Lucro Presumido remove ICMS do Total da NF
                if line.move_id.company_id.l10n_br_incidencia_cumulativa == '2' and line.move_id.company_id.l10n_br_regime_tributario == '3':
                    l10n_br_total_nfe -= line.l10n_br_icms_valor
            l10n_br_total_tributos = line.l10n_br_icms_valor + line.l10n_br_icmsst_valor + line.l10n_br_ipi_valor + line.l10n_br_pis_valor + line.l10n_br_cofins_valor + line.l10n_br_ii_valor + line.l10n_br_ii_valor_aduaneira + line.l10n_br_iss_valor + line.l10n_br_irpj_valor + line.l10n_br_csll_valor

            line.update({
                'l10n_br_desc_valor': l10n_br_desc_valor,
                'l10n_br_prod_valor': l10n_br_prod_valor,
                'l10n_br_total_nfe': l10n_br_total_nfe,
                'l10n_br_total_tributos': l10n_br_total_tributos,
            })

    @api.onchange('l10n_br_icms_valor','l10n_br_icmsst_valor','l10n_br_icmsst_valor_outros','l10n_br_ipi_valor','l10n_br_ipi_valor_outros','l10n_br_pis_valor','l10n_br_cofins_valor','l10n_br_ii_valor','l10n_br_ii_valor_aduaneira','l10n_br_frete','l10n_br_seguro',
                  'l10n_br_icmsst_substituto_valor', 'l10n_br_icmsst_substituto_valor_outros', 'l10n_br_icmsst_retido_valor', 'l10n_br_icmsst_retido_valor_outros',
                  'l10n_br_despesas_acessorias','l10n_br_iss_valor','l10n_br_irpj_valor','l10n_br_csll_valor','l10n_br_csll_ret_valor','l10n_br_irpj_ret_valor','l10n_br_inss_ret_valor','l10n_br_iss_ret_valor','l10n_br_pis_ret_valor','l10n_br_cofins_ret_valor')
    def _onchange_l10n_br_mark_recompute_taxes(self):
        ''' Recompute the dynamic onchange based on taxes.
        If the edited line is a tax line, don't recompute anything as the user must be able to
        set a custom value.
        '''
        for line in self:
            if not line.tax_repartition_line_id:
                line.recompute_tax_line = True

class L10nBrAccountMoveCancel(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.account.move.cancel'
    _description = 'Cancelamento Documento Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_motivo = fields.Text(string="Motivo", required=True)

    def do_cancelar_nfe(self):
        invoice = self.env["account.move"].browse(self._context.get("active_id"))
        invoice.update({'l10n_br_motivo': self.l10n_br_motivo})
        self.env.cr.commit()
        invoice.action_cancelar_nfe()
        return {'type': 'ir.actions.act_window_close'}

class L10nBrAccountMoveCCE(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.account.move.cce'
    _description = 'Carta de Correção'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_correcao = fields.Text(string="Correção", required=True)

    def do_cce_nfe(self):
        invoice = self.env["account.move"].browse(self._context.get("active_id"))
        invoice.update({'l10n_br_correcao': self.l10n_br_correcao})
        self.env.cr.commit()
        invoice.action_gerar_cce_nfe()
        return {'type': 'ir.actions.act_window_close'}

class AccountMoveReference(models.Model):
    _name = "l10n_br_ciel_it_account.account.move.referencia"
    _description = "NF-e referência"
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    move_id = fields.Many2one('account.move', string='Journal Entry', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade", help="The move of this entry line.", check_company=True)
    l10n_br_chave_nf = fields.Char( string='Chave NF-e', required=True )

class L10nBrMdfeCancel(models.TransientModel):
    _name = 'l10n_br_ciel_it_account.mdfe.cancel'
    _description = 'Cancelamento MDF-e'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_motivo = fields.Text(string="Motivo", required=True)

    def do_cancelar_mdfe(self):
        invoice = self.env["l10n_br_ciel_it_account.mdfe"].browse(self._context.get("active_id"))
        invoice.update({'l10n_br_motivo': self.l10n_br_motivo})
        self.env.cr.commit()
        invoice.action_cancelar_mdfe()
        return {'type': 'ir.actions.act_window_close'}

class L10nBrMdfe(models.Model):
    _name = 'l10n_br_ciel_it_account.mdfe'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'MDF-e'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Número',required=True, readonly=True, copy=False, default='/')
    l10n_br_status = fields.Selection( MDFE_STATUS, string='Situação', default='01', copy=False )
    l10n_br_tipo_documento_id = fields.Many2one('l10n_br_ciel_it_account.tipo.documento.mdfe', string='Tipo de Documento', required=True, check_company=True)

    l10n_br_date_emissao = fields.Datetime( string='Data de Emissão', default=lambda self: fields.datetime.now() )
    l10n_br_date_inicio = fields.Datetime( string='Data de Início da Viagem', default=lambda self: fields.datetime.now() )
    l10n_br_numero_mdfe = fields.Integer( string='Número do MDF-e', copy=False )
    l10n_br_serie_mdfe = fields.Char( string='Série do MDF-e', copy=False )
    l10n_br_chave_mdfe = fields.Char( string='Chave do MDF-e', copy=False )
    l10n_br_cstat_mdfe = fields.Char( string='Status do MDF-e', copy=False, readonly=True )
    l10n_br_xmotivo_mdfe = fields.Char( string='Situação do MDF-e', copy=False, readonly=True )
    l10n_br_motivo = fields.Text( string='Motivo Cancelamento', copy=False, readonly=True )

    l10n_br_municipio_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município de Carregamento', required=True, default=lambda self: self.env.company.l10n_br_municipio_id)
    l10n_br_uf_final = fields.Char( string='UF do Descarregamento', required=True )
    l10n_br_ufs_percurso = fields.Char( string="UF's do Percurso", help="Informar as UF's separado por virgula" )

    move_ids = fields.Many2many( 'account.move', 'mdfe_account_move_rel', domain=[('state', '=', 'posted'),('l10n_br_chave_nf', '!=', False)], string='Faturas', required=True, check_company=True)

    l10n_br_veiculo_tracao_id = fields.Many2one('l10n_br_ciel_it_account.veiculo', string='Veículo Tração', required=True)
    l10n_br_motorista_ids = fields.Many2many('l10n_br_ciel_it_account.motorista', 'mfe_motorista_rel', string='Motoristas', required=True)
    l10n_br_veiculo_reboque_ids = fields.Many2many('l10n_br_ciel_it_account.veiculo', 'mfe_reboque_rel', string='Reboques')

    l10n_br_xml_aut_mdfe = fields.Binary( string="XML MDF-e", copy=False )
    l10n_br_xml_aut_mdfe_fname = fields.Char( string="Arquivo XML MDF-e", compute="_get_l10n_br_xml_aut_mdfe_fname" )
    l10n_br_pdf_aut_mdfe = fields.Binary( string="DAMDFE MDF-e", copy=False )
    l10n_br_pdf_aut_mdfe_fname = fields.Char( string="Arquivo DAMDFE MDF-e", compute="_get_l10n_br_pdf_aut_mdfe_fname" )

    def _gerar_mdfe_tx2(self):
        
        self.ensure_one()

        def _format_nMdfe(valor):
            return str(valor).zfill(8)

        def _format_nDup(valor):
            return str(valor).zfill(3)

        def _format_decimal_2(valor):
            return "{:.2f}".format(valor)

        def _format_decimal_3(valor):
            return "{:.3f}".format(valor)

        def _format_decimal_4(valor):
            return "{:.4f}".format(valor)

        def _format_decimal_10(valor):
            return "{:.10f}".format(valor)

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_datetime_timezone(date):
            return datetime.strftime(date,'%Y-%m-%d')+'T'+datetime.strftime(date,'%H:%M:%S')+datetime.strftime(date,'%z')[0:3]+':00'

        def _format_cep(texto):
            return str(texto).replace("-","").replace(".","")
    
        def _format_name(texto):
            return str(texto)

        mdfe = self

        mdfe_vals = {}
        mdfe_vals['Versao_2'] = mdfe.l10n_br_tipo_documento_id.l10n_br_versao
        mdfe_vals['cUF_5'] = mdfe.company_id.state_id.l10n_br_codigo_ibge
        mdfe_vals['tpAmb_6'] = mdfe.l10n_br_tipo_documento_id.l10n_br_ambiente
        mdfe_vals['tpEmit_7'] = mdfe.l10n_br_tipo_documento_id.l10n_br_emitente
        mdfe_vals['mod_8'] = mdfe.l10n_br_tipo_documento_id.l10n_br_modelo
        mdfe_vals['serie_9'] = mdfe.l10n_br_serie_mdfe
        mdfe_vals['nMDF_10'] = mdfe.l10n_br_numero_mdfe
        mdfe_vals['cMDF_11'] = _format_nMdfe(mdfe.id)
        mdfe_vals['modal_13'] = mdfe.l10n_br_tipo_documento_id.l10n_br_modal

        invoice_date_br = datetime.now(pytz.timezone('America/Sao_Paulo'))
        mdfe_vals['dhEmi_14'] = _format_datetime_timezone(invoice_date_br)
        mdfe_vals['tpEmis_15'] = mdfe.l10n_br_tipo_documento_id.l10n_br_tipo_emissao
        mdfe_vals['procEmi_16'] = '0'
        mdfe_vals['verProc_17'] = 'Odoo 13.0e'
        mdfe_vals['UFIni_18'] = mdfe.l10n_br_municipio_id.state_id.code
        mdfe_vals['UFFim_19'] = mdfe.l10n_br_uf_final
        mdfe_vals['dhIniViagem_25'] = _format_datetime_timezone(invoice_date_br)
        mdfe_vals['CNPJ_26'] = _format_cnpj_cpf(mdfe.company_id.l10n_br_cnpj)
        mdfe_vals['IE_27'] = mdfe.company_id.l10n_br_ie
        mdfe_vals['xNome_28'] = mdfe.company_id.l10n_br_razao_social or mdfe.company_id.name
        mdfe_vals['xFant_29'] = mdfe.company_id.name
        mdfe_vals['xLgr_31'] = mdfe.company_id.street
        mdfe_vals['nro_32'] = mdfe.company_id.l10n_br_endereco_numero
        mdfe_vals['xCpl_33'] = mdfe.company_id.street2 or ""
        mdfe_vals['xBairro_34'] = mdfe.company_id.l10n_br_endereco_bairro
        mdfe_vals['cMun_35'] = mdfe.company_id.l10n_br_municipio_id.codigo_ibge
        mdfe_vals['xMun_36'] = mdfe.company_id.l10n_br_municipio_id.name
        mdfe_vals['CEP_37'] = _format_cep(mdfe.company_id.zip)
        mdfe_vals['UF_38'] = mdfe.company_id.state_id.code
        mdfe_vals['fone_39'] = _format_fone(mdfe.company_id.phone or "")
        mdfe_vals['email_40'] = mdfe.company_id.email or ""
        mdfe_vals['versaoModal_42'] = mdfe.l10n_br_tipo_documento_id.l10n_br_versao
        mdfe_vals['qNFe_71'] = len(mdfe.move_ids)
        mdfe_vals['vCarga_73'] = _format_decimal_2(sum([nfe.l10n_br_total_nfe for nfe in mdfe.move_ids]))
        mdfe_vals['cUnid_74'] = '01'
        mdfe_vals['qCarga_75'] = _format_decimal_4(sum([nfe.l10n_br_peso_bruto for nfe in mdfe.move_ids]))

        mdfeMunCarrega_vals = {}
        mdfeMunCarrega_vals['cMunCarrega_21'] = mdfe.l10n_br_municipio_id.codigo_ibge
        mdfeMunCarrega_vals['xMunCarrega_22'] = _format_name(mdfe.l10n_br_municipio_id.name)
        
        mdfeMunDescarga_lines = []
        for invoice in mdfe.move_ids:
            mdfeMunDescarga_vals = {}
            #_logger.info(['invoice_type', invoice.type, TIPO_NF[invoice.type]])
            if TIPO_NF[invoice.type] == 1:
                mdfeMunDescarga_vals['cMunDescarga_46'] = invoice.partner_shipping_id.l10n_br_municipio_id.codigo_ibge or invoice.partner_id.l10n_br_municipio_id.codigo_ibge
                mdfeMunDescarga_vals['xMunDescarga_47'] = _format_name(invoice.partner_shipping_id.l10n_br_municipio_id.name or invoice.partner_id.l10n_br_municipio_id.name)
            else:
                mdfeMunDescarga_vals['cMunDescarga_46'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge
                mdfeMunDescarga_vals['xMunDescarga_47'] = _format_name(invoice.company_id.l10n_br_municipio_id.name)

            mdfeMunDescarga_lines.append(mdfeMunDescarga_vals)

        mdfeMunDescarga_lines = [dict(t) for t in {tuple(d.items()) for d in mdfeMunDescarga_lines}]

        mdfeNFe_lines = []
        for invoice in mdfe.move_ids:
            mdfeNFe_vals = {}

            #_logger.info(['invoice_type', invoice.type, TIPO_NF[invoice.type]])
            if TIPO_NF[invoice.type] == 1:
                mdfeNFe_vals['cMunDescarga_46'] = invoice.partner_shipping_id.l10n_br_municipio_id.codigo_ibge or invoice.partner_id.l10n_br_municipio_id.codigo_ibge
            else:
                mdfeNFe_vals['cMunDescarga_46'] = invoice.company_id.l10n_br_municipio_id.codigo_ibge

            mdfeNFe_vals['chNFe_58'] = invoice.l10n_br_chave_nf
            mdfeNFe_lines.append(mdfeNFe_vals)

        mdfeUF_percurso = []
        if mdfe.l10n_br_ufs_percurso:
            for ufs in mdfe.l10n_br_ufs_percurso.split(","):
                for ufpercurso in ufs.split(";"):
                    mdfeUF_percurso.append({'UFPer_24': ufpercurso.strip()})
                
        mdfeRodo_vals = {}
        mdfeRodo_vals['RNTRC_rodo_2'] = '00000000'
        mdfeRodo_vals['cInt_rodo_5'] = mdfe.l10n_br_veiculo_tracao_id.id
        mdfeRodo_vals['placa_rodo_6'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_placa
        mdfeRodo_vals['tara_rodo_7'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_tara
        mdfeRodo_vals['capKG_rodo_8'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_capacidade_kg
        mdfeRodo_vals['capM3_rodo_9'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_capacidade_m3
        mdfeRodo_vals['tpRod_rodo_34'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_rodado
        mdfeRodo_vals['tpCar_rodo_35'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_carroceria
        mdfeRodo_vals['UF_rodo_36'] = mdfe.l10n_br_veiculo_tracao_id.l10n_br_uf

        mdfeCondutor_lines = []
        for motorista in mdfe.l10n_br_motorista_ids:
            mdfeCondutor_vals = {}
            mdfeCondutor_vals['xNome_rodo_13'] = motorista.name
            mdfeCondutor_vals['CPF_rodo_14'] = _format_cnpj_cpf(motorista.l10n_br_cpf)
            mdfeCondutor_lines.append(mdfeCondutor_vals)

        mdfeReboque_lines = []
        for reboque in mdfe.l10n_br_veiculo_reboque_ids:
            mdfeReboque_vals = {}
            mdfeReboque_vals['cInt_rodo_16'] = reboque.id
            mdfeReboque_vals['placa_rodo_17'] = reboque.l10n_br_placa
            mdfeReboque_vals['tara_rodo_18'] = reboque.l10n_br_tara
            mdfeReboque_vals['capKG_rodo_19'] = reboque.l10n_br_capacidade_kg
            mdfeReboque_vals['capM3_rodo_20'] = reboque.l10n_br_capacidade_m3
            mdfeReboque_vals['tpCar_rodo_43'] = reboque.l10n_br_carroceria
            mdfeReboque_vals['UF_rodo_44'] = reboque.l10n_br_uf
            mdfeReboque_lines.append(mdfeReboque_vals)

        nfetx2 = "incluirenviMDFe"
        for key, value in mdfe_vals.items():
            nfetx2 += "%0A" + key + "%3D" + str(value)

        nfetx2 += "%0AincluirinfMunCarrega"
        for key, value in mdfeMunCarrega_vals.items():
            nfetx2 += "%0A" + key + "%3D" + str(value)
        nfetx2 += "%0AsalvarinfMunCarrega"

        for mdfeUF_percurso_vals in mdfeUF_percurso:
            nfetx2 += "%0AincluirinfPercurso"
            for key, value in mdfeUF_percurso_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0AsalvarinfPercurso"

        for mdfeMunDescarga_vals in mdfeMunDescarga_lines:
            nfetx2 += "%0AincluirinfMunDescarga"
            for key, value in mdfeMunDescarga_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)

            for mdfeNFe_vals in [item for item in mdfeNFe_lines if item['cMunDescarga_46'] == mdfeMunDescarga_vals['cMunDescarga_46']]:
                nfetx2 += "%0AincluirinfNFe"
                for key, value in mdfeNFe_vals.items():
                    if key != 'cMunDescarga_46':
                        nfetx2 += "%0A" + key + "%3D" + str(value)
                nfetx2 += "%0AsalvarinfNFe"

            nfetx2 += "%0AsalvarinfMunDescarga"

        nfetx2 += "%0AsalvarenviMDFe"
        nfetx2 += "%0Aincluirrodo"

        for key, value in mdfeRodo_vals.items():
            nfetx2 += "%0A" + key + "%3D" + str(value)

        for mdfeCondutor_vals in mdfeCondutor_lines:
            nfetx2 += "%0Aincluircondutor"
            for key, value in mdfeCondutor_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0Asalvarcondutor"

        for mdfeReboque_vals in mdfeReboque_lines:
            nfetx2 += "%0AincluirveicReboque"
            for key, value in mdfeReboque_vals.items():
                nfetx2 += "%0A" + key + "%3D" + str(value)
            nfetx2 += "%0AsalvarveicReboque"

        nfetx2 += "%0Asalvarrodo"
        
        #_logger.info(['passo 6',nfetx2])
        
        return nfetx2

    def _get_l10n_br_xml_aut_mdfe_fname(self):

        for record in self:
            record.l10n_br_xml_aut_mdfe_fname = "%s-mdfe.xml" % (record.l10n_br_chave_mdfe or record.l10n_br_numero_mdfe)

    def _get_l10n_br_pdf_aut_mdfe_fname(self):

        for record in self:
            record.l10n_br_pdf_aut_mdfe_fname = "%s-mdfe.pdf" % (record.l10n_br_chave_mdfe or record.l10n_br_numero_mdfe)

    def _action_gerar_mdfe(self):
        """
        Transmite MDF-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        invoice = self
        
        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % ( 
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            "FORMATO%3Dtx2%0A",
        )
        nfetx2 += invoice._gerar_mdfe_tx2()

        url = "%s/ManagerAPIWeb/mdfe/envia" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Gerar MDFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

            try:
                invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))
            except:
                invoice.message_post(body=_format_message(response.text))


            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if not "EXCEPTION" in response.text and response_values[2] == '100':
                to_write = {}
                to_write['l10n_br_status'] = '02'
                to_write['l10n_br_chave_mdfe'] = response_values[1]
                to_write['l10n_br_cstat_mdfe'] = response_values[2]
                to_write['l10n_br_xmotivo_mdfe'] = response_values[3]
                invoice.update(to_write)
                self.env.cr.commit()
                invoice.action_gerar_xml_mdfe()
                invoice.action_gerar_danfe_mdfe()
            else:
                to_write = {}
                to_write['l10n_br_xmotivo_mdfe'] = response_values[len(response_values)-1]
                invoice.update(to_write)
                self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_resolver_mdfe(self):
        """
        Resolver MDF-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()
        invoice = self
        
        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s" % ( 
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_mdfe,
        )

        url = "%s/ManagerAPIWeb/mdfe/resolve" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Resolver MDFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

            invoice.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))

            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if not "EXCEPTION" in response.text and response_values[2] == '100':
                to_write = {}
                to_write['l10n_br_status'] = '02'
                to_write['l10n_br_chave_mdfe'] = response_values[1]
                to_write['l10n_br_cstat_mdfe'] = response_values[2]
                to_write['l10n_br_xmotivo_mdfe'] = response_values[3]
                invoice.update(to_write)
                self.env.cr.commit()
                invoice.action_gerar_xml_mdfe()
                invoice.action_gerar_danfe_mdfe()
            else:
                to_write = {}
                to_write['l10n_br_xmotivo_mdfe'] = response_values[len(response_values)-1]
                invoice.update(to_write)
                self.env.cr.commit()

        except Exception as e:
            invoice.message_post(body=_format_message(e))
            raise UserError(_format_message(e))


    def action_gerar_xmldanfe_mdfe(self):
        self.ensure_one()
        self.action_gerar_xml_mdfe()
        self.action_gerar_danfe_mdfe()

    def action_gerar_danfe_mdfe(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/mdfe/imprime?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&URL=0" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_mdfe,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)

        self.update({
            'l10n_br_pdf_aut_mdfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_xml_mdfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/mdfe/xml?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_mdfe,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)

        self.update({
            'l10n_br_xml_aut_mdfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_mdfe(self):

        for mdfe in self:
            if not mdfe.l10n_br_date_emissao:
                mdfe.l10n_br_date_emissao = fields.Date.context_today(self)

            if not mdfe.l10n_br_date_inicio:
                mdfe.l10n_br_date_inicio = fields.Date.context_today(self)

        for mdfe in self:
            to_write = {}

            if mdfe.name == '/':
                to_write['name'] = mdfe.l10n_br_tipo_documento_id.sequence_id.next_by_id(sequence_date=mdfe.l10n_br_date_emissao)

            if not mdfe.l10n_br_numero_mdfe:
                to_write['l10n_br_numero_mdfe'] = mdfe.l10n_br_tipo_documento_id.l10n_br_numero_mdfe_id.next_by_id()

            if not mdfe.l10n_br_serie_mdfe:
                to_write['l10n_br_serie_mdfe'] = mdfe.l10n_br_tipo_documento_id.l10n_br_serie_mdfe

            if to_write:
                mdfe.update(to_write)
                self.env.cr.commit()

            mdfe._action_gerar_mdfe()

    def action_cancelar_mdfe(self):
    
        for mdfe in self:
            mdfe._action_cancelar_mdfe()

    def _action_cancelar_mdfe(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/mdfe/cancela?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&Justificativa=%s" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_mdfe,
            self.l10n_br_motivo,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Cancelar MDF-e</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers)
            self.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))

            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if "Evento registrado e vinculado ao MDF-e" in response.text:
                to_write = {}
                to_write['l10n_br_status'] = '03'
                to_write['l10n_br_cstat_mdfe'] = response_values[1]
                to_write['l10n_br_xmotivo_mdfe'] = response_values[2]
                self.update(to_write)
                self.env.cr.commit()
                self.action_gerar_xml_mdfe()
            else:
                to_write = {}
                to_write['l10n_br_cstat_mdfe'] = ''
                to_write['l10n_br_xmotivo_mdfe'] = response_values[len(response_values)-1]
                self.update(to_write)
                self.env.cr.commit()

        except Exception as e:
            self.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

    def action_encerrar_mdfe(self):
        
        for mdfe in self:
            mdfe._action_encerrar_mdfe()

    def _action_encerrar_mdfe(self):
    
        def _format_date(date):
            return datetime.strftime(date,'%Y-%m-%d')

        def _format_datetime(date):
            return datetime.strftime(date,'%Y-%m-%d')+'T'+datetime.strftime(date,'%H:%M:%S')

        def _format_timezone(date):
            return datetime.strftime(date,'%z')[0:3]+':00'

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""


        self.ensure_one()

        url = "%s/ManagerAPIWeb/mdfe/encerra?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&DhEvento=%s&Fuso=%s&DataEncerramento=%s&CodUfEncerramento=%s&CodMunicipioEncerramento=%s" % (
            self.l10n_br_tipo_documento_id.l10n_br_url,
            self.l10n_br_tipo_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.company_id.l10n_br_cnpj),
            self.l10n_br_chave_mdfe,
            _format_datetime(datetime.now(pytz.timezone('America/Sao_Paulo'))),
            _format_timezone(datetime.now(pytz.timezone('America/Sao_Paulo'))),
            _format_date(datetime.now(pytz.timezone('America/Sao_Paulo'))),
            self.company_id.state_id.l10n_br_codigo_ibge,
            self.company_id.l10n_br_municipio_id.codigo_ibge,            
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            self.l10n_br_tipo_documento_id.l10n_br_usuario,
            self.l10n_br_tipo_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Encerrar MDF-e</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers)
            self.message_post(body=_format_message(response.content.decode('utf-8').replace('\delimiter',' ')))

            response_values = response.content.decode('utf-8').replace('\delimiter',' ').split(",")
            if "Evento registrado e vinculado ao MDF-e" in response.text:
                to_write = {}
                to_write['l10n_br_status'] = '04'
                to_write['l10n_br_cstat_mdfe'] = response_values[1]
                to_write['l10n_br_xmotivo_mdfe'] = response_values[2]
                self.update(to_write)
                self.env.cr.commit()
                self.action_gerar_xml_mdfe()
            else:
                to_write = {}
                to_write['l10n_br_cstat_mdfe'] = ''
                to_write['l10n_br_xmotivo_mdfe'] = response_values[len(response_values)-1]
                self.update(to_write)
                self.env.cr.commit()

        except Exception as e:
            self.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

class L10nBrTipoDocumentoMdfe(models.Model):
    _name = 'l10n_br_ciel_it_account.tipo.documento.mdfe'
    _description = 'Tipo de Documento MDF-e'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Nome',required=True)
    active = fields.Boolean(string='Ativo',default=True)
    sequence_id = fields.Many2one('ir.sequence', string='Sequencia')
    l10n_br_versao = fields.Selection( VERSAO_MDFE, string='Versão do Leiaute' )
    l10n_br_ambiente = fields.Selection( AMBIENTE_MDFE, string='Ambiente' )
    l10n_br_emitente = fields.Selection( EMITENTE_MDFE, string='Tipo Emitente' )
    l10n_br_modelo = fields.Char( string='Modelo do Documento Fiscal' )
    l10n_br_modal = fields.Selection( MODAL_MDFE, string='Modalidade de Transporte' )
    l10n_br_tipo_emissao = fields.Selection( TIPO_EMISSAO_MDFE, string='Forma de Emissão' )
    l10n_br_numero_mdfe_id = fields.Many2one('ir.sequence', string='Número do MDF-e' )
    l10n_br_serie_mdfe = fields.Char( string='Série do MDF-e' )

    l10n_br_grupo = fields.Char( string='Grupo' )
    l10n_br_url = fields.Char( string='URL' )
    l10n_br_usuario = fields.Char( string='Usuário' )
    l10n_br_senha = fields.Char( string='Senha' )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'O Nome deve ser unico !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrTipoDocumentoMdfe, self).copy(dict(default or {}))

class L10nBrMotorista(models.Model):
    _name = 'l10n_br_ciel_it_account.motorista'
    _description = 'Motorista'

    name = fields.Char(string='Nome',required=True)
    l10n_br_cpf = fields.Char(string='CPF',required=True)

class L10nBrVeiculo(models.Model):
    _name = 'l10n_br_ciel_it_account.veiculo'
    _description = 'Veículo'

    name = fields.Char(string='Nome',required=True)
    l10n_br_placa = fields.Char(string='Placa',required=True)
    l10n_br_uf = fields.Char( string='UF' )
    l10n_br_tara = fields.Integer(string='Tara (KG)')
    l10n_br_capacidade_kg = fields.Integer(string='Capacidade (KG)')
    l10n_br_capacidade_m3 = fields.Integer(string='Capacidade (M3)')
    l10n_br_rodado = fields.Selection( TIPO_RODADO, string='Tipo de Rodado' )
    l10n_br_carroceria = fields.Selection( TIPO_CARROCERIA, string='Tipo de Carroceria' )

class L10nBrTipoCobranca(models.Model):
    _name = 'l10n_br_ciel_it_account.tipo.cobranca'
    _description = 'Tipo de Cobrança'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Nome',required=True)
    journal_id = fields.Many2one('account.journal', string='Bank', domain=[('type', '=', 'bank')], check_company=True)
    l10n_br_cedente_banco = fields.Char( string='Código do Banco' )
    l10n_br_cedente_conta = fields.Char( string='Conta Corrente' )
    l10n_br_cedente_conta_digito = fields.Char( string='DV' )
    l10n_br_cedente_convenio = fields.Char( string='Convênio' )
    l10n_br_nosso_numero_id = fields.Many2one('ir.sequence', string='Nosso Número' )
    l10n_br_mensagem_pagamento = fields.Char( string='Mensagem Local Pagamento', default='Pagável em qualquer banco até o vencimento.' )
    l10n_br_mensagem_01 = fields.Char( string='Mensagem 01' )
    l10n_br_mensagem_02 = fields.Char( string='Mensagem 02' )
    l10n_br_mensagem_03 = fields.Char( string='Mensagem 03' )
    l10n_br_mensagem_04 = fields.Char( string='Mensagem 04' )
    l10n_br_mensagem_05 = fields.Char( string='Mensagem 05' )
    l10n_br_mensagem_06 = fields.Char( string='Mensagem 06' )
    l10n_br_mensagem_07 = fields.Char( string='Mensagem 07' )
    l10n_br_mensagem_08 = fields.Char( string='Mensagem 08' )
    l10n_br_mensagem_09 = fields.Char( string='Mensagem 09' )
    l10n_br_especie = fields.Selection( COBRANCA_ESPECIE, string='Espécie Documento' )
    l10n_br_transmissao = fields.Selection( TIPO_TRANSMISSAO, string='Tipo Transmissão', default='webservice' )
    l10n_br_codigo_multa = fields.Selection( COBRANCA_MULTA, string='Tipo de Multa' )
    l10n_br_percentual_multa = fields.Float( string='% de Multa' )
    l10n_br_codigo_juros = fields.Selection( COBRANCA_JUROS, string='Tipo de Juros' )
    l10n_br_percentual_juros = fields.Float( string='% de Juros' )
    l10n_br_codigo_baixa = fields.Selection( COBRANCA_BAIXA, string='Tipo de Baixa/Devolução' )
    l10n_br_dias_baixa = fields.Integer( string='Dias para Baixa/Devolução' )
    l10n_br_codigo_protesto = fields.Selection( COBRANCA_PROTESTO, string='Tipo Protesto' )
    l10n_br_dias_protesto = fields.Integer( string='Dias para Protesto' )
    l10n_br_url = fields.Char( string='URL' )
    l10n_br_token = fields.Char( string='Token' )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'O Nome deve ser unico !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrTipoCobranca, self).copy(dict(default or {}))

class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_SAIDA, string='Tipo de Pedido (saída)', states={'draft': [('readonly', False)]} )
    l10n_br_tipo_pedido_entrada = fields.Selection( TIPO_PEDIDO_ENTRADA, string='Tipo de Pedido (entrada)', states={'draft': [('readonly', False)]} )
    fiscal_position_id = fields.Many2one('account.fiscal.position', 'Fiscal Position', check_company=True)
    l10n_br_no_payment = fields.Boolean(string="No Payment")
    account_no_payment_id = fields.Many2one('account.account', string='Account', index=True, ondelete="cascade", check_company=True, domain=[('deprecated', '=', False)])
    writeoff_account_id = fields.Many2one('account.account', string='Conta Diferença Pagamento', index=True, ondelete="cascade", check_company=True, domain=[('deprecated', '=', False)])

class L10nBrDi(models.Model):
    _name = 'l10n_br_ciel_it_account.di'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _description = 'DI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', required=True)
    incoterm_id = fields.Many2one('account.incoterms', string='Incoterm', required=True)
    partner_id = fields.Many2one('res.partner', string='Fornecedor', required=True)
    purchase_ids = fields.Many2many('purchase.order', string='Pedido de Compra', copy=False)
    name = fields.Char(string='Número da DI', required=True)
    state = fields.Selection( DI_STATUS, string='Situação', default='01', copy=False )
    line_ids = fields.One2many('l10n_br_ciel_it_account.di.line', 'l10n_br_di_id', string='Linhas', copy=True, readonly=True, states={'01': [('readonly', False)]})
    adicao_ids = fields.One2many('l10n_br_ciel_it_account.di.adicao', 'l10n_br_di_id', string='Adições', copy=True, readonly=True, states={'01': [('readonly', False)]})
    moeda_ids = fields.One2many('l10n_br_ciel_it_account.di.moeda', 'l10n_br_di_id', string='Moedas', copy=True, readonly=True, states={'01': [('readonly', False)]})
    despesa_ids = fields.One2many('l10n_br_ciel_it_account.di.despesa', 'l10n_br_di_id', string='Despesas', copy=True, readonly=True, states={'01': [('readonly', False)]})
    l10n_br_data_di = fields.Date( string='Data da DI', required=True )
    l10n_br_local_desembaraco = fields.Char(string='Local de Desembaraço', required=True)
    l10n_br_uf_desembaraco = fields.Char( string='UF de Desembaraço', required=True )
    l10n_br_data_desembaraco = fields.Date( string='Data de Desembaraço', required=True )
    l10n_br_via_transporte = fields.Selection( VIA_TRANSPORTE_DI, string='Via de Transporte Internacional', required=True )
    l10n_br_tipo_importacao = fields.Selection( TIPO_IMPORTACAO, string='Tipo de Importação', required=True )

    def action_gerar_rateio(self):

        self.ensure_one()

        l10n_br_peso_total = sum(self.line_ids.mapped('l10n_br_peso_total'))

        for despesa in self.despesa_ids:
            moedas = [moeda for moeda in self.moeda_ids if moeda.currency_id == despesa.currency_id]
            l10n_br_taxa = moedas[0].l10n_br_taxa if moedas else 1.00
            despesa.write({
                'l10n_br_valor_brl': despesa.l10n_br_valor * l10n_br_taxa
            })

        l10n_br_despesa_cif_total_brl = sum([item.l10n_br_valor_brl for item in self.despesa_ids if item.l10n_br_tipo_despesa in ['frete','seguro']])
        l10n_br_despesa_adicional_total_brl = sum([item.l10n_br_valor_brl for item in self.despesa_ids if item.l10n_br_tipo_despesa == 'adicional'])
        l10n_br_despesa_aduaneira_total_brl = sum([item.l10n_br_valor_brl for item in self.despesa_ids if item.l10n_br_tipo_despesa == 'aduaneira'])

        for line in self.line_ids:
            moedas = [moeda for moeda in self.moeda_ids if moeda.currency_id == line.currency_id]
            l10n_br_taxa = moedas[0].l10n_br_taxa if moedas else 1.00

            l10n_br_valor_brl = line.l10n_br_valor * l10n_br_taxa
            l10n_br_valor_cif_brl = l10n_br_valor_brl + (l10n_br_despesa_cif_total_brl * ( line.l10n_br_peso_total / l10n_br_peso_total ) / line.l10n_br_quantidade)
            l10n_br_valor_adicional_brl = l10n_br_despesa_adicional_total_brl * ( line.l10n_br_peso_total / l10n_br_peso_total ) / line.l10n_br_quantidade
            l10n_br_valor_aduaneira_brl = l10n_br_despesa_aduaneira_total_brl * ( line.l10n_br_peso_total / l10n_br_peso_total ) / line.l10n_br_quantidade

            line.write({
                'l10n_br_valor_brl': l10n_br_valor_brl,
                'l10n_br_valor_cif_brl': l10n_br_valor_cif_brl,
                'l10n_br_valor_adicional_brl': l10n_br_valor_adicional_brl,
                'l10n_br_valor_aduaneira_brl': l10n_br_valor_aduaneira_brl,
            })

        self.write({'state': '02'})

    @api.onchange('purchase_ids')
    def onchange_purchase_ids(self):

        if not self.purchase_ids and self.state != '01':
            self.write({'state': '02'})

    def action_gerar_po(self):

        self.ensure_one()
        
        order_lines = []
        for item in self.line_ids:
            order_line = {}

            order_line['name'] = item.product_id.display_name
            order_line['product_id'] = item.product_id.id
            order_line['product_qty'] = item.l10n_br_quantidade
            order_line['product_uom'] = item.uom_id.id
            order_line['price_unit'] = item.l10n_br_valor_cif_brl + item.l10n_br_valor_adicional_brl
            order_line['date_planned'] = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            ## PIS ##
            order_line['l10n_br_pis_cst'] = item.l10n_br_di_adicao_id.l10n_br_pis_cst
            order_line['l10n_br_pis_base'] = round(item.l10n_br_total_cif_brl + item.l10n_br_total_adicional_brl, 2)
            order_line['l10n_br_pis_aliquota'] = item.l10n_br_di_adicao_id.l10n_br_pis_aliquota
            order_line['l10n_br_pis_valor'] = round(order_line['l10n_br_pis_base'] * order_line['l10n_br_pis_aliquota'] / 100.00, 2)

            ## COFINS ##
            order_line['l10n_br_cofins_cst'] = item.l10n_br_di_adicao_id.l10n_br_cofins_cst
            order_line['l10n_br_cofins_base'] = round(item.l10n_br_total_cif_brl + item.l10n_br_total_adicional_brl, 2)
            order_line['l10n_br_cofins_aliquota'] = item.l10n_br_di_adicao_id.l10n_br_cofins_aliquota
            order_line['l10n_br_cofins_valor'] = round(order_line['l10n_br_cofins_base'] * order_line['l10n_br_cofins_aliquota'] / 100.00, 2)

            ## II ##
            order_line['l10n_br_ii_base'] = round(item.l10n_br_total_cif_brl + item.l10n_br_total_adicional_brl, 2)
            order_line['l10n_br_ii_aliquota'] = item.l10n_br_di_adicao_id.l10n_br_ii_aliquota
            order_line['l10n_br_ii_valor'] = round(order_line['l10n_br_ii_base'] * order_line['l10n_br_ii_aliquota'] / 100.00, 2)
            order_line['l10n_br_ii_valor_aduaneira'] = round(item.l10n_br_total_aduaneira_brl, 2)
            order_line['l10n_br_di_adicao_id'] = item.l10n_br_di_adicao_id.id

            ## IPI ##
            order_line['l10n_br_ipi_enq'] = '999'
            order_line['l10n_br_ipi_cst'] = item.l10n_br_di_adicao_id.l10n_br_ipi_cst
            order_line['l10n_br_ipi_base'] = order_line['l10n_br_ii_base'] + order_line['l10n_br_ii_valor']
            order_line['l10n_br_ipi_aliquota'] = item.l10n_br_di_adicao_id.l10n_br_ipi_aliquota
            order_line['l10n_br_ipi_valor'] = round(order_line['l10n_br_ipi_base'] * order_line['l10n_br_ipi_aliquota'] / 100.00, 2)

            ## ICMS ##
            order_line['l10n_br_icms_modalidade_base'] = item.l10n_br_di_adicao_id.l10n_br_icms_modalidade_base
            order_line['l10n_br_icms_cst'] = item.l10n_br_di_adicao_id.l10n_br_icms_cst
            order_line['l10n_br_icms_aliquota'] = item.l10n_br_di_adicao_id.l10n_br_icms_aliquota
            order_line['l10n_br_icms_reducao_base'] = item.l10n_br_di_adicao_id.l10n_br_icms_reducao_base
            # Rafael Petrella - 10/2/21 - Na importação quando aliquota ICMS 0% base precisa ser 0.00
            if order_line['l10n_br_icms_aliquota'] == 0.00:
                order_line['l10n_br_icms_base'] = 0.00
            else:
                order_line['l10n_br_icms_base'] = round(item.l10n_br_total_cif_brl + item.l10n_br_total_adicional_brl + item.l10n_br_total_aduaneira_brl + order_line['l10n_br_ii_valor'] + order_line['l10n_br_ipi_valor'] + order_line['l10n_br_pis_valor'] + order_line['l10n_br_cofins_valor'], 2) / (1 - (order_line['l10n_br_icms_aliquota'] / 100.00))

            order_line['l10n_br_icms_base'] = round(order_line['l10n_br_icms_base'] * (1.00 - (order_line['l10n_br_icms_reducao_base']/100.00)), 2)            
            
            order_line['l10n_br_icms_valor'] = round(order_line['l10n_br_icms_base'] * order_line['l10n_br_icms_aliquota'] / 100.00, 2)

            order_lines.append((0, 0, order_line))

        purchase_ids = []
        n = 200
        for n_order_lines in [order_lines[i:i + n] for i in range(0, len(order_lines), n)]:        

            pedido_compra_vals = {}

            pedido_compra_vals["partner_id"] = self.partner_id.id
            pedido_compra_vals["payment_term_id"] = self.payment_term_id.id
            pedido_compra_vals["incoterm_id"] = self.incoterm_id.id
            pedido_compra_vals["l10n_br_tipo_pedido"] = 'importacao'
            pedido_compra_vals['l10n_br_imposto_auto'] = True

            pedido_compra_vals["order_line"] = n_order_lines
            pedido_compra = self.env['purchase.order'].create(pedido_compra_vals)
            pedido_compra.onchange_l10n_br_calcular_imposto()

            pedido_compra.write({'l10n_br_imposto_auto': False})
            for i, item in enumerate(pedido_compra.order_line):
                item.write(n_order_lines[i][2])

            pedido_compra.onchange_l10n_br_calcular_imposto()

            purchase_ids.append(pedido_compra.id)

        self.write({
            'purchase_ids': [(6,0,purchase_ids)],
            'state': '03',
        })

        view_id = self.env.ref('purchase.purchase_order_form').id

        return {
            'name': 'Pedido de Compra',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id,'form')],
            'res_model': 'purchase.order',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': purchase_ids[0],
        }

    def action_rascunho(self):

        self.ensure_one()
        self.write({'state': '01'})

class L10nBrDiDespesa(models.Model):
    _name = 'l10n_br_ciel_it_account.di.despesa'
    _description = 'Despesas da DI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_di_id = fields.Many2one('l10n_br_ciel_it_account.di', string='DI', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    name = fields.Char(string='Descrição')
    l10n_br_tipo_despesa = fields.Selection( TIPO_DESPESA_IMPORTACAO, string='Tipo de Despesa', required=True )
    currency_id = fields.Many2one('res.currency', string='Moeda', required=True )
    l10n_br_valor = fields.Float(string='Valor Total', required=True, digits = (12,6) )
    l10n_br_valor_brl = fields.Float(string='Valor Total (BRL)', digits = (12,6) )
    
class L10nBrDiLine(models.Model):
    _name = 'l10n_br_ciel_it_account.di.line'
    _description = 'Linhas da DI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_di_id = fields.Many2one('l10n_br_ciel_it_account.di', string='DI', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    l10n_br_di_adicao_id = fields.Many2one('l10n_br_ciel_it_account.di.adicao', string='Adição', required=True)
    l10n_br_quantidade = fields.Float( string='Quantidade', required=True, digits = (12,6) )
    uom_id = fields.Many2one('uom.uom', string='UoM', required=True )
    l10n_br_peso = fields.Float('Peso Unitário', digits='Stock Weight')
    l10n_br_peso_total = fields.Float('Peso Total', digits='Stock Weight', store=True, compute="_get_l10n_br_peso_total" )
    product_id = fields.Many2one('product.product', string='Produto', required=True )
    currency_id = fields.Many2one('res.currency', string='Moeda', required=True )
    l10n_br_valor = fields.Float(string='Valor Unitário FOB', required=True, digits = (12,6) )
    l10n_br_total = fields.Float(string='Valor Total FOB', digits = (12,6), store=True, compute="_get_l10n_br_total" )
    l10n_br_valor_brl = fields.Float(string='Valor Unitário FOB (BRL)', digits = (12,6) )
    l10n_br_total_brl = fields.Float(string='Valor Total FOB (BRL)', digits = (12,6), store=True, compute="_get_l10n_br_total" )
    l10n_br_valor_cif_brl = fields.Float(string='Valor Unitário CIF (BRL)', digits = (12,6) )
    l10n_br_total_cif_brl = fields.Float(string='Valor Total CIF (BRL)', digits = (12,6), store=True, compute="_get_l10n_br_total" )
    l10n_br_valor_adicional_brl = fields.Float(string='Valor Unitário Adicional (BRL)', digits = (12,6) )
    l10n_br_total_adicional_brl = fields.Float(string='Valor Total Adicional (BRL)', digits = (12,6), store=True, compute="_get_l10n_br_total" )
    l10n_br_valor_aduaneira_brl = fields.Float(string='Valor Unitário Aduaneira (BRL)', digits = (12,6) )
    l10n_br_total_aduaneira_brl = fields.Float(string='Valor Total Aduaneira (BRL)', digits = (12,6), store=True, compute="_get_l10n_br_total" )
    name = fields.Char(string='Descrição')

    @api.depends('l10n_br_quantidade', 'l10n_br_valor', 'l10n_br_valor_brl', 'l10n_br_valor_cif_brl', 'l10n_br_valor_adicional_brl', 'l10n_br_valor_aduaneira_brl')
    def _get_l10n_br_total(self):
        for record in self:
            record.l10n_br_total = (record.l10n_br_valor * record.l10n_br_quantidade)
            record.l10n_br_total_brl = (record.l10n_br_valor_brl * record.l10n_br_quantidade)
            record.l10n_br_total_cif_brl = (record.l10n_br_valor_cif_brl * record.l10n_br_quantidade)
            record.l10n_br_total_adicional_brl = (record.l10n_br_valor_adicional_brl * record.l10n_br_quantidade)
            record.l10n_br_total_aduaneira_brl = (record.l10n_br_valor_aduaneira_brl * record.l10n_br_quantidade)
            
    @api.depends('l10n_br_quantidade', 'l10n_br_peso')
    def _get_l10n_br_peso_total(self):
        for record in self:
            record.l10n_br_peso_total = (record.l10n_br_peso * record.l10n_br_quantidade)
            
    @api.onchange('product_id')
    def onchange_product_id(self):
        for item in self:
            item.uom_id = item.product_id.uom_po_id.id
            item.l10n_br_peso = item.product_id.weight
            item.name = item.product_id.name

class L10nBrDiAdicao(models.Model):
    _name = 'l10n_br_ciel_it_account.di.adicao'
    _description = 'Adições da DI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_di_id = fields.Many2one('l10n_br_ciel_it_account.di', string='DI', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    name = fields.Char( string='Adição', compute='_compute_name', store=True )
    l10n_br_numero = fields.Integer( string='Número', required=True )
    l10n_br_icms_modalidade_base = fields.Selection( MODALIDADE_ICMS, string='Modalidade de Determinação da BC do ICMS' )
    l10n_br_icms_cst = fields.Selection( ICMS_CST, string='Código de Situação Tributária do ICMS' )
    l10n_br_icms_aliquota = fields.Float( string='ICMS (%)' )
    l10n_br_icms_reducao_base = fields.Float( string='Redução da BC do ICMS (%)', digits = (12,4) )
    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )
    l10n_br_ipi_aliquota = fields.Float( string='IPI (%)' )
    l10n_br_ii_aliquota = fields.Float( string='II (%)' )
    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_pis_aliquota = fields.Float( string='PIS (%)' )
    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )
    l10n_br_cofins_aliquota = fields.Float( string='COFINS (%)' )
    
    @api.depends('l10n_br_numero','name')
    def _compute_name(self):
        for line in self:
            line.name = "{}/{}".format(line.l10n_br_di_id.name, line.l10n_br_numero)

class L10nBrDiMoeda(models.Model):
    _name = 'l10n_br_ciel_it_account.di.moeda'
    _description = 'Moedas da DI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_di_id = fields.Many2one('l10n_br_ciel_it_account.di', string='DI', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    currency_id = fields.Many2one('res.currency', string='Moeda', required=True )
    l10n_br_taxa = fields.Float(string='Taxa', required=True, digits = (12,6) )

class AccountTax(models.Model):
    _inherit = 'account.tax'

    name = fields.Char(index=True)

    def name_get(self):
        result = []
        for item in self:
            result.append((item.id, item.description or item.name))
        return result

    def _clear_tax(self, limit=1000):

        if dtime(23,0) <= datetime.now(pytz.timezone('America/Sao_Paulo')).time() or datetime.now(pytz.timezone('America/Sao_Paulo')).time() <= dtime(5,00):
            sql_query = """
                    SELECT A01.id
                    FROM account_tax A01
                    WHERE NOT A01.name LIKE '%[*]%'
                      AND NOT EXISTS(SELECT 1 FROM account_tax_sale_order_line_rel A02 WHERE A02.account_tax_id = A01.id)
                      AND NOT EXISTS(SELECT 1 FROM account_tax_purchase_order_line_rel A02 WHERE A02.account_tax_id = A01.id)
                      AND NOT EXISTS(SELECT 1 FROM account_tax_sale_advance_payment_inv_rel A02 WHERE A02.account_tax_id = A01.id)
                      AND NOT EXISTS(SELECT 1 FROM account_move_line_account_tax_rel A02 WHERE A02.account_tax_id = A01.id)
                      AND NOT EXISTS(SELECT 1 FROM account_move_line A02 WHERE A02.tax_line_id = A01.id)
                    ORDER BY A01.id DESC
                    LIMIT """ + str(limit) + ";"
            self.env.cr.execute(sql_query)
            ids = [x[0] for x in self.env.cr.fetchall()]
            for id in ids:
                try:
                    self.browse(id).unlink()
                except Exception as e:
                    _logger.info(str(e))
                    pass

class AccountTaxRepartitionLine(models.Model):
    _inherit = "account.tax.repartition.line"

    invoice_tax_id = fields.Many2one(index=True)

class L10nBrNfeXml(models.Model):
    _name = 'l10n_br_ciel_it_account.nfe.xml'
    _description = 'NF-e XML'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char( 'Name' )

    l10n_br_chave_nf = fields.Char( string='Chave da Nota Fiscal', copy=False )
    l10n_br_arquivo_xml = fields.Binary( string='Arquivo XML', readonly=True, copy=False )
    l10n_br_nome_arquivo_xml = fields.Char( compute='_get_nome_arquivo_xml', readonly=True, copy=False )

    def _get_nome_arquivo_xml(self):
        self.l10n_br_nome_arquivo_xml = self.l10n_br_chave_nf + '-nfe.xml'


class L10nBrDfe(models.Model):
    _name = 'l10n_br_ciel_it_account.dfe'
    _description = 'DF-e'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Número',required=True, readonly=True, copy=False, default='/')
    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_ENTRADA, string='Tipo de Pedido', default='compra', track_visibility='onchange' )
    l10n_br_status = fields.Selection( DFE_STATUS, string='Situação', default='01', copy=False, track_visibility='onchange' )
    partner_id = fields.Many2one( 'res.partner', string='Fornecedor', track_visibility='onchange' )
    purchase_id = fields.Many2one('purchase.order', string='Pedido de Compra', copy=False, track_visibility='onchange')
    purchase_fiscal_id = fields.Many2one('purchase.order', string='Pedido de Compra (Escrituração)', copy=False, track_visibility='onchange')
    l10n_br_numero_parcelas = fields.Integer( string='Número de Parcelas', track_visibility='onchange' )
    l10n_br_data_entrada = fields.Date( string='Data de Entrada', track_visibility='onchange' )

    payment_reference = fields.Char(string="Referencia de Pagamento", copy=False)

    l10n_br_body_xml_dfe = fields.Text( string='Conteudo XML', readonly=True, copy=False )
    l10n_br_xml_body_dfe = fields.Text( string="Body XML DF-e", copy=False, readonly=True )
    l10n_br_xml_dfe = fields.Binary( string="XML DF-e", copy=False, track_visibility='onchange' )
    l10n_br_xml_dfe_fname = fields.Char( string="Arquivo XML DF-e", compute="_get_l10n_br_xml_dfe_fname" )
    l10n_br_pdf_dfe = fields.Binary( string="DANFE DF-e", copy=False, track_visibility='onchange' )
    l10n_br_pdf_dfe_fname = fields.Char( string="Arquivo DANFE DF-e", compute="_get_l10n_br_pdf_dfe_fname" )

    protnfe_infprot_nprot = fields.Char( string='Protocolo', readonly=True )
    protnfe_infprot_digval = fields.Char( string='Digito Validador', readonly=True )
    protnfe_infnfe_chnfe = fields.Char( string='Chave de Acesso', readonly=True )
    nfe_infnfe_dest_cnpj = fields.Char( string='CNPJ Destinatário', readonly=True )
    nfe_infnfe_emit_cnpj = fields.Char( string='CNPJ Emitente', readonly=True )
    nfe_infnfe_emit_ie = fields.Char( string='IE Emitente', readonly=True )
    nfe_infnfe_emit_cpf = fields.Char( string='CPF Emitente', readonly=True )
    nfe_infnfe_emit_xnome = fields.Char( string='Razao Social', readonly=True )
    nfe_infnfe_emit_crt = fields.Char( string='Regime Tributário', readonly=True )
    nfe_infnfe_ide_nnf = fields.Char( string='Número da Nota', readonly=True )
    nfe_infnfe_ide_serie = fields.Char( string='Série da Nota', readonly=True )
    cte_infcte_ide_cmunini = fields.Char( string='Município de Origem', readonly=True )
    cte_infcte_ide_cmunfim = fields.Char( string='Município de Destino', readonly=True )
    nfe_infnfe_total_icmstot_vprod = fields.Float( string='Valor dos Produtos', readonly=True )
    nfe_infnfe_total_icmstot_vnf = fields.Float( string='Valor da Nota', readonly=True )
    nfe_infnfe_ide_dhemi = fields.Date( string='Data de Emissão', readonly=True )
    nfe_infnfe_emit_uf = fields.Char( string='UF Emitente', readonly=True )
    nfe_infnfe_dest_uf = fields.Char( string='UF Destinatário', readonly=True )
    nfe_infnfe_infadic_infcpl = fields.Char( string='Dados Adicionais', readonly=True )
    nfe_infnfe_total_icms_vicmsdeson = fields.Char( string='ICMS Desonerado', readonly=True )
    nfe_infnfe_total_icms_vbc = fields.Float( string='BC ICMS', readonly=True )
    nfe_infnfe_total_icms_vicms = fields.Float( string='Valor ICMS', readonly=True )
    nfe_infnfe_total_icms_vbcst = fields.Float( string='BC ICMS ST', readonly=True )
    nfe_infnfe_total_icms_vst = fields.Float( string='Valor ICMS ST', readonly=True )
    nfe_infnfe_total_icms_vipi = fields.Float( string='Valor IPI', readonly=True )
    nfe_infnfe_total_icms_vpis = fields.Float( string='Valor PIS', readonly=True )
    nfe_infnfe_total_icms_vcofins = fields.Float( string='Valor COFINS', readonly=True )
    nfe_infnfe_total_icms_vdesc = fields.Float( string='Valor do Desconto', readonly=True )
    nfe_infnfe_total_icms_voutro = fields.Float( string='Outras Despesas Acessórias', readonly=True )
    nfe_infnfe_total_icms_vseg = fields.Float( string='Valor do Seguro', readonly=True )
    nfe_infnfe_total_icms_vfrete = fields.Float( string='Valor do Frete', readonly=True )
    lines_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.dfe.line', string='Itens', inverse_name='dfe_id' )
    dups_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.dfe.pagamento', string='Pagamentos', inverse_name='dfe_id' )
    refs_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.dfe.referencia', string='Referências', inverse_name='dfe_id' )
    
    is_cte = fields.Boolean( string='CT-e', compute='_get_is_cte' )

    _sql_constraints = [
        ('protnfe_infnfe_chnfe', 'unique ("protnfe_infnfe_chnfe")', "Chave do DF-e já existe !"),
    ]
    
    def _sync_destinadas(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

        nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % (
            l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
            "DOCUMENTO%3DDFE",
        )

        url = "%s/ManagerAPIWeb/nfe/envia" % (
            l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }
        
        basic_auth = HTTPBasicAuth(
            l10n_br_documento_id.l10n_br_usuario,
            l10n_br_documento_id.l10n_br_senha,
        )

        try:

            response = requests.get(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

        except Exception as e:
            _logger.info(str(e))

    def _get_destinadas(self, days=7):

        end_time = datetime.now()
        now = end_time - timedelta(days)
        hour = timedelta(hours=1)
        while now <= end_time:
        
            def _format_cnpj_cpf(cnpj_cpf):
                if cnpj_cpf:
                    return cnpj_cpf.replace("/","").replace("-","").replace(".","")
                else:
                    return ""

            l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

            nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&origem=2&Filtro=%s and %s&Campos=chave,cnpj,nnf,serie,dtemissao" % (
                l10n_br_documento_id.l10n_br_grupo,
                _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
                "dtemissao >= '%s'" % now.strftime('%Y-%m-%d %H:%M:%S'),
                "dtemissao <= '%s'" % (now + hour).strftime('%Y-%m-%d %H:%M:%S'),
            )

            url = "%s/ManagerAPIWeb/nfe/consulta?%s" % (
                l10n_br_documento_id.l10n_br_url,
                nfetx2
            )

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
            }

            basic_auth = HTTPBasicAuth(
                l10n_br_documento_id.l10n_br_usuario,
                l10n_br_documento_id.l10n_br_senha,
            )

            try:

                response = requests.get(url, auth=basic_auth, headers=headers, data={})

                for retorno in response.text.split("\n"):
                    if "EXCEPTION" in retorno:
                        continue

                    campos = retorno.split(",")
                    if campos and len(campos) == 5:
                        dfe_id = self.env['l10n_br_ciel_it_account.dfe'].search([('protnfe_infnfe_chnfe','=',campos[0])],limit=1)
                        if not dfe_id:
                            dfe_id = self.env['l10n_br_ciel_it_account.dfe'].create({
                                "protnfe_infnfe_chnfe": campos[0],
                                "nfe_infnfe_emit_cnpj": campos[1],
                                "nfe_infnfe_ide_nnf": campos[2],
                                "nfe_infnfe_ide_serie": campos[3],
                                "nfe_infnfe_ide_dhemi": datetime.strptime(campos[4][0:10],'%d/%m/%Y'),
                            })

                            to_write = {}
                            
                            if dfe_id.nfe_infnfe_emit_cnpj:
                                partner_id = self.env["res.partner"].search([("l10n_br_cnpj","=",dfe_id.nfe_infnfe_emit_cnpj)],limit=1)
                                if partner_id:
                                    to_write["partner_id"] = partner_id.id
                                    if dfe_id.nfe_infnfe_emit_ie:
                                        partner_id.write({'l10n_br_ie':dfe_id.nfe_infnfe_emit_ie})
                            
                            if to_write:
                                dfe_id.update(to_write)

                            dfe_id.action_sincronizar_dfe()

            except Exception as e:
                _logger.info("Exception-----%s" % (e))
                _logger.info(sys.exc_info()[0])
                _logger.info(sys.exc_info()[2].tb_lineno)

            now += hour

    def _update_parse_nfe(self):
    
        tag_det = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}det'
        tag_det_imposto_icms_predbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}pRedBC'

        for dfe_id in self:
            xml_root = ET.ElementTree(ET.fromstring(dfe_id.l10n_br_body_xml_dfe)).getroot()

            for idx, line_item in enumerate(xml_root.findall(tag_det)):
        
                documento_item_values = {}

                documento_item_values['det_imposto_icms_predbc'] = ''
                for item_tree in line_item.findall(tag_det_imposto_icms_predbc):
                    documento_item_values['det_imposto_icms_predbc'] = item_tree.text

                dfe_id.lines_ids[idx].write(documento_item_values)

    def _update_parse_cte(self):

        tag_cte_infcte_ide_cmunini = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}cMunIni'
        tag_cte_infcte_ide_cmunfim = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}cMunFim'
        for dfe_id in self:
            xml_root = ET.ElementTree(ET.fromstring(dfe_id.l10n_br_body_xml_dfe)).getroot()
            documento_values = {}

            documento_values['cte_infcte_ide_cmunini'] = ''
            for item_tree in xml_root.findall(tag_cte_infcte_ide_cmunini):
                documento_values['cte_infcte_ide_cmunini'] = item_tree.text

            documento_values['cte_infcte_ide_cmunfim'] = ''
            for item_tree in xml_root.findall(tag_cte_infcte_ide_cmunfim):
                documento_values['cte_infcte_ide_cmunfim'] = item_tree.text

            dfe_id.write(documento_values)

    @api.depends('protnfe_infnfe_chnfe')
    def _get_is_cte(self):
        for item in self:
            # CT-e - 57
            item.is_cte = item.protnfe_infnfe_chnfe and item.protnfe_infnfe_chnfe[20:22] == '57'

    def action_gerar_po_dfe(self):
        
        self.ensure_one()

        if not self.l10n_br_data_entrada:
            raise UserError('%s - Data de Entrada não foi informado.' % self.name)
        
        if not self.partner_id:
            raise UserError('%s - Fornecedor não foi informado.' % self.name)

        for item in self.lines_ids:
            if not item.product_id:
                raise UserError('%s - Produto não foi informado.' % self.name)

            if item.l10n_br_quantidade == 0.00:
                raise UserError('%s - Qtde (ESTOQUE) não foi informada.' % self.name)

        return self._create_po()

    def _create_po(self):

        def cancel_pedido_compra(old_purchase_id, new_purchase_id):
            
            if old_purchase_id.state != 'cancel':
                old_purchase_id.button_unlock()
                old_purchase_id.button_cancel()

            refs = ["<a href=# data-oe-model=purchase.order data-oe-id=%s>%s</a>" % tuple(name_get) for name_get in new_purchase_id.name_get()]
            message = _("Entrada via DF-e, Solicitação de compra atendida por: %s") % ','.join(refs)
            old_purchase_id.message_post(body=message)

            refs = ["<a href=# data-oe-model=purchase.order data-oe-id=%s>%s</a>" % tuple(name_get) for name_get in old_purchase_id.name_get()]
            message = _("Entrada via DF-e, Solicitação de compra origem: %s") % ','.join(refs)
            new_purchase_id.message_post(body=message)

        order_lines = []
        for item in self.lines_ids:
            order_line = {}

            fator = item.det_prod_qcom / item.l10n_br_quantidade

            order_line['dfe_line_id'] = item.id
            order_line['name'] = item.product_id.display_name
            order_line['product_id'] = item.product_id.id
            order_line['product_qty'] = item.l10n_br_quantidade
            order_line['product_uom'] = item.product_id.uom_id.id
            if not self.is_cte:
                order_line['price_unit'] = item.det_prod_vuncom * fator
            else:
                order_line['price_unit'] = item.det_prod_vprod * fator
            order_line['date_planned'] = fields.Datetime.to_datetime(self.l10n_br_data_entrada) + timedelta(hours=12)
            order_line['account_analytic_id'] = item.account_analytic_id.id            
            order_line['l10n_br_compra_indcom'] = item.l10n_br_compra_indcom
            order_line['discount'] = item.det_prod_vdesc / item.det_prod_vprod * 100.00
            order_lines.append((0, 0, order_line))
        
        pedido_compra_vals = {}
        
        pedido_compra_vals['dfe_id'] = self.id
        pedido_compra_vals["date_order"] = fields.Datetime.to_datetime(self.l10n_br_data_entrada) + timedelta(hours=12)
        pedido_compra_vals["partner_id"] = self.partner_id.id
        pedido_compra_vals["l10n_br_tipo_pedido"] = self.l10n_br_tipo_pedido
        pedido_compra_vals['l10n_br_imposto_auto'] = True
        pedido_compra_vals["l10n_br_frete"] = self.nfe_infnfe_total_icms_vfrete
        pedido_compra_vals["l10n_br_seguro"] = self.nfe_infnfe_total_icms_vseg
        pedido_compra_vals["l10n_br_despesas_acessorias"] = self.nfe_infnfe_total_icms_voutro
        
        if self.l10n_br_tipo_pedido in TIPO_PEDIDO_ENTRADA_NO_PAYMENT:
            company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', 'purchase'), ('l10n_br_no_payment', '=', True), ('l10n_br_tipo_pedido', '=', False), ('l10n_br_tipo_pedido_entrada', '=', self.l10n_br_tipo_pedido)]
            journal = self.env['account.journal'].search(domain, limit=1)
            if journal.fiscal_position_id:
                pedido_compra_vals['fiscal_position_id'] = journal.fiscal_position_id.id

        pedido_compra_vals["order_line"] = order_lines

        pedido_compra = self.env['purchase.order'].create(pedido_compra_vals)
        pedido_compra.onchange_l10n_br_calcular_imposto()
        
        pedido_compra.write({'l10n_br_imposto_auto': False})
        for item in pedido_compra.order_line:
            
            #################################
            ## FRETE / DESPESAS ACESSORIAS ##
            #################################
            order_line = {}

            order_line['l10n_br_frete'] = item.dfe_line_id.det_prod_vfrete
            order_line['l10n_br_seguro'] = item.dfe_line_id.det_prod_vseg
            order_line['l10n_br_despesas_acessorias'] = item.dfe_line_id.det_prod_voutro

            item.write(order_line)

            ################
            ##### ICMS #####
            ################
            order_line = {}

            order_line['l10n_br_icms_cst'] = item.l10n_br_icms_cst or ('00' if self.is_cte else '90')
            if not item.l10n_br_icms_cst and item.dfe_line_id.det_imposto_icms_cst:
                order_line['l10n_br_icms_cst'] = item.dfe_line_id.det_imposto_icms_cst

            order_line['l10n_br_icms_base'] = item.dfe_line_id.det_imposto_icms_vbc
            order_line['l10n_br_icms_aliquota'] = item.dfe_line_id.det_imposto_icms_picms
            order_line['l10n_br_icms_reducao_base'] = item.dfe_line_id.det_imposto_icms_predbc
            order_line['l10n_br_icmsst_base'] = item.dfe_line_id.det_imposto_icms_vbcst
            order_line['l10n_br_icmsst_retido_base'] = item.dfe_line_id.det_imposto_icms_vbcstret

            if order_line['l10n_br_icms_cst'] in ['00','10','20','60','70','101','201','500']:
                order_line['l10n_br_icms_valor'] = item.dfe_line_id.det_imposto_icms_vicms + item.dfe_line_id.det_imposto_icms_vcredicmssn
                order_line['l10n_br_icmsst_valor'] = item.dfe_line_id.det_imposto_icms_vicmsst
                order_line['l10n_br_icmsst_retido_valor'] = item.dfe_line_id.det_imposto_icms_vicmsstret
                order_line['l10n_br_icmsst_substituto_valor'] = item.dfe_line_id.det_imposto_icms_vicmssubstituto
            # Rafael Petrella - 31/08/2020
            # Conforme explicação no chamado 16961;
            elif order_line['l10n_br_icms_cst'] in ['51','90']:
                order_line['l10n_br_icms_valor'] = item.dfe_line_id.det_imposto_icms_vicms + item.dfe_line_id.det_imposto_icms_vcredicmssn
                order_line['l10n_br_icmsst_valor'] = item.dfe_line_id.det_imposto_icms_vicmsst
                order_line['l10n_br_icmsst_retido_valor'] = item.dfe_line_id.det_imposto_icms_vicmsstret
                order_line['l10n_br_icmsst_substituto_valor'] = item.dfe_line_id.det_imposto_icms_vicmssubstituto
            else:
                order_line['l10n_br_icms_valor_outros'] = item.dfe_line_id.det_imposto_icms_vicms + item.dfe_line_id.det_imposto_icms_vcredicmssn
                order_line['l10n_br_icmsst_valor_outros'] = item.dfe_line_id.det_imposto_icms_vicmsst
                order_line['l10n_br_icmsst_retido_valor_outros'] = item.dfe_line_id.det_imposto_icms_vicmsstret
                order_line['l10n_br_icmsst_substituto_valor_outros'] = item.dfe_line_id.det_imposto_icms_vicmssubstituto

            item.write(order_line)

            ################
            ###### IPI #####
            ################
            order_line = {}

            order_line['l10n_br_ipi_cst'] = item.l10n_br_ipi_cst or '49'
            if not item.l10n_br_ipi_cst and item.dfe_line_id.det_imposto_ipi_cst:
                if IPI_CST_ENTRADA.get(item.dfe_line_id.det_imposto_ipi_cst):
                    order_line['l10n_br_ipi_cst'] = IPI_CST_ENTRADA[item.dfe_line_id.det_imposto_ipi_cst]
                else:
                    order_line['l10n_br_ipi_cst'] = '49'

            order_line['l10n_br_ipi_base'] = item.dfe_line_id.det_imposto_ipi_vbc
            order_line['l10n_br_ipi_aliquota'] = item.dfe_line_id.det_imposto_ipi_pipi

            if order_line['l10n_br_ipi_cst'] == '00':
                order_line['l10n_br_ipi_valor'] = item.dfe_line_id.det_imposto_ipi_vipi
            else:
                order_line['l10n_br_ipi_valor_outros'] = item.dfe_line_id.det_imposto_ipi_vipi
                
            item.write(order_line)

        pedido_compra.onchange_l10n_br_calcular_imposto()

        self.write({
            'purchase_fiscal_id': pedido_compra.id,
            'l10n_br_status': '04',
        })

        if self.purchase_id:
            cancel_pedido_compra(self.purchase_id, pedido_compra)

        for line in [line for line in self.lines_ids if line.purchase_id]:
            cancel_pedido_compra(line.purchase_id, pedido_compra)

        view_id = self.env.ref('purchase.purchase_order_form').id

        return {
            'name': 'Pedido de Compra',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(view_id,'form')],
            'res_model': 'purchase.order',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': pedido_compra.id,
        }


    def action_rateio_dfe(self):
        
        self.ensure_one()

    def action_atualizar_dfe(self):

        self.ensure_one()
        
        to_write = {}
        
        if self.nfe_infnfe_emit_cnpj:
            partner_id = self.env["res.partner"].search([("l10n_br_cnpj","=",self.nfe_infnfe_emit_cnpj)],limit=1)
            if partner_id:
                to_write["partner_id"] = partner_id.id
                if self.nfe_infnfe_emit_ie:
                    partner_id.write({'l10n_br_ie':self.nfe_infnfe_emit_ie})
        
        if to_write:
            self.update(to_write)

        for item in self.lines_ids:
            to_write = {}
            if item.det_prod_cprod:
                product_id = self.env["product.product"].search([("default_code","=",item.det_prod_cprod)],limit=1)
                product_supplier_id = self.env["product.supplierinfo"].search([("product_code","=",item.det_prod_cprod),("name","=",self.partner_id.id)],limit=1)

                if not product_id and product_supplier_id:
                    product_id = self.env["product.product"].search([("product_tmpl_id","=",product_supplier_id.product_tmpl_id.id)],limit=1)

                if product_id:
                    to_write["product_id"] = product_id.id
                to_write["l10n_br_quantidade"] = item.det_prod_qcom * (product_supplier_id.fator_un if product_supplier_id else 1.00)

            if to_write:
                item.update(to_write)
        
        if self.l10n_br_numero_parcelas > 0 and len(self.dups_ids) == 0:

            to_write = {}
            l10n_br_numero_parcelas = self.l10n_br_numero_parcelas
            nfe_infnfe_total_icmstot_vnf = self.nfe_infnfe_total_icmstot_vnf / l10n_br_numero_parcelas
                
            dups_ids = []
            while l10n_br_numero_parcelas > 0:
                documento_item_values = { 'dfe_id': self.id }

                documento_item_values['cobr_dup_ndup'] = str(l10n_br_numero_parcelas).zfill(3)
                documento_item_values['cobr_dup_dvenc'] = fields.Date.context_today(self)+timedelta(days=30*l10n_br_numero_parcelas)
                documento_item_values['cobr_dup_vdup'] = nfe_infnfe_total_icmstot_vnf

                dups_ids.append((0,0,documento_item_values))
                l10n_br_numero_parcelas -= 1

            if dups_ids:
                to_write['dups_ids'] = dups_ids

            if to_write:
                self.update(to_write)            

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('nfe_infnfe_emit_cnpj'):
                if cnpj.validate(vals['nfe_infnfe_emit_cnpj']):
                    vals['nfe_infnfe_emit_cnpj'] = compatible.clear_punctuation(vals['nfe_infnfe_emit_cnpj'])
                    vals['nfe_infnfe_emit_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['nfe_infnfe_emit_cnpj'][:2], vals['nfe_infnfe_emit_cnpj'][2:5], vals['nfe_infnfe_emit_cnpj'][5:8], vals['nfe_infnfe_emit_cnpj'][8:12], vals['nfe_infnfe_emit_cnpj'][12:])
            if vals.get('nfe_infnfe_emit_cpf'):
                if cpf.validate(vals['nfe_infnfe_emit_cpf']):
                    vals['nfe_infnfe_emit_cpf'] = compatible.clear_punctuation(vals['nfe_infnfe_emit_cpf'])
                    vals['nfe_infnfe_emit_cpf'] = '{}.{}.{}-{}'.format(vals['nfe_infnfe_emit_cpf'][:3], vals['nfe_infnfe_emit_cpf'][3:6], vals['nfe_infnfe_emit_cpf'][6:9], vals['nfe_infnfe_emit_cpf'][9:])
        return super(L10nBrDfe, self).create(vals_list)

    def write(self, vals):
        if vals.get('nfe_infnfe_emit_cnpj'):
            if cnpj.validate(vals['nfe_infnfe_emit_cnpj']):
                vals['nfe_infnfe_emit_cnpj'] = compatible.clear_punctuation(vals['nfe_infnfe_emit_cnpj'])
                vals['nfe_infnfe_emit_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['nfe_infnfe_emit_cnpj'][:2], vals['nfe_infnfe_emit_cnpj'][2:5], vals['nfe_infnfe_emit_cnpj'][5:8], vals['nfe_infnfe_emit_cnpj'][8:12], vals['nfe_infnfe_emit_cnpj'][12:])
        if vals.get('nfe_infnfe_emit_cpf'):
            if cpf.validate(vals['nfe_infnfe_emit_cpf']):
                vals['nfe_infnfe_emit_cpf'] = compatible.clear_punctuation(vals['nfe_infnfe_emit_cpf'])
                vals['nfe_infnfe_emit_cpf'] = '{}.{}.{}-{}'.format(vals['nfe_infnfe_emit_cpf'][:3], vals['nfe_infnfe_emit_cpf'][3:6], vals['nfe_infnfe_emit_cpf'][6:9], vals['nfe_infnfe_emit_cpf'][9:])
        return super(L10nBrDfe, self).write(vals)

    def _get_l10n_br_xml_dfe_fname(self):
        for record in self:
            record.l10n_br_xml_dfe_fname = "%s-nfe.xml" % (record.protnfe_infnfe_chnfe or record.nfe_infnfe_ide_nnf)

    def _get_l10n_br_pdf_dfe_fname(self):
        for record in self:
            record.l10n_br_pdf_dfe_fname = "%s-nfe.pdf" % (record.protnfe_infnfe_chnfe or record.nfe_infnfe_ide_nnf)

    def action_sincronizar_dfe(self):
        """
        Sincronização de NFe's Destinadas
        """

        self.ensure_one()

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        if self.is_cte:

            l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([('l10n_br_modelo','=','55')],limit=1)

            nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&TipoNSU=0" % (
                l10n_br_documento_id.l10n_br_grupo,
                _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
            )

            url = "%s/ManagerAPIWeb/cte/consultadfe" % (
                l10n_br_documento_id.l10n_br_url,
            )

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
            }
            
            basic_auth = HTTPBasicAuth(
                l10n_br_documento_id.l10n_br_usuario,
                l10n_br_documento_id.l10n_br_senha,
            )

            def _format_message(message):
                return str(message)

            try:

                response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))
                
                if "Documento(s) localizado(s)" in response.text:

                    self.action_sincronizar_dfe()
                    return

                else:

                    to_write = {}

                    if self.name == '/':
                        to_write['name'] = self.env.ref("l10n_br_ciel_it_account.sequence_dfe").next_by_id(sequence_date=fields.Date.context_today(self))
                    to_write['l10n_br_status'] = '02'

                    if to_write:
                        self.update(to_write)
                        self.env.cr.commit()

            except Exception as e:
                raise UserError(_format_message(e))

        else:            

            l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

            nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % (
                l10n_br_documento_id.l10n_br_grupo,
                _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
                "DOCUMENTO%3DDFE%0ACHAVENOTA%3D" + self.protnfe_infnfe_chnfe,
            )

            url = "%s/ManagerAPIWeb/nfe/envia" % (
                l10n_br_documento_id.l10n_br_url,
            )

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
            }
            
            basic_auth = HTTPBasicAuth(
                l10n_br_documento_id.l10n_br_usuario,
                l10n_br_documento_id.l10n_br_senha,
            )

            def _format_message(message):
                return str(message)

            try:

                response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

                if response.text.split(",")[0] == "138":
                    to_write = {}

                    if self.name == '/':
                        to_write['name'] = self.env.ref("l10n_br_ciel_it_account.sequence_dfe").next_by_id(sequence_date=fields.Date.context_today(self))
                    to_write['l10n_br_status'] = '02'

                    if to_write:
                        self.update(to_write)
                        self.env.cr.commit()

                else:
                    raise UserError(_format_message(response.text))

            except Exception as e:
                raise UserError(_format_message(e))

    def action_ciencia_dfe(self):
        """
        CIENCIA da NFe's Destinada
        """

        self.ensure_one()

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_datetime(date):
            return datetime.strftime(date,'%Y-%m-%d')+'T'+datetime.strftime(date,'%H:%M:%S')

        if self.is_cte:

            l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

            nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Filtro=%s&Campos=situacao,chave,motivo" % (
                l10n_br_documento_id.l10n_br_grupo,
                _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
                "chave=" + self.protnfe_infnfe_chnfe,
            )

            url = "%s/ManagerAPIWeb/cte/consulta?%s" % (
                l10n_br_documento_id.l10n_br_url,
                nfetx2,
            )

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
            }
            
            basic_auth = HTTPBasicAuth(
                l10n_br_documento_id.l10n_br_usuario,
                l10n_br_documento_id.l10n_br_senha,
            )

            def _format_message(message):
                return str(message)

            try:

                #_logger.info([url,headers,nfetx2])
                response = requests.get(url, auth=basic_auth, headers=headers, data={})
                #_logger.info(response.text)
                
                if "AUTORIZADA" in response.text:

                    to_write = {}

                    to_write['l10n_br_status'] = '03'

                    if to_write:
                        self.update(to_write)
                        self.env.cr.commit()

                    self.action_gerar_xml_dfe()
                    self.action_gerar_danfe_dfe()

                else:
                    raise UserError(_format_message(response.text))

            except Exception as e:
                raise UserError(_format_message(e))

        else:
            l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

            nfetx2 = "encode=true&Grupo=%s&CNPJ=%s&Arquivo=%s" % (
                l10n_br_documento_id.l10n_br_grupo,
                _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
                "DOCUMENTO%3DDFE%0ATIPOEVENTO%3D2%0ACHAVENOTA%3D" + self.protnfe_infnfe_chnfe + "%0ADHEVENTO%3D" + _format_datetime(fields.Date.context_today(self)) + "%0AFUSO%3D-03:00%0A",
            )

            url = "%s/ManagerAPIWeb/nfe/envia" % (
                l10n_br_documento_id.l10n_br_url,
            )

            headers = {
                'Content-Type': "application/x-www-form-urlencoded",
            }
            
            basic_auth = HTTPBasicAuth(
                l10n_br_documento_id.l10n_br_usuario,
                l10n_br_documento_id.l10n_br_senha,
            )

            def _format_message(message):
                return str(message)

            try:

                response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

                if response.text.split(",")[0] == "AUTORIZADO" or response.text.split(",")[0] == "138":
                    to_write = {}

                    to_write['l10n_br_status'] = '03'

                    if to_write:
                        self.update(to_write)
                        self.env.cr.commit()

                    self.action_gerar_xml_dfe()
                    self.action_gerar_danfe_dfe()

                else:
                    raise UserError(_format_message(response.text))

            except Exception as e:
                raise UserError(_format_message(e))

    def action_gerar_danfe_dfe(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()

        if not self.protnfe_infnfe_chnfe:
            return

        l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)

        tipo_xml = 'cte' if self.is_cte else 'nfe'
        url = "%s/ManagerAPIWeb/%s/imprime?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s&URL=0" % (
            l10n_br_documento_id.l10n_br_url,
            tipo_xml,
            l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
            self.protnfe_infnfe_chnfe,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            l10n_br_documento_id.l10n_br_usuario,
            l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)

        self.update({
            'l10n_br_pdf_dfe': base64.b64encode(response.content)
        })
        self.env.cr.commit()

    def action_gerar_xml_dfe(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self.ensure_one()
        
        l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([],limit=1)
        
        tipo_xml = 'cte' if self.is_cte else 'nfe'
        url = "%s/ManagerAPIWeb/%s/xml?encode=true&Grupo=%s&CNPJ=%s&ChaveNota=%s" % (
            l10n_br_documento_id.l10n_br_url,
            tipo_xml,
            l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
            self.protnfe_infnfe_chnfe,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            l10n_br_documento_id.l10n_br_usuario,
            l10n_br_documento_id.l10n_br_senha,
        )

        response = requests.get(url, auth=basic_auth, headers=headers)
        body_xml = str(response.text)
        self.update({
            'l10n_br_xml_dfe': base64.b64encode(response.content),
            'l10n_br_body_xml_dfe': body_xml
        })
        self.env.cr.commit()

    def action_gerar_xmldanfe_dfe(self):
        self.ensure_one()
        self.action_gerar_xml_dfe()
        self.action_gerar_danfe_dfe()

    def action_parse_dfe(self):
        self.ensure_one()
        
        if self.is_cte:
            self.action_parse_cte()
        else:
            self.action_parse_nfe()

        to_write = {}
        to_write['l10n_br_status'] = '03'
        self.update(to_write)

    def action_parse_cte(self):
        self.ensure_one()
        
        tag_protnfe_infnfe_chnfe = './{http://www.portalfiscal.inf.br/cte}protCTe/{http://www.portalfiscal.inf.br/cte}infProt/{http://www.portalfiscal.inf.br/cte}chCTe'
        tag_nfe_infnfe_emit_cnpj = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}emit/{http://www.portalfiscal.inf.br/cte}CNPJ'
        tag_nfe_infnfe_emit_ie = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}emit/{http://www.portalfiscal.inf.br/cte}IE'
        tag_nfe_infnfe_emit_xnome = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}emit/{http://www.portalfiscal.inf.br/cte}xNome'
        tag_nfe_infnfe_ide_nnf = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}nCT'
        tag_nfe_infnfe_ide_serie = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}serie'
        tag_nfe_infnfe_ide_dhemi = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}dhEmi'
        tag_cte_infcte_ide_cmunini = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}cMunIni'
        tag_cte_infcte_ide_cmunfim = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}ide/{http://www.portalfiscal.inf.br/cte}cMunFim'
        tag_nfe_infnfe_total_icmstot_vnf = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}vPrest/{http://www.portalfiscal.inf.br/cte}vTPrest'
        tag_det_imposto_icms_vbc = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}imp/{http://www.portalfiscal.inf.br/cte}ICMS/*[1]/{http://www.portalfiscal.inf.br/cte}vBC'
        tag_det_imposto_icms_picms = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}imp/{http://www.portalfiscal.inf.br/cte}ICMS/*[1]/{http://www.portalfiscal.inf.br/cte}pICMS'
        tag_det_imposto_icms_vicms = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}imp/{http://www.portalfiscal.inf.br/cte}ICMS/*[1]/{http://www.portalfiscal.inf.br/cte}vICMS'

        tag_ref = './{http://www.portalfiscal.inf.br/cte}CTe/{http://www.portalfiscal.inf.br/cte}infCte/{http://www.portalfiscal.inf.br/cte}infCTeNorm/{http://www.portalfiscal.inf.br/cte}infDoc/{http://www.portalfiscal.inf.br/cte}infNFe'
        tag_infdoc_infnfe_chave = './{http://www.portalfiscal.inf.br/cte}chave'

        body_xml = base64.b64decode(self.l10n_br_xml_dfe)
        if not self.l10n_br_xml_dfe:
            self.update({
                'l10n_br_body_xml_dfe': body_xml,
                'l10n_br_status': '03'
            })
            self.env.cr.commit()

        xml_root = ET.ElementTree(ET.fromstring(self.l10n_br_body_xml_dfe or body_xml)).getroot()

        documento_values = {}

        documento_values['protnfe_infnfe_chnfe'] = ''
        for item_tree in xml_root.findall(tag_protnfe_infnfe_chnfe):
            documento_values['protnfe_infnfe_chnfe'] = item_tree.text

        documento_values['nfe_infnfe_emit_cnpj'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_cnpj):
            documento_values['nfe_infnfe_emit_cnpj'] = item_tree.text

        documento_values['nfe_infnfe_emit_ie'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_ie):
            documento_values['nfe_infnfe_emit_ie'] = item_tree.text

        documento_values['nfe_infnfe_emit_xnome'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_xnome):
            documento_values['nfe_infnfe_emit_xnome'] = item_tree.text

        documento_values['nfe_infnfe_ide_nnf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_nnf):
            documento_values['nfe_infnfe_ide_nnf'] = item_tree.text

        documento_values['nfe_infnfe_ide_serie'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_serie):
            documento_values['nfe_infnfe_ide_serie'] = item_tree.text

        documento_values['cte_infcte_ide_cmunini'] = ''
        for item_tree in xml_root.findall(tag_cte_infcte_ide_cmunini):
            documento_values['cte_infcte_ide_cmunini'] = item_tree.text

        documento_values['cte_infcte_ide_cmunfim'] = ''
        for item_tree in xml_root.findall(tag_cte_infcte_ide_cmunfim):
            documento_values['cte_infcte_ide_cmunfim'] = item_tree.text

        documento_values['nfe_infnfe_ide_dhemi'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_dhemi):
            documento_values['nfe_infnfe_ide_dhemi'] = datetime.strptime(item_tree.text[0:10],'%Y-%m-%d')

        documento_values['nfe_infnfe_total_icmstot_vnf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icmstot_vnf):
            documento_values['nfe_infnfe_total_icmstot_vnf'] = item_tree.text

        lines_ids = []
        documento_item_values = { 'dfe_id': self.id, 'det_prod_xprod': 'FRETE', 'det_prod_qcom': 1, 'det_prod_vprod': documento_values['nfe_infnfe_total_icmstot_vnf'] }

        documento_item_values['det_imposto_icms_vbc'] = ''
        for item_tree in xml_root.findall(tag_det_imposto_icms_vbc):
            documento_item_values['det_imposto_icms_vbc'] = item_tree.text
            documento_values['nfe_infnfe_total_icms_vbc'] = item_tree.text

        documento_item_values['det_imposto_icms_picms'] = ''
        for item_tree in xml_root.findall(tag_det_imposto_icms_picms):
            documento_item_values['det_imposto_icms_picms'] = item_tree.text

        documento_item_values['det_imposto_icms_vicms'] = ''
        for item_tree in xml_root.findall(tag_det_imposto_icms_vicms):
            documento_item_values['det_imposto_icms_vicms'] = item_tree.text
            documento_values['nfe_infnfe_total_icms_vicms'] = item_tree.text

        lines_ids.append((0,0,documento_item_values))

        documento_values['lines_ids'] = lines_ids

        dups_ids = []
        documento_item_values = { 'dfe_id': self.id }
        documento_item_values['cobr_dup_ndup'] = '01'
        documento_item_values['cobr_dup_dvenc'] = documento_values['nfe_infnfe_ide_dhemi']
        documento_item_values['cobr_dup_vdup'] = documento_values['nfe_infnfe_total_icmstot_vnf']
        dups_ids.append((0,0,documento_item_values))
        documento_values['dups_ids'] = dups_ids

        refs_ids = []
        for line_item in xml_root.findall(tag_ref):
            documento_item_values = { 'dfe_id': self.id }

            documento_item_values['infdoc_infnfe_chave'] = ''
            for item_tree in line_item.findall(tag_infdoc_infnfe_chave):
                documento_item_values['infdoc_infnfe_chave'] = item_tree.text

            refs_ids.append((0,0,documento_item_values))

        documento_values['refs_ids'] = refs_ids

        self.update(documento_values)
        self.env.cr.commit()


    def action_parse_nfe(self):
        self.ensure_one()

        tag_protnfe_infprot_nprot = './{http://www.portalfiscal.inf.br/nfe}protNFe/{http://www.portalfiscal.inf.br/nfe}infProt/{http://www.portalfiscal.inf.br/nfe}nProt'
        tag_protnfe_infprot_digval = './{http://www.portalfiscal.inf.br/nfe}protNFe/{http://www.portalfiscal.inf.br/nfe}infProt/{http://www.portalfiscal.inf.br/nfe}digVal'
        tag_protnfe_infnfe_chnfe = './{http://www.portalfiscal.inf.br/nfe}protNFe/{http://www.portalfiscal.inf.br/nfe}infProt/{http://www.portalfiscal.inf.br/nfe}chNFe'
        tag_nfe_infnfe_dest_cnpj = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}dest/{http://www.portalfiscal.inf.br/nfe}CNPJ'
        tag_nfe_infnfe_emit_cnpj = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}CNPJ'
        tag_nfe_infnfe_emit_ie = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}IE'
        tag_nfe_infnfe_emit_cpf = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}CPF'
        tag_nfe_infnfe_emit_xnome = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}xNome'
        tag_nfe_infnfe_emit_crt = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/{http://www.portalfiscal.inf.br/nfe}CRT'
        tag_nfe_infnfe_ide_nnf = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}nNF'
        tag_nfe_infnfe_ide_serie = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}serie'
        tag_nfe_infnfe_total_icmstot_vprod = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/{http://www.portalfiscal.inf.br/nfe}ICMSTot/{http://www.portalfiscal.inf.br/nfe}vProd'
        tag_nfe_infnfe_total_icmstot_vnf = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/{http://www.portalfiscal.inf.br/nfe}ICMSTot/{http://www.portalfiscal.inf.br/nfe}vNF'
        tag_nfe_infnfe_ide_dhemi = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}dhEmi'
        tag_nfe_infnfe_ide_demi = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}dEmi'
        tag_nfe_infnfe_emit_uf = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}emit/*[1]/{http://www.portalfiscal.inf.br/nfe}UF'
        tag_nfe_infnfe_dest_uf = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}dest/*[1]/{http://www.portalfiscal.inf.br/nfe}UF'
        tag_nfe_infnfe_infadic_infcpl = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}infAdic/{http://www.portalfiscal.inf.br/nfe}infCpl'
        tag_nfe_infnfe_total_icms_vicmsdeson = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMSDeson'
        tag_nfe_infnfe_total_icms_vbc = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vBC'
        tag_nfe_infnfe_total_icms_vicms = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMS'
        tag_nfe_infnfe_total_icms_vbcst = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vBCST'
        tag_nfe_infnfe_total_icms_vst = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vST'
        tag_nfe_infnfe_total_icms_vipi = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vIPI'
        tag_nfe_infnfe_total_icms_vpis = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vPIS'
        tag_nfe_infnfe_total_icms_vcofins = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vCOFINS'
        tag_nfe_infnfe_total_icms_vdesc = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vDesc'
        tag_nfe_infnfe_total_icms_voutro = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vOutro'
        tag_nfe_infnfe_total_icms_vfrete = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vFrete'
        tag_nfe_infnfe_total_icms_vseg = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}total/*[1]/{http://www.portalfiscal.inf.br/nfe}vSeg'

        tag_det = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}det'
        tag_det_prod_cprod = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}cProd'
        tag_det_prod_xprod = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}xProd'
        tag_det_prod_qcom = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}qCom'
        tag_det_prod_ucom = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}uCom'
        tag_det_prod_vuncom = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vUnCom'
        tag_det_prod_vdesc = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vDesc'
        tag_det_prod_vfrete = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vFrete'
        tag_det_prod_vseg = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vSeg'
        tag_det_prod_voutro = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vOutro'
        tag_det_prod_vseg = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vSeg'
        tag_det_prod_vprod = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}vProd'
        tag_det_prod_cfop = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}CFOP'
        tag_det_prod_ncm = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}NCM'
        tag_det_prod_xped = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}xPed'
        tag_det_prod_nitemped = './{http://www.portalfiscal.inf.br/nfe}prod/{http://www.portalfiscal.inf.br/nfe}nItemPed'
        tag_det_infadprod = './{http://www.portalfiscal.inf.br/nfe}infAdProd'
        tag_det_imposto_icms_vbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vBC'
        tag_det_imposto_icms_picms = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}pICMS'
        tag_det_imposto_icms_predbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}pRedBC'
        tag_det_imposto_icms_vicms = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMS'
        tag_det_imposto_icms_vbcst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vBCST'
        tag_det_imposto_icms_vicmsst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMSST'
        tag_det_imposto_icms_vbcstret = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vBCSTRet'
        tag_det_imposto_icms_vicmsstret = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMSSTRet'
        tag_det_imposto_icms_vicmssubstituto = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vICMSSubstituto'
        tag_det_imposto_icms_pcredsn = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}pCredSN'
        tag_det_imposto_icms_vcredicmssn = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}vCredICMSSN'
        tag_det_imposto_ipi_vbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}IPI/*[1]/{http://www.portalfiscal.inf.br/nfe}vBC'
        tag_det_imposto_ipi_pipi = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}IPI/*[1]/{http://www.portalfiscal.inf.br/nfe}pIPI'
        tag_det_imposto_ipi_vipi = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}IPI/*[1]/{http://www.portalfiscal.inf.br/nfe}vIPI'
        tag_det_imposto_cofins_vbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}COFINS/*[1]/{http://www.portalfiscal.inf.br/nfe}vBC'
        tag_det_imposto_cofins_pcofins = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}COFINS/*[1]/{http://www.portalfiscal.inf.br/nfe}pCOFINS'
        tag_det_imposto_cofins_vcofins = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}COFINS/*[1]/{http://www.portalfiscal.inf.br/nfe}vCOFINS'
        tag_det_imposto_cofins_cst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}COFINS/*[1]/{http://www.portalfiscal.inf.br/nfe}CST'
        tag_det_imposto_pis_vbc = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}PIS/*[1]/{http://www.portalfiscal.inf.br/nfe}vBC'
        tag_det_imposto_pis_ppis = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}PIS/*[1]/{http://www.portalfiscal.inf.br/nfe}pPIS'
        tag_det_imposto_pis_vpis = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}PIS/*[1]/{http://www.portalfiscal.inf.br/nfe}vPIS'
        tag_det_imposto_pis_cst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}PIS/*[1]/{http://www.portalfiscal.inf.br/nfe}CST'
        tag_det_imposto_icms_cst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}CST'
        tag_det_imposto_icms_orig = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}ICMS/*[1]/{http://www.portalfiscal.inf.br/nfe}orig'
        tag_det_imposto_ipi_cst = './{http://www.portalfiscal.inf.br/nfe}imposto/{http://www.portalfiscal.inf.br/nfe}IPI/*[1]/{http://www.portalfiscal.inf.br/nfe}CST'

        tag_refNFe = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}ide/{http://www.portalfiscal.inf.br/nfe}NFref/{http://www.portalfiscal.inf.br/nfe}refNFe'

        tag_dup = './{http://www.portalfiscal.inf.br/nfe}NFe/{http://www.portalfiscal.inf.br/nfe}infNFe/{http://www.portalfiscal.inf.br/nfe}cobr/{http://www.portalfiscal.inf.br/nfe}dup'
        tag_cobr_dup_ndup = './{http://www.portalfiscal.inf.br/nfe}nDup'
        tag_cobr_dup_dvenc = './{http://www.portalfiscal.inf.br/nfe}dVenc'
        tag_cobr_dup_vdup = './{http://www.portalfiscal.inf.br/nfe}vDup'

        body_xml = base64.b64decode(self.l10n_br_xml_dfe)
        if not self.l10n_br_xml_dfe:
            self.update({
                'l10n_br_body_xml_dfe': body_xml,
                'l10n_br_status': '03'
            })
            self.env.cr.commit()

        xml_root = ET.ElementTree(ET.fromstring(self.l10n_br_body_xml_dfe or body_xml)).getroot()

        documento_values = {}

        documento_values['protnfe_infprot_nprot'] = ''
        for item_tree in xml_root.findall(tag_protnfe_infprot_nprot):
            documento_values['protnfe_infprot_nprot'] = item_tree.text

        documento_values['protnfe_infprot_digval'] = ''
        for item_tree in xml_root.findall(tag_protnfe_infprot_digval):
            documento_values['protnfe_infprot_digval'] = item_tree.text

        documento_values['protnfe_infnfe_chnfe'] = ''
        for item_tree in xml_root.findall(tag_protnfe_infnfe_chnfe):
            documento_values['protnfe_infnfe_chnfe'] = item_tree.text

        documento_values['nfe_infnfe_dest_cnpj'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_dest_cnpj):
            documento_values['nfe_infnfe_dest_cnpj'] = item_tree.text

        documento_values['nfe_infnfe_emit_cnpj'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_cnpj):
            documento_values['nfe_infnfe_emit_cnpj'] = item_tree.text

        documento_values['nfe_infnfe_emit_ie'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_ie):
            documento_values['nfe_infnfe_emit_ie'] = item_tree.text

        documento_values['nfe_infnfe_emit_cpf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_cpf):
            documento_values['nfe_infnfe_emit_cpf'] = item_tree.text

        documento_values['nfe_infnfe_emit_xnome'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_xnome):
            documento_values['nfe_infnfe_emit_xnome'] = item_tree.text

        documento_values['nfe_infnfe_emit_crt'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_crt):
            documento_values['nfe_infnfe_emit_crt'] = item_tree.text

        documento_values['nfe_infnfe_ide_nnf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_nnf):
            documento_values['nfe_infnfe_ide_nnf'] = item_tree.text

        documento_values['nfe_infnfe_ide_serie'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_serie):
            documento_values['nfe_infnfe_ide_serie'] = item_tree.text

        documento_values['nfe_infnfe_total_icmstot_vprod'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icmstot_vprod):
            documento_values['nfe_infnfe_total_icmstot_vprod'] = item_tree.text

        documento_values['nfe_infnfe_total_icmstot_vnf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icmstot_vnf):
            documento_values['nfe_infnfe_total_icmstot_vnf'] = item_tree.text

        documento_values['nfe_infnfe_ide_dhemi'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_dhemi):
            documento_values['nfe_infnfe_ide_dhemi'] = datetime.strptime(item_tree.text[0:10],'%Y-%m-%d')
        for item_tree in xml_root.findall(tag_nfe_infnfe_ide_demi):
            documento_values['nfe_infnfe_ide_dhemi'] = datetime.strptime(item_tree.text[0:10],'%Y-%m-%d')

        documento_values['nfe_infnfe_emit_uf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_emit_uf):
            documento_values['nfe_infnfe_emit_uf'] = item_tree.text

        documento_values['nfe_infnfe_dest_uf'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_dest_uf):
            documento_values['nfe_infnfe_dest_uf'] = item_tree.text

        documento_values['nfe_infnfe_infadic_infcpl'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_infadic_infcpl):
            documento_values['nfe_infnfe_infadic_infcpl'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vicmsdeson'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vicmsdeson):
            documento_values['nfe_infnfe_total_icms_vicmsdeson'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vbc'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vbc):
            documento_values['nfe_infnfe_total_icms_vbc'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vicms'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vicms):
            documento_values['nfe_infnfe_total_icms_vicms'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vbcst'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vbcst):
            documento_values['nfe_infnfe_total_icms_vbcst'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vst'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vst):
            documento_values['nfe_infnfe_total_icms_vst'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vipi'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vipi):
            documento_values['nfe_infnfe_total_icms_vipi'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vpis'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vpis):
            documento_values['nfe_infnfe_total_icms_vpis'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vcofins'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vcofins):
            documento_values['nfe_infnfe_total_icms_vcofins'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vdesc'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vdesc):
            documento_values['nfe_infnfe_total_icms_vdesc'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_voutro'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_voutro):
            documento_values['nfe_infnfe_total_icms_voutro'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vfrete'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vfrete):
            documento_values['nfe_infnfe_total_icms_vfrete'] = item_tree.text

        documento_values['nfe_infnfe_total_icms_vseg'] = ''
        for item_tree in xml_root.findall(tag_nfe_infnfe_total_icms_vseg):
            documento_values['nfe_infnfe_total_icms_vseg'] = item_tree.text

        dups_ids = []
        for line_item in xml_root.findall(tag_dup):
            documento_item_values = { 'dfe_id': self.id }

            documento_item_values['cobr_dup_ndup'] = ''
            for item_tree in line_item.findall(tag_cobr_dup_ndup):
                documento_item_values['cobr_dup_ndup'] = item_tree.text

            documento_item_values['cobr_dup_dvenc'] = ''
            for item_tree in line_item.findall(tag_cobr_dup_dvenc):
                documento_item_values['cobr_dup_dvenc'] = item_tree.text

            documento_item_values['cobr_dup_vdup'] = ''
            for item_tree in line_item.findall(tag_cobr_dup_vdup):
                documento_item_values['cobr_dup_vdup'] = item_tree.text

            dups_ids.append((0,0,documento_item_values))

        documento_values['dups_ids'] = dups_ids

        lines_ids = []
        for line_item in xml_root.findall(tag_det):
            documento_item_values = { 'dfe_id': self.id, 'det_nitem': line_item.attrib['nItem'] }

            documento_item_values['det_prod_cprod'] = ''
            for item_tree in line_item.findall(tag_det_prod_cprod):
                documento_item_values['det_prod_cprod'] = item_tree.text

            documento_item_values['det_prod_xprod'] = ''
            for item_tree in line_item.findall(tag_det_prod_xprod):
                documento_item_values['det_prod_xprod'] = item_tree.text

            documento_item_values['det_prod_qcom'] = ''
            for item_tree in line_item.findall(tag_det_prod_qcom):
                documento_item_values['det_prod_qcom'] = item_tree.text

            documento_item_values['det_prod_ucom'] = ''
            for item_tree in line_item.findall(tag_det_prod_ucom):
                documento_item_values['det_prod_ucom'] = item_tree.text

            documento_item_values['det_prod_vuncom'] = ''
            for item_tree in line_item.findall(tag_det_prod_vuncom):
                documento_item_values['det_prod_vuncom'] = item_tree.text

            documento_item_values['det_prod_vdesc'] = ''
            for item_tree in line_item.findall(tag_det_prod_vdesc):
                documento_item_values['det_prod_vdesc'] = item_tree.text

            documento_item_values['det_prod_vfrete'] = ''
            for item_tree in line_item.findall(tag_det_prod_vfrete):
                documento_item_values['det_prod_vfrete'] = item_tree.text

            documento_item_values['det_prod_vseg'] = ''
            for item_tree in line_item.findall(tag_det_prod_vseg):
                documento_item_values['det_prod_vseg'] = item_tree.text

            documento_item_values['det_prod_voutro'] = ''
            for item_tree in line_item.findall(tag_det_prod_voutro):
                documento_item_values['det_prod_voutro'] = item_tree.text

            documento_item_values['det_prod_vseg'] = ''
            for item_tree in line_item.findall(tag_det_prod_vseg):
                documento_item_values['det_prod_vseg'] = item_tree.text

            documento_item_values['det_prod_vprod'] = ''
            for item_tree in line_item.findall(tag_det_prod_vprod):
                documento_item_values['det_prod_vprod'] = item_tree.text

            documento_item_values['det_prod_cfop'] = ''
            for item_tree in line_item.findall(tag_det_prod_cfop):
                documento_item_values['det_prod_cfop'] = item_tree.text

            documento_item_values['det_prod_ncm'] = ''
            for item_tree in line_item.findall(tag_det_prod_ncm):
                documento_item_values['det_prod_ncm'] = item_tree.text

            documento_item_values['det_prod_xped'] = ''
            for item_tree in line_item.findall(tag_det_prod_xped):
                documento_item_values['det_prod_xped'] = item_tree.text

            documento_item_values['det_prod_nitemped'] = ''
            for item_tree in line_item.findall(tag_det_prod_nitemped):
                documento_item_values['det_prod_nitemped'] = item_tree.text

            documento_item_values['det_infadprod'] = ''
            for item_tree in line_item.findall(tag_det_infadprod):
                documento_item_values['det_infadprod'] = item_tree.text

            documento_item_values['det_imposto_icms_vbc'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vbc):
                documento_item_values['det_imposto_icms_vbc'] = item_tree.text

            documento_item_values['det_imposto_icms_picms'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_picms):
                documento_item_values['det_imposto_icms_picms'] = item_tree.text

            documento_item_values['det_imposto_icms_predbc'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_predbc):
                documento_item_values['det_imposto_icms_predbc'] = item_tree.text

            documento_item_values['det_imposto_icms_vicms'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vicms):
                documento_item_values['det_imposto_icms_vicms'] = item_tree.text

            documento_item_values['det_imposto_icms_vbcst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vbcst):
                documento_item_values['det_imposto_icms_vbcst'] = item_tree.text

            documento_item_values['det_imposto_icms_vicmsst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vicmsst):
                documento_item_values['det_imposto_icms_vicmsst'] = item_tree.text

            documento_item_values['det_imposto_icms_vbcstret'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vbcstret):
                documento_item_values['det_imposto_icms_vbcstret'] = item_tree.text

            documento_item_values['det_imposto_icms_vicmsstret'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vicmsstret):
                documento_item_values['det_imposto_icms_vicmsstret'] = item_tree.text

            documento_item_values['det_imposto_icms_vicmssubstituto'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vicmssubstituto):
                documento_item_values['det_imposto_icms_vicmssubstituto'] = item_tree.text

            documento_item_values['det_imposto_icms_pcredsn'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_pcredsn):
                documento_item_values['det_imposto_icms_pcredsn'] = item_tree.text

            documento_item_values['det_imposto_icms_vcredicmssn'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_vcredicmssn):
                documento_item_values['det_imposto_icms_vcredicmssn'] = item_tree.text

            documento_item_values['det_imposto_ipi_vbc'] = ''
            for item_tree in line_item.findall(tag_det_imposto_ipi_vbc):
                documento_item_values['det_imposto_ipi_vbc'] = item_tree.text

            documento_item_values['det_imposto_ipi_pipi'] = ''
            for item_tree in line_item.findall(tag_det_imposto_ipi_pipi):
                documento_item_values['det_imposto_ipi_pipi'] = item_tree.text

            documento_item_values['det_imposto_ipi_vipi'] = ''
            for item_tree in line_item.findall(tag_det_imposto_ipi_vipi):
                documento_item_values['det_imposto_ipi_vipi'] = item_tree.text

            documento_item_values['det_imposto_cofins_vbc'] = ''
            for item_tree in line_item.findall(tag_det_imposto_cofins_vbc):
                documento_item_values['det_imposto_cofins_vbc'] = item_tree.text

            documento_item_values['det_imposto_cofins_pcofins'] = ''
            for item_tree in line_item.findall(tag_det_imposto_cofins_pcofins):
                documento_item_values['det_imposto_cofins_pcofins'] = item_tree.text

            documento_item_values['det_imposto_cofins_vcofins'] = ''
            for item_tree in line_item.findall(tag_det_imposto_cofins_vcofins):
                documento_item_values['det_imposto_cofins_vcofins'] = item_tree.text

            documento_item_values['det_imposto_cofins_cst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_cofins_cst):
                documento_item_values['det_imposto_cofins_cst'] = item_tree.text

            documento_item_values['det_imposto_pis_vbc'] = ''
            for item_tree in line_item.findall(tag_det_imposto_pis_vbc):
                documento_item_values['det_imposto_pis_vbc'] = item_tree.text

            documento_item_values['det_imposto_pis_ppis'] = ''
            for item_tree in line_item.findall(tag_det_imposto_pis_ppis):
                documento_item_values['det_imposto_pis_ppis'] = item_tree.text

            documento_item_values['det_imposto_pis_vpis'] = ''
            for item_tree in line_item.findall(tag_det_imposto_pis_vpis):
                documento_item_values['det_imposto_pis_vpis'] = item_tree.text

            documento_item_values['det_imposto_pis_cst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_pis_cst):
                documento_item_values['det_imposto_pis_cst'] = item_tree.text

            documento_item_values['det_imposto_icms_cst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_cst):
                documento_item_values['det_imposto_icms_cst'] = item_tree.text

            documento_item_values['det_imposto_icms_orig'] = ''
            for item_tree in line_item.findall(tag_det_imposto_icms_orig):
                documento_item_values['det_imposto_icms_orig'] = item_tree.text

            documento_item_values['det_imposto_ipi_cst'] = ''
            for item_tree in line_item.findall(tag_det_imposto_ipi_cst):
                documento_item_values['det_imposto_ipi_cst'] = item_tree.text

            lines_ids.append((0,0,documento_item_values))

        documento_values['lines_ids'] = lines_ids

        self.update(documento_values)
        self.env.cr.commit()

class L10nBrDfePagamento(models.Model):
    _name = 'l10n_br_ciel_it_account.dfe.pagamento'
    _inherit = ['mail.thread']
    _description = 'Pagamento Documento Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    dfe_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe', string='Documento' )

    cobr_dup_ndup = fields.Char( string='Parcela', readonly=True )
    cobr_dup_dvenc = fields.Date( string='Vencimento', track_visibility='onchange' )
    cobr_dup_vdup = fields.Float( string='Valor', track_visibility='onchange' )

class L10nBrDfeReferencia(models.Model):
    _name = 'l10n_br_ciel_it_account.dfe.referencia'
    _inherit = ['mail.thread']
    _description = 'Referencia Documento Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    dfe_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe', string='Documento' )

    infdoc_infnfe_chave = fields.Char( string='Chave', readonly=True, track_visibility='onchange' )

class L10nBrDfeLine(models.Model):
    _name = 'l10n_br_ciel_it_account.dfe.line'
    _inherit = ['mail.thread']
    _description = 'Item Documento Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    dfe_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.dfe', string='Documento' )
    det_nitem = fields.Char( string='Item', readonly=True )
    purchase_id = fields.Many2one('purchase.order', string='Pedido de Compra', copy=False, track_visibility='onchange')
    product_id = fields.Many2one('product.product', string='Produto', track_visibility='onchange' )
    l10n_br_quantidade = fields.Float( string='Qtde (Estoque)', digits = (12,6), track_visibility='onchange' )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account', track_visibility='onchange')

    det_prod_cprod = fields.Char( string='Código do Produto', readonly=True )
    det_prod_xprod = fields.Char( string='Descrição do Produto', readonly=True )
    det_prod_qcom = fields.Float( string='Qtde DF-e', readonly=True )
    det_prod_ucom = fields.Char( string='Unidade', readonly=True )
    det_prod_vuncom = fields.Float( string='Valor Unitário', digits = (12,10), readonly=True )
    det_prod_vdesc = fields.Float( string='Valor Desconto', readonly=True )
    det_prod_vfrete = fields.Float( string='Valor Frete', readonly=True )
    det_prod_vseg = fields.Float( string='Valor Seguro', readonly=True )
    det_prod_voutro = fields.Float( string='Valor Outro', readonly=True )
    det_prod_vseg = fields.Float( string='Valor Seguro', readonly=True )
    det_prod_vprod = fields.Float( string='Valor Total do Item', readonly=True )
    det_prod_cfop = fields.Char( string='CFOP', readonly=True )
    det_prod_ncm = fields.Char( string='NCM', readonly=True )
    det_prod_xped = fields.Char( string='Pedido Cliente', readonly=True )
    det_prod_nitemped = fields.Char( string='Item Pedido Cliente', readonly=True )
    det_infadprod = fields.Char( string='Dados Adicionais do Produto', readonly=True )
    det_imposto_icms_vbc = fields.Float( string='BC ICMS', readonly=True )
    det_imposto_icms_picms = fields.Float( string='% ICMS', readonly=True )
    det_imposto_icms_predbc = fields.Float( string='% Red ICMS', readonly=True )
    det_imposto_icms_vicms = fields.Float( string='Valor ICMS', readonly=True )
    det_imposto_icms_vbcst = fields.Float( string='BC ICMS ST', readonly=True )
    det_imposto_icms_vicmsst = fields.Float( string='Valor ICMS ST', readonly=True )
    det_imposto_icms_vbcstret = fields.Float( string='BC ICMS ST Ret' )
    det_imposto_icms_vicmsstret = fields.Float( string='Valor ICMS ST Ret' )
    det_imposto_icms_vicmssubstituto = fields.Float( string='Valor ICMS ST Sub' )
    det_imposto_icms_pcredsn = fields.Float( string='% ICMS SN', readonly=True )
    det_imposto_icms_vcredicmssn = fields.Float( string='Valor ICMS SN' )
    det_imposto_ipi_vbc = fields.Float( string='BC IPI', readonly=True )
    det_imposto_ipi_pipi = fields.Float( string='% IPI', readonly=True )
    det_imposto_ipi_vipi = fields.Float( string='Valor IPI', readonly=True )
    det_imposto_cofins_vbc = fields.Float( string='BC COFINS', readonly=True )
    det_imposto_cofins_pcofins = fields.Float( string='% COFINS', readonly=True )
    det_imposto_cofins_vcofins = fields.Float( string='Valor COFINS', readonly=True )
    det_imposto_pis_vbc = fields.Float( string='BC PIS', readonly=True )
    det_imposto_pis_ppis = fields.Float( string='% PIS', readonly=True )
    det_imposto_pis_vpis = fields.Float( string='Valor PIS', readonly=True )
    det_imposto_icms_cst = fields.Char( string='CST ICMS', readonly=True )
    det_imposto_icms_orig = fields.Char( string='Cód. Origem ', readonly=True )
    det_imposto_ipi_cst = fields.Char( string='CST IPI', readonly=True )
    det_imposto_pis_cst = fields.Char( string='CST PIS', readonly=True )
    det_imposto_cofins_cst = fields.Char( string='CST COFINS', readonly=True )

class AccountMoveReversal(models.TransientModel):
    
    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({
            'l10n_br_tipo_pedido': False,
            'l10n_br_tipo_pedido_entrada': 'devolucao'
        })
        #_logger.info(res)
        return res

class L10nBrInutilizarNF(models.Model):
    _name = 'l10n_br_ciel_it_account.inutilizar.nfe'
    _description = 'Inutilizar NF-e'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Número',required=True, readonly=True, copy=False, default='/')
    state = fields.Selection([('rascunho', 'Rascunho'),('autorizado', 'Autorizado'),('excecao_autorizado', 'Exceção (Falha)')], string='Status', readonly=True, copy=False, track_visibility='onchange', default='rascunho')
    serie = fields.Char(string='Série da Nota Fiscal', copy=False)
    numero_inicial = fields.Integer(string='Numero Inicial', copy=False)
    numero_final = fields.Integer(string='Numero Final', copy=False)
    motivo = fields.Text(string="Motivo", required=True)
    cstat = fields.Integer(string='cStat', readonly=True, copy=False)
    protocolo = fields.Char(string='Protocolo', readonly=True, copy=False)
    situacao = fields.Char(string='Situação da Nota Fiscal', readonly=True, copy=False)

    def action_inutilizar_nfe(self):
        """
        Inutilizar Faixa NF-e
        """

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/", "").replace("-", "").replace(".", "")
            else:
                return ""

        def _format_datetime_ano(date):
            return datetime.strftime(date, '%Y')[-2::]

        if self.name == '/':
            self.write({'name': self.env.ref("l10n_br_ciel_it_account.sequence_inutilizar_nfe").next_by_id(sequence_date=fields.Date.context_today(self))})

        l10n_br_documento_id = self.env["l10n_br_ciel_it_account.tipo.documento"].search([('l10n_br_modelo','=','55')],limit=1)

        nfetx2 = "Grupo=%s&CNPJ=%s&Ano=%s&Serie=%s&NFIni=%s&NFFin=%s&Justificativa=%s" % (
            l10n_br_documento_id.l10n_br_grupo,
            _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
            _format_datetime_ano(self.create_date),
            self.serie,
            self.numero_inicial,
            self.numero_final,
            self.motivo
        )

        url = "%s/ManagerAPIWeb/nfe/inutiliza" % (
            l10n_br_documento_id.l10n_br_url,
        )

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
        }

        basic_auth = HTTPBasicAuth(
            l10n_br_documento_id.l10n_br_usuario,
            l10n_br_documento_id.l10n_br_senha,
        )

        def _format_message(message):
            return "<p>Ação:</p><ul><li>Inutilizar NFe</li></ul><p>Retorno:</p><ul><li>%s</li></ul>" % str(message)

        try:

            response = requests.post(url, auth=basic_auth, headers=headers, data=nfetx2.encode('utf-8'))

            self.message_post(body=_format_message(response.text))
            response_values = response.text.split(",")
            if response_values[1] == "102":
                self.update({
                    'state': 'autorizado',
                    'protocolo': response_values[0],
                    'cstat': response_values[1],
                    'situacao': response_values[2],
                })
                self.env.cr.commit()

            else:
                self.update({
                    'state': 'excecao_autorizado',
                    'cstat': response_values[1],
                    'situacao': response_values[2]
                })
                self.env.cr.commit()

        except Exception as e:
            self.message_post(body=_format_message(e))
            raise UserError(_format_message(e))

class AccountPaymentBoleto(models.TransientModel):

    _name = 'l10n_br_ciel_it_account.pagamento.boleto'
    _description = 'Registrar Pagamento'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_valor = fields.Float( string='Valor Principal', required=True )
    l10n_br_juros = fields.Float( string='Valor Multa/Juros' )
    l10n_br_total = fields.Float( string='Total Recebido', compute='_l10n_br_total', readonly=True )
    
    @api.depends('l10n_br_valor', 'l10n_br_juros')
    def _l10n_br_total(self):
        for item in self:
            item.l10n_br_total = item.l10n_br_valor + item.l10n_br_juros
    
    def registrar_pagamento(self):

        move_line_id = self.env["account.move.line"].browse(self._context.get("active_id"))
        invoice = move_line_id.move_id

        l10n_br_cobranca_id = invoice.payment_acquirer_id.l10n_br_cobranca_id if invoice.payment_acquirer_id else invoice.invoice_payment_term_id.l10n_br_cobranca_id
        if not l10n_br_cobranca_id:
            return

        payment_values = self.env['account.payment'].with_context(active_ids=invoice.id, active_model='account.move', active_id=invoice.id).default_get({})
        payment_values["journal_id"] = l10n_br_cobranca_id.journal_id.id
        payment_values["payment_method_id"] = l10n_br_cobranca_id.journal_id.inbound_payment_method_ids[0].id
        amount = self.l10n_br_total
        if payment_values.get("amount") and amount > payment_values["amount"]:
            payment_values["payment_difference_handling"] = 'reconcile'
            payment_values["writeoff_account_id"] = l10n_br_cobranca_id.journal_id.writeoff_account_id.id
        payment_values["amount"] = amount
        self.env['account.payment'].create(payment_values).post()

        data_to_update = {}
        data_to_update["l10n_br_paga"] = True
        move_line_id.write(data_to_update)

        return

