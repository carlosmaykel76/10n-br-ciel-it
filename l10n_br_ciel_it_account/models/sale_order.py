# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
import uuid
from odoo.addons.l10n_br_ciel_it_account.models.account_payment_term import *

import logging
_logger = logging.getLogger(__name__)

INDICADOR_IE = [
    ('1', 'Contribuinte ICMS'),
    ('2', 'Contribuinte isento de Inscrição no cadastro de Contribuintes do ICMS'),
    ('9', 'Não Contribuinte'),
]

TIPO_OPERACAO = [
    ('saida','Saída'),
    ('entrada','Entrada'),
]

TIPO_PEDIDO_SAIDA = [
    ('venda','Saída: Venda'),
    ('servico','Saída: Venda de Serviço'),
    ('venda-conta-ordem','Saída: Venda por Conta e Ordem'),
    ('venda_futura','Saída: Venda p/ Entrega Futura'),
    ('venda-consignacao','Saída: Venda em Consignação'),
    ('amostra','Saída: Remessa p/ Amostra Grátis'),
    ('rem-conta-ordem','Saída: Remessa por Conta e Ordem'),
    ('bonificacao','Saída: Remessa p/ Bonificação'),
    ('conserto','Saída: Remessa p/ Conserto'),
    ('demonstracao','Saída: Remessa p/ Demonstração'),
    ('deposito','Saída: Remessa p/ Depósito'),
    ('troca','Saída: Remessa p/ Troca'),
    ('feira','Saída: Remessa p/ Feira'),
    ('exportacao','Saída: Remessa p/ Exportação'),
    ('comodato','Saída: Remessa em Comodato'),
    ('garantia','Saída: Remessa em Garantia'),
    ('consignacao','Saída: Remessa em Consignação'),
    ('locacao','Saída: Remessa para Locação'),
    ('compra','Saída: Devolução de Compra'),
    ('dev-conserto','Saída: Devolução de Conserto'),
    ('dev-consignacao','Saída: Devolução de Consignação'),
    ('dev-locacao','Saída: Devolução de Locação'),
    ('dev-demonstracao','Saída: Devolução de Demonstração'),
    ('industrializacao','Saída: Remessa p/ Industrialização'),
    ('outro','Saída: Outros'),
]

TIPO_PEDIDO_SAIDA_NO_PAYMENT = [
    'amostra',
    'rem-conta-ordem',
    'bonificacao',
    'conserto',
    'demonstracao',
    'deposito',
    'feira',
    'comodato',
    'garantia',
    'consignacao',
    'locacao',
    'dev-conserto',
    'dev-consignacao',
    'dev-locacao',
    'dev-demonstracao',
    'industrializacao',
]

TIPO_PEDIDO_SAIDA_CONSIGNADO = [
    'consignacao'
]

TIPO_PRODUTO = [
    ('comprado','Comprado'),
    ('produzido','Produzido'),
    ('servico','Serviço'),
]

TIPO_CLIENTE = [
    ('pf','Pessoa Física'),
    ('pj','Pessoa Jurídica'),
    ('ex','Exterior'),
    ('zf','Zona Franca'),
]

TIPO_DESTINACAO = [
    ('uso','Uso e Consumo'),
    ('ind','Industrialização'),
    ('com','Comercialização'),
]

OPERACAO_ICMSST = [
    ('ncmuf','UF de Destino e NCM incidem ICMSST'),
    ('cst_st','CST Entrada com ST'),
]

VERSAO_NFE = [
    ('4.00','NFE 4.00'),
]

FORMATO_IMPRESSAO_NFE = [
    ('0','Sem geração de DANFE'),
    ('1','DANFE normal, Retrato'),
    ('2','DANFE normal, Paisagem'),
    ('3','DANFE Simplificado'),
]

AMBIENTE_NFE = [
    ('1','Produção'),
    ('2','Homologação'),
]

TIPO_EMISSAO_NFE = [
    ('1','Emissão normal (não em contingência)'),
    ('2','Contingência FS-IA, com impressão do DANFE em formulário de segurança'),
    ('3','Contingência SCAN (Sistema de Contingência do Ambiente Nacional)'),
    ('4','Contingência DPEC (Declaração Prévia da Emissão em Contingência)'),
    ('5','Contingência FS-DA, com impressão do DANFE em formulário de segurança'),
    ('6','Contingência SVC-AN (SEFAZ Virtual de Contingência do AN)'),
    ('7','Contingência SVC-RS (SEFAZ Virtual de Contingência do RS)'),
]

FINALIDADE_NFE = [
    ('1','1 - NF-e Normal'),
    ('2','2 - NF-e Complementar'),
    ('3','3 - NF-e de Ajuste'),
    ('4','4 - Devolução de Mercadoria'),
]

INDICADOR_PRESENCA = [
    ('0','0 - Não se aplica'),
    ('1','1 - Operação presencial'),
    ('2','2 - Operação não presencial, pela internet'),
    ('3','3 - Operação não presencial, teleatendimento'),
    ('4','4 - NFC-e em operação com entrega a domicílio'),
    ('9','9 - Operação não presencial, outros'),
]

OPERACAO_CONSUMIDOR = [
    ('0', '0 - Normal'),
    ('1', '1 - Consumidor Final'),
]

LOCAL_DESTINO_OPERACAO = [
    ('1', '1 - Operação interna'),
    ('2', '2 - Opeação interestadual'),
    ('3', '3 - Operação com exterior'),
]

MODALIDADE_ICMS = [
    ('0', '0 - Margem Valor Agregado (%)'),
    ('1', '1 - Pauta (Valor)'),
    ('2', '2 - Preço Tabelado Máx. (valor)'),
    ('3', '3 - Valor da operação'),
]

MOTIVO_ICMS_DESONERACAO = [
    ('3' , '03 - Uso na agropecuária'),
    ('9' , '09 - Outros'),
    ('12', '12 - Órgão de fomento e desenvolvimento agropecário'),
]

MODALIDADE_ICMSST = [
    ('0', '0 - Preço tabelado ou máximo sugerido'),
    ('1', '1 - Lista Negativa (valor)'),
    ('2', '2 - Lista Positiva (valor)'),
    ('3', '3 - Lista Neutra (valor)'),
    ('4', '4 - Margem Valor Agregado (%)'),
    ('5', '5 - Pauta (valor)'),
]

ICMS_CST = [
    ('00' , '00 - Tributada integralmente'),
    ('10' , '10 - Tributada e com cobrança do ICMS-ST'),
    ('20' , '20 - Com redução de base de cálculo'),
    ('30' , '30 - Isenta ou não tributada e com cobrança do ICMS-ST'),
    ('40' , '40 - Isenta'),
    ('41' , '41 - Não tributada'),
    ('50' , '50 - Suspensão'),
    ('51' , '51 - Diferimento'),
    ('60' , '60 - ICMS cobrado anteriormente por ST'),
    ('70' , '70 - Com redução de base de cálculo e cobrança do ICMS-ST'),
    ('90' , '90 - Outras'),
    ('101', '101 - Tributada pelo Simples Nacional com permissão de crédito'),
    ('102', '102 - Tributada pelo Simples Nacional sem permissão de crédito'),
    ('103', '103 - Isenção do ICMS no Simples Nacional para faixa de receita bruta'),
    ('201', '201 - Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por substituição tributária'),
    ('202', '202 - Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por substituição tributária'),
    ('203', '203 - Isenção do ICMS no Simples Nacional para faixa de receita bruta e com cobrança do ICMS por substituição tributária'),
    ('300', '300 - Imune'),
    ('400', '400 - Não tributada pelo Simples Nacional'),
    ('500', '500 - ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação'),
    ('900', '900 - Outros'),
]

IPI_CST = [
    ('00', '00 - Entrada com Recuperação de Crédito'),
    ('01', '01 - Entrada Tributável com Alíquota Zero'),
    ('02', '02 - Entrada Isenta'),
    ('03', '03 - Entrada Não-Tributada'),
    ('04', '04 - Entrada Imune'),
    ('05', '05 - Entrada com Suspensão'),
    ('49', '49 - Outras Entradas'),
    ('50', '50 - Saída Tributada'),
    ('51', '51 - Saída Tributável com Alíquota Zero'),
    ('52', '52 - Saída Isenta'),
    ('53', '53 - Saída Não-Tributada'),
    ('54', '54 - Saída Imune'),
    ('55', '55 - Saída com Suspensão'),
    ('99', '99 - Outras Saídas'),
]

IPI_CST_ENTRADA = {
    '50': '00',
    '51': '01',
    '52': '02',
    '53': '03',
    '54': '04',
    '55': '05',
    '99': '49',
}

PIS_CST = [
    ('01', '01 - Operação Tributável com Alíquota Básica'),
    ('02', '02 - Operação Tributável com Alíquota por Unidade de Medida de Produto'),
    ('03', '03 - Operação Tributável com Alíquota por Unidade de Medida de Produto'),
    ('04', '04 - Operação Tributável Monofásica – Revenda a Alíquota Zero'),
    ('05', '05 - Operação Tributável por Substituição Tributária'),
    ('06', '06 - Operação Tributável a Alíquota Zero'),
    ('07', '07 - Operação Isenta da Contribuição'),
    ('08', '08 - Operação sem Incidência da Contribuição'),
    ('09', '09 - Operação com Suspensão da Contribuição'),
    ('49', '49 - Outras Operações de Saída'),
    ('50', '50 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
    ('51', '51 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno'),
    ('52', '52 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita de Exportação'),
    ('53', '53 - Operação com Direito a Crédito – Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
    ('54', '54 - Operação com Direito a Crédito – Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
    ('55', '55 - Operação com Direito a Crédito – Vinculada a Receitas Não Tributadas Mercado Interno e de Exportação'),
    ('56', '56 - Oper. c/ Direito a Créd. Vinculada a Rec. Tributadas e Não-Tributadas Mercado Interno e de Exportação'),
    ('60', '60 - Crédito Presumido – Oper. de Aquisição Vinculada Exclusivamente a Rec. Tributada no Mercado Interno'),
    ('61', '61 - Créd. Presumido – Oper. de Aquisição Vinculada Exclusivamente a Rec. Não-Tributada Mercado Interno'),
    ('62', '62 - Crédito Presumido – Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),
    ('63', '63 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec.Tributadas e Não-Tributadas no Mercado Interno'),
    ('64', '64 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Tributadas no Mercado Interno e de Exportação'),
    ('65', '65 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Não-Tributadas Mercado Interno e Exportação'),
    ('66', '66 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Trib. e Não-Trib. Mercado Interno e Exportação'),
    ('67', '67 - Crédito Presumido – Outras Operações'),
    ('70', '70 - Operação de Aquisição sem Direito a Crédito'),
    ('71', '71 - Operação de Aquisição com Isenção'),
    ('72', '72 - Operação de Aquisição com Suspensão'),
    ('73', '73 - Operação de Aquisição a Alíquota Zero'),
    ('74', '74 - Operação de Aquisição sem Incidência da Contribuição'),
    ('75', '75 - Operação de Aquisição por Substituição Tributária'),
    ('98', '98 - Outras Operações de Entrada'),
    ('99', '99 - Outras Operações'),
]

COFINS_CST = [
    ('01', '01 - Operação Tributável com Alíquota Básica'),
    ('02', '02 - Operação Tributável com Alíquota por Unidade de Medida de Produto'),
    ('03', '03 - Operação Tributável com Alíquota por Unidade de Medida de Produto'),
    ('04', '04 - Operação Tributável Monofásica – Revenda a Alíquota Zero'),
    ('05', '05 - Operação Tributável por Substituição Tributária'),
    ('06', '06 - Operação Tributável a Alíquota Zero'),
    ('07', '07 - Operação Isenta da Contribuição'),
    ('08', '08 - Operação sem Incidência da Contribuição'),
    ('09', '09 - Operação com Suspensão da Contribuição'),
    ('49', '49 - Outras Operações de Saída'),
    ('50', '50 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita Tributada no Mercado Interno'),
    ('51', '51 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita Não-Tributada no Mercado Interno'),
    ('52', '52 - Operação com Direito a Crédito – Vinculada Exclusivamente a Receita de Exportação'),
    ('53', '53 - Operação com Direito a Crédito – Vinculada a Receitas Tributadas e Não-Tributadas no Mercado Interno'),
    ('54', '54 - Operação com Direito a Crédito – Vinculada a Receitas Tributadas no Mercado Interno e de Exportação'),
    ('55', '55 - Operação com Direito a Crédito – Vinculada a Receitas Não Tributadas Mercado Interno e de Exportação'),
    ('56', '56 - Oper. c/ Direito a Créd. Vinculada a Rec. Tributadas e Não-Tributadas Mercado Interno e de Exportação'),
    ('60', '60 - Crédito Presumido – Oper. de Aquisição Vinculada Exclusivamente a Rec. Tributada no Mercado Interno'),
    ('61', '61 - Créd. Presumido – Oper. de Aquisição Vinculada Exclusivamente a Rec. Não-Tributada Mercado Interno'),
    ('62', '62 - Crédito Presumido – Operação de Aquisição Vinculada Exclusivamente a Receita de Exportação'),
    ('63', '63 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec.Tributadas e Não-Tributadas no Mercado Interno'),
    ('64', '64 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Tributadas no Mercado Interno e de Exportação'),
    ('65', '65 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Não-Tributadas Mercado Interno e Exportação'),
    ('66', '66 - Créd. Presumido – Oper. de Aquisição Vinculada a Rec. Trib. e Não-Trib. Mercado Interno e Exportação'),
    ('67', '67 - Crédito Presumido – Outras Operações'),
    ('70', '70 - Operação de Aquisição sem Direito a Crédito'),
    ('71', '71 - Operação de Aquisição com Isenção'),
    ('72', '72 - Operação de Aquisição com Suspensão'),
    ('73', '73 - Operação de Aquisição a Alíquota Zero'),
    ('74', '74 - Operação de Aquisição sem Incidência da Contribuição'),
    ('75', '75 - Operação de Aquisição por Substituição Tributária'),
    ('98', '98 - Outras Operações de Entrada'),
    ('99', '99 - Outras Operações'),
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_contact_id = fields.Many2one(
        'res.partner', string='Contato', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)

    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', compute="_get_l10n_br_operacao_id", check_company=True )
    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_SAIDA, string='Tipo de Pedido', default='venda', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_operacao_consumidor = fields.Selection( OPERACAO_CONSUMIDOR, string='Operação Consumidor Final', default='0', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_indicador_presenca = fields.Selection( INDICADOR_PRESENCA, string='Indicador Presença', default='0', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )
    payment_term_id = fields.Many2one( readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    payment_acquirer_id = fields.Many2one( 'payment.acquirer', string='Forma de Pagamento', readonly=True, states={'draft': [('readonly', False)]}, domain=[('state', '=', 'enabled')] )
    incoterm = fields.Many2one( string='Tipo de Frete', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_pedido_compra = fields.Char( string='Pedido de Compra do Cliente', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    l10n_br_item_pedido_compra = fields.Char( string='Item Pedido de Compra do Cliente', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )

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

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        for order in self.filtered(lambda order: order.partner_contact_id and order.partner_contact_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_contact_id.id])

        return res

    def action_quotation_sent(self):
        res = super(SaleOrder, self).action_quotation_sent()

        for order in self.filtered(lambda order: order.partner_contact_id and order.partner_contact_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_contact_id.id])

        return res

    @api.onchange('partner_id')
    def onchange_l10n_br_partner_id(self):
        for item in self:
            if item.partner_id:
                item.l10n_br_compra_indcom = item.partner_id.l10n_br_compra_indcom
                item.carrier_id = item.partner_id.property_delivery_carrier_id.id
                item.partner_contact_id = item.partner_id.child_ids[0].id if len(item.partner_id.child_ids) > 0 else item.partner_id.id
            else:
                item.partner_contact_id = False

    def _get_l10n_br_operacao_id(self):
        for record in self:
            order_line = record.order_line.filtered(lambda l: not l.display_type)
            record.l10n_br_operacao_id = order_line[0].l10n_br_operacao_id if len(order_line) > 0 else False

    @api.onchange('l10n_br_calcular_imposto')
    def onchange_l10n_br_calcular_imposto(self):
        for item in self:
            item._do_rateio_frete()
            order_line = item.order_line.filtered(lambda l: not l.display_type)
            for line in order_line:
                line._do_calculate_l10n_br_impostos()
            item._do_calculate_l10n_br_impostos()

    def _do_rateio_frete(self):

        self.ensure_one()

        order_line = self.order_line.filtered(lambda l: not l.display_type)
        for line in order_line:
            values_to_update = {}
            values_to_update['l10n_br_frete'] = 0.00
            values_to_update['l10n_br_seguro'] = 0.00
            values_to_update['l10n_br_despesas_acessorias'] = 0.00

            line.update(values_to_update)

        l10n_br_frete_saldo = l10n_br_frete = self.l10n_br_frete
        l10n_br_seguro_saldo = l10n_br_seguro = self.l10n_br_seguro
        l10n_br_despesas_acessorias_saldo = l10n_br_despesas_acessorias = self.l10n_br_despesas_acessorias
        
        for idx, line in enumerate(order_line):
            values_to_update = {}

            fator = (line.l10n_br_prod_valor - line.l10n_br_desc_valor) / ((self.l10n_br_prod_valor - self.l10n_br_desc_valor) or 1.00)

            values_to_update['l10n_br_frete'] = round(l10n_br_frete * fator,2)
            values_to_update['l10n_br_seguro'] = round(l10n_br_seguro * fator,2)
            values_to_update['l10n_br_despesas_acessorias'] = round(l10n_br_despesas_acessorias * fator,2)

            l10n_br_frete_saldo -= values_to_update['l10n_br_frete']
            l10n_br_seguro_saldo -= values_to_update['l10n_br_seguro']
            l10n_br_despesas_acessorias_saldo -= values_to_update['l10n_br_despesas_acessorias']

            if idx == len(order_line)-1:
                values_to_update['l10n_br_frete'] += l10n_br_frete_saldo
                values_to_update['l10n_br_seguro'] += l10n_br_seguro_saldo
                values_to_update['l10n_br_despesas_acessorias'] += l10n_br_despesas_acessorias_saldo

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
        order_line = self.order_line.filtered(lambda l: not l.display_type)
        for line in order_line:
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
        l10n_br_informacao_fiscal = l10n_br_informacao_fiscal.replace('%%l10n_br_pedido_compra%%',"Pedido de Compra: " + self.l10n_br_pedido_compra + "." if self.l10n_br_pedido_compra else "")

        # Simples Nacional
        if self.company_id.l10n_br_regime_tributario != '3':
            l10n_br_icms_credito_valor = sum(self.order_line.mapped('l10n_br_icms_credito_valor'))
            l10n_br_icms_credito_aliquota = 0.00
            if self.order_line:
                l10n_br_icms_credito_aliquota = max(self.order_line.mapped('l10n_br_icms_credito_aliquota'))
            if l10n_br_icms_credito_valor > 0.00 and l10n_br_icms_credito_aliquota > 0.00:
                l10n_br_informacao_fiscal += (" " if l10n_br_informacao_fiscal else "") + "PERMITE O APROVEITAMENTO DO CRÉDITO DE ICMS NO VALOR DE (R$ {0}) CORRESPONDENTE À ALIQUOTA DE ({1}%), NOS TERMOS DO ART 23, DA LEI COMPLEMENTAR Nº 123 DE 2006.".format( _format_decimal_2(l10n_br_icms_credito_valor), _format_decimal_2(l10n_br_icms_credito_aliquota) )
            else:
                l10n_br_informacao_fiscal += (" " if l10n_br_informacao_fiscal else "") + "DOCUMENTO EMITIDO POR ME OU EPP OPTANTE PELO SIMPLES NACIONAL NÃO GERA CRÉDITO FISCAL DE ICMS/IPI, NOS TERMOS DO ART 23, DA LEI COMPLEMENTAR Nº 123 DE 2006."

        l10n_br_informacao_fiscal = self._get_l10n_br_informacao_fiscal(l10n_br_informacao_fiscal)

        values_to_update['l10n_br_informacao_fiscal'] = l10n_br_informacao_fiscal

        self.update(values_to_update)

    @api.onchange('order_line','l10n_br_tipo_pedido','l10n_br_operacao_consumidor','partner_id','company_id','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias')
    def onchange_l10n_br_imposto(self):
        for item in self:
            if item.l10n_br_imposto_auto:
                item.l10n_br_calcular_imposto = not item.l10n_br_calcular_imposto

    @api.depends('order_line.l10n_br_icms_base','order_line.l10n_br_icms_valor','order_line.l10n_br_icmsst_base','order_line.l10n_br_icmsst_valor',
        'order_line.l10n_br_prod_valor','order_line.l10n_br_desc_valor','order_line.l10n_br_ipi_valor','order_line.l10n_br_pis_valor',
        'order_line.l10n_br_cofins_valor','order_line.l10n_br_total_nfe','order_line.l10n_br_total_tributos','order_line.l10n_br_icms_dest_valor',
        'order_line.l10n_br_icms_remet_valor','order_line.l10n_br_fcp_dest_valor','order_line.l10n_br_fcp_st_valor','order_line.l10n_br_fcp_st_ant_valor',
        'order_line.l10n_br_icms_valor_isento','order_line.l10n_br_icms_valor_outros','order_line.l10n_br_icms_valor_desonerado','order_line.l10n_br_ipi_valor_isento','order_line.l10n_br_ipi_valor_outros',
        'order_line.l10n_br_pis_valor_isento','order_line.l10n_br_pis_valor_outros','order_line.l10n_br_cofins_valor_isento','order_line.l10n_br_cofins_valor_outros'
        ,'order_line.l10n_br_iss_valor','order_line.l10n_br_irpj_valor','order_line.l10n_br_csll_valor','order_line.l10n_br_irpj_ret_valor','order_line.l10n_br_inss_ret_valor','order_line.l10n_br_iss_ret_valor','order_line.l10n_br_csll_ret_valor'
        ,'order_line.l10n_br_pis_ret_valor','order_line.l10n_br_cofins_ret_valor' )
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
            l10n_br_iss_valor = sum(order.order_line.mapped('l10n_br_iss_valor'))
            l10n_br_irpj_valor = sum(order.order_line.mapped('l10n_br_irpj_valor'))
            l10n_br_csll_valor = sum(order.order_line.mapped('l10n_br_csll_valor'))
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

    def _create_invoices(self, grouped=False, final=False):

        moves = super(SaleOrder, self)._create_invoices(grouped, final)

        if self.company_id.country_id != self.env.ref('base.br'):
            return moves

        for move in moves:
            move.with_context(check_move_validity=False,check_rateio_frete=False).onchange_l10n_br_calcular_imposto()

    def _prepare_invoice(self):

        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        if self.company_id.country_id != self.env.ref('base.br'):
            return invoice_vals

        if self.l10n_br_tipo_pedido in TIPO_PEDIDO_SAIDA_NO_PAYMENT:
            company_id = self._context.get('force_company', self._context.get('default_company_id', self.env.company.id))
            domain = [('company_id', '=', company_id), ('type', '=', 'sale'), ('l10n_br_no_payment', '=', True), ('l10n_br_tipo_pedido_entrada', '=', False), ('l10n_br_tipo_pedido', '=', self.l10n_br_tipo_pedido)]
            journal = self.env['account.journal'].search(domain, limit=1)
            invoice_vals['journal_id'] = journal.id
            if journal.fiscal_position_id:
                invoice_vals['fiscal_position_id'] = journal.fiscal_position_id.id

        if self.partner_contact_id:
            invoice_vals['partner_contact_id'] = self.partner_contact_id.id


        invoice_vals['l10n_br_tipo_pedido'] = self.l10n_br_tipo_pedido
        invoice_vals['l10n_br_operacao_consumidor'] = self.l10n_br_operacao_consumidor
        invoice_vals['l10n_br_indicador_presenca'] = self.l10n_br_indicador_presenca
        
        invoice_vals['l10n_br_compra_indcom'] = self.l10n_br_compra_indcom
        if self.payment_acquirer_id:
            invoice_vals['payment_acquirer_id'] = self.payment_acquirer_id.id

        invoice_vals['l10n_br_informacao_fiscal'] = self.l10n_br_informacao_fiscal
        invoice_vals['l10n_br_informacao_complementar'] = self.l10n_br_informacao_complementar

        if self.l10n_br_cfop_id:
            invoice_vals['l10n_br_cfop_id'] = self.l10n_br_cfop_id.id

        invoice_vals['l10n_br_pedido_compra'] = self.l10n_br_pedido_compra
        invoice_vals['l10n_br_item_pedido_compra'] = self.l10n_br_item_pedido_compra

        invoice_vals['l10n_br_imposto_auto'] = self.l10n_br_imposto_auto
        invoice_vals['l10n_br_calcular_imposto'] = self.l10n_br_calcular_imposto

        invoice_vals['l10n_br_frete'] = self.l10n_br_frete
        invoice_vals['l10n_br_seguro'] = self.l10n_br_seguro
        invoice_vals['l10n_br_despesas_acessorias'] = self.l10n_br_despesas_acessorias

        stock_picking_id = self.env['stock.picking'].search([('origin','=',self.name),('state','=','done')], order='date_done desc', limit=1)
        if stock_picking_id:
            invoice_vals['l10n_br_carrier_id'] = stock_picking_id.carrier_id
            invoice_vals['l10n_br_peso_liquido'] = stock_picking_id.l10n_br_peso_liquido
            invoice_vals['l10n_br_peso_bruto'] = stock_picking_id.l10n_br_peso_bruto
            invoice_vals['l10n_br_volumes'] = stock_picking_id.l10n_br_volumes
            invoice_vals['l10n_br_especie'] = stock_picking_id.l10n_br_especie
            invoice_vals['l10n_br_veiculo_placa'] = stock_picking_id.l10n_br_veiculo_placa
            invoice_vals['l10n_br_veiculo_uf'] = stock_picking_id.l10n_br_veiculo_uf
            invoice_vals['l10n_br_veiculo_rntc'] = stock_picking_id.l10n_br_veiculo_rntc

        return invoice_vals

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    l10n_br_operacao_id = fields.Many2one( 'l10n_br_ciel_it_account.operacao', string='Operação', domain = [('l10n_br_tipo_operacao','=','saida')], check_company=True )
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
    l10n_br_pedido_compra = fields.Char( string='Pedido de Compra do Cliente', default=lambda self: self.order_id.l10n_br_pedido_compra )
    l10n_br_item_pedido_compra = fields.Char( string='Item Pedido de Compra do Cliente', default=lambda self: self.order_id.l10n_br_item_pedido_compra )
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

    l10n_br_icmsst_retido_base = fields.Float( string='Valor da Base de Cálculo do ICMSST Retido' )
    l10n_br_icmsst_retido_aliquota = fields.Float( string='Alíquota suportada pelo Consumidor Final (%)' )
    l10n_br_icmsst_substituto_valor = fields.Float( string='Valor do ICMS próprio do Substituto' )
    l10n_br_icmsst_retido_valor = fields.Float( string='Valor do ICMSST Retido' )

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

    qty_available = fields.Float( related='product_id.qty_available' )
    virtual_available = fields.Float( related='product_id.virtual_available' )
    
    def _get_tax_company_id(self):
        return self.order_id.company_id

    def _get_protected_fields(self):
        
        protected_fields = super(SaleOrderLine, self)._get_protected_fields()
        protected_fields.extend([
                'l10n_br_operacao_id','l10n_br_cfop_id','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias','l10n_br_desc_valor'
                ,'l10n_br_prod_valor','l10n_br_total_nfe','l10n_br_total_tributos','l10n_br_informacao_adicional','l10n_br_pedido_compra','l10n_br_item_pedido_compra'
                ,'l10n_br_compra_indcom','l10n_br_mensagem_fiscal_ids','l10n_br_icms_modalidade_base','l10n_br_icms_reducao_base'
                ,'l10n_br_icms_diferido_valor_operacao','l10n_br_icms_diferido_aliquota','l10n_br_icms_diferido_valor','l10n_br_icms_cst'
                ,'l10n_br_icms_base','l10n_br_icms_aliquota','l10n_br_icms_valor','l10n_br_icms_valor_isento','l10n_br_icms_valor_outros'
                ,'l10n_br_icms_valor_desonerado','l10n_br_icms_motivo_desonerado','l10n_br_icms_dest_base','l10n_br_icms_dest_aliquota','l10n_br_icms_inter_aliquota'
                ,'l10n_br_icms_inter_participacao','l10n_br_icms_dest_valor','l10n_br_icms_remet_valor','l10n_br_icms_credito_aliquota','l10n_br_icms_credito_valor'
                ,'l10n_br_codigo_beneficio','l10n_br_fcp_base','l10n_br_fcp_dest_aliquota','l10n_br_fcp_dest_valor','l10n_br_fcp_st_base','l10n_br_fcp_st_aliquota'
                ,'l10n_br_fcp_st_valor','l10n_br_fcp_st_ant_base','l10n_br_fcp_st_ant_aliquota','l10n_br_fcp_st_ant_valor','l10n_br_icmsst_modalidade_base','l10n_br_icmsst_reducao_base'
                ,'l10n_br_icmsst_mva','l10n_br_icmsst_base','l10n_br_icmsst_aliquota','l10n_br_icmsst_valor','l10n_br_icmsst_retido_base','l10n_br_icmsst_retido_aliquota'
                ,'l10n_br_icmsst_substituto_valor','l10n_br_icmsst_retido_valor','l10n_br_icmsst_base_propria_aliquota','l10n_br_icmsst_uf','l10n_br_ipi_cst'
                ,'l10n_br_ipi_base','l10n_br_ipi_aliquota','l10n_br_ipi_valor','l10n_br_ipi_valor_isento','l10n_br_ipi_valor_outros','l10n_br_ipi_cnpj','l10n_br_ipi_selo_codigo'
                ,'l10n_br_ipi_selo_quantidade','l10n_br_ipi_enq','l10n_br_pis_cst','l10n_br_pis_base','l10n_br_pis_aliquota','l10n_br_pis_valor','l10n_br_pis_valor_isento'
                ,'l10n_br_pis_valor_outros','l10n_br_cofins_cst','l10n_br_cofins_base','l10n_br_cofins_aliquota','l10n_br_cofins_valor','l10n_br_cofins_valor_isento','l10n_br_cofins_valor_outros'
                ,'l10n_br_iss_valor','l10n_br_irpj_valor','l10n_br_csll_valor','l10n_br_csll_ret_valor','l10n_br_irpj_ret_valor','l10n_br_inss_ret_valor','l10n_br_iss_ret_valor','l10n_br_pis_ret_valor','l10n_br_cofins_ret_valor'
        ])
        return protected_fields

    @api.model
    def _handle_taxes(self, name, tax_key, price_include, amount, fixed):

        type_tax_use = 'sale'
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

        for line in self:

            tax_key = False
            if line.tax_id:
                tax_key = line.tax_id[0].name[-9:-1]
            
            if not tax_key:
                tax_key = str(uuid.uuid4())[:8]
            
            line.update({'tax_id': [(5,)]})
                        
            tax_ids = []
            ## ICMS ##
            amount = line.l10n_br_icms_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS', tax_key, True, amount, True)
                tax_ids.append(tax_icms_id.id)

            amount = line.l10n_br_icms_valor_isento # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS ISENTO', tax_key, True, amount, True)
                tax_ids.append(tax_icms_id.id)

            amount = line.l10n_br_icms_valor_outros # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS OUTROS', tax_key, True, amount, True)
                tax_ids.append(tax_icms_id.id)

            amount = line.l10n_br_icms_valor_desonerado # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_icms_id = line._handle_taxes('ICMS DESONERADO', tax_key, True, amount, True)
                tax_ids.append(tax_icms_id.id)

            ## ICMSST ##
            amount = line.l10n_br_icmsst_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_icmsst_id = line._handle_taxes('ICMS ST', tax_key, False, amount, True)
                tax_ids.append(tax_icmsst_id.id)

            ## IPI ##
            amount = line.l10n_br_ipi_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI', tax_key, False, amount, True)
                tax_ids.append(tax_ipi_id.id)

            amount = line.l10n_br_ipi_valor_isento # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI ISENTO', tax_key, False, amount, True)
                tax_ids.append(tax_ipi_id.id)

            amount = line.l10n_br_ipi_valor_outros # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_ipi_id = line._handle_taxes('IPI OUTROS', tax_key, False, amount, True)
                tax_ids.append(tax_ipi_id.id)

            ## PIS ##
            amount = line.l10n_br_pis_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_pis_id = line._handle_taxes('PIS', tax_key, True, amount, True)
                tax_ids.append(tax_pis_id.id)

            amount = line.l10n_br_pis_valor_isento # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_pis_id = line._handle_taxes('PIS ISENTO', tax_key, True, amount, True)
                tax_ids.append(tax_pis_id.id)

            amount = line.l10n_br_pis_valor_outros # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_pis_id = line._handle_taxes('PIS OUTROS', tax_key, True, amount, True)
                tax_ids.append(tax_pis_id.id)

            ## COFINS ##
            amount = line.l10n_br_cofins_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_cofins_id = line._handle_taxes('COFINS', tax_key, True, amount, True)
                tax_ids.append(tax_cofins_id.id)

            amount = line.l10n_br_cofins_valor_isento # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_cofins_id = line._handle_taxes('COFINS ISENTO', tax_key, True, amount, True)
                tax_ids.append(tax_cofins_id.id)

            amount = line.l10n_br_cofins_valor_outros # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_cofins_id = line._handle_taxes('COFINS OUTROS', tax_key, True, amount, True)
                tax_ids.append(tax_cofins_id.id)

            ## ISS ##
            amount = line.l10n_br_iss_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_iss_id = line._handle_taxes('ISS', tax_key, True, amount, True)
                tax_ids.append(tax_iss_id.id)

            ## IRPJ ##
            amount = line.l10n_br_irpj_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_irpj_id = line._handle_taxes('IRPJ', tax_key, True, amount, True)
                tax_ids.append(tax_irpj_id.id)

            ## CSLL ##
            amount = line.l10n_br_csll_valor # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_csll_id = line._handle_taxes('CSLL', tax_key, True, amount, True)
                tax_ids.append(tax_csll_id.id)

            ## CSLL RET ##
            amount = line.l10n_br_csll_ret_aliquota
            if amount != 0.00:
                tax_csll_ret_id = line._handle_taxes('CSLL RET', tax_key, False, amount, False)
                tax_ids.append(tax_csll_ret_id.id)

            ## IRPJ RET ##
            amount = line.l10n_br_irpj_ret_aliquota
            if amount != 0.00:
                tax_irpj_ret_id = line._handle_taxes('IRPJ RET', tax_key, False, amount, False)
                tax_ids.append(tax_irpj_ret_id.id)

            ## INSS RET ##
            amount = line.l10n_br_inss_ret_aliquota
            if amount != 0.00:
                tax_inss_ret_id = line._handle_taxes('INSS RET', tax_key, False, amount, False)
                tax_ids.append(tax_inss_ret_id.id)

            ## ISS RET ##
            amount = line.l10n_br_iss_ret_aliquota
            if amount != 0.00:
                tax_iss_ret_id = line._handle_taxes('ISS RET', tax_key, False, amount, False)
                tax_ids.append(tax_iss_ret_id.id)

            ## PIS RET ##
            amount = line.l10n_br_pis_ret_aliquota
            if amount != 0.00:
                tax_pis_ret_id = line._handle_taxes('PIS RET', tax_key, False, amount, False)
                tax_ids.append(tax_pis_ret_id.id)

            ## COFINS RET ##
            amount = line.l10n_br_cofins_ret_aliquota
            if amount != 0.00:
                tax_cofins_ret_id = line._handle_taxes('COFINS RET', tax_key, False, amount, False)
                tax_ids.append(tax_cofins_ret_id.id)

            ## FRETE ##
            amount = line.l10n_br_frete # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_frete_id = line._handle_taxes('FRETE', tax_key, False, amount, True)
                tax_ids.append(tax_frete_id.id)

            ## SEGURO ##
            amount = line.l10n_br_seguro # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_seguro_id = line._handle_taxes('SEGURO', tax_key, False, amount, True)
                tax_ids.append(tax_seguro_id.id)

            ## DESPESAS ##
            amount = line.l10n_br_despesas_acessorias # / (line.product_uom_qty or 1.00)
            if amount != 0.00:
                tax_despesas_id = line._handle_taxes('DESPESAS', tax_key, False, amount, True)
                tax_ids.append(tax_despesas_id.id)

            if tax_ids:
                line.update({'tax_id': [(6, 0, tax_ids)]})
                
    @api.onchange('product_id')
    def l10n_br_onchange_product_id(self):
        if self.company_id.country_id == self.env.ref('base.br'):
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

            domain = [('l10n_br_tipo_operacao','=','saida'),('l10n_br_tipo_pedido','=',self.order_id.l10n_br_tipo_pedido)]

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
            if self._get_tax_company_id().country_id != self.order_id.partner_id.country_id:
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
            if self._get_tax_company_id().state_id == self.order_id.partner_id.state_id:
                l10n_br_destino_operacao = '1' # 1 - Operação interna
            elif self._get_tax_company_id().country_id != self.order_id.partner_id.country_id:
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

            ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
            ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.order_id.partner_id.id)],limit=1)
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
                if self._get_tax_company_id().state_id == self.order_id.partner_id.state_id:
                    values_to_update['l10n_br_cfop_id'] = self.l10n_br_operacao_id.l10n_br_intra_cfop_id.id
                elif self._get_tax_company_id().country_id != self.order_id.partner_id.country_id:
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
            if self._get_tax_company_id().l10n_br_regime_tributario == '3':
                values_to_update['l10n_br_icms_cst'] = '00'
                icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id)],limit=1)
                if icms_uf:
                    if self._get_tax_company_id().state_id != self.order_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
                        l10n_br_icms_aliquota = icms_uf.l10n_br_icms_ext_aliquota
                    else:
                        l10n_br_icms_aliquota = icms_uf.l10n_br_icms_aliquota
            else:
                values_to_update['l10n_br_icms_cst'] = '101'

            ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
            ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.order_id.partner_id.id)],limit=1)
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
                    icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id)],limit=1)
                    if icms_uf:
                        if self._get_tax_company_id().state_id != self.order_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
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
            if self.order_id.l10n_br_operacao_consumidor == '0' and \
            self.order_id.partner_id.l10n_br_indicador_ie != '9' and \
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
                    if self._get_tax_company_id().l10n_br_regime_tributario != '3':
                        l10n_br_icms_aliquota_sn = 0.00
                        icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id)],limit=1)
                        if icms_uf:
                            if self._get_tax_company_id().state_id != self.order_id.partner_id.state_id and self.product_id.l10n_br_origem in ['1','2','3','8']:
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
                values_to_update['l10n_br_icms_credito_aliquota'] = self._get_tax_company_id().l10n_br_icms_credito_aliquota
                values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self._get_tax_company_id().l10n_br_icms_credito_aliquota / 100.00,2)
        
            elif values_to_update['l10n_br_icms_cst'] == '102':
                pass

            elif values_to_update['l10n_br_icms_cst'] == '201':
                values_to_update['l10n_br_icms_credito_aliquota'] = self._get_tax_company_id().l10n_br_icms_credito_aliquota
                values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self._get_tax_company_id().l10n_br_icms_credito_aliquota / 100.00,2)

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
                values_to_update['l10n_br_icms_credito_aliquota'] = self._get_tax_company_id().l10n_br_icms_credito_aliquota
                values_to_update['l10n_br_icms_credito_valor'] = round(self.l10n_br_total_nfe * self._get_tax_company_id().l10n_br_icms_credito_aliquota / 100.00,2)

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
                self.order_id.l10n_br_operacao_consumidor == '1' and \
                self.order_id.partner_id.l10n_br_indicador_ie == '9':

                    l10n_br_icms_dest_aliquota = 0.00
                    icms_uf = self.env["l10n_br_ciel_it_account.icms.uf"].search([('state_de_id','=',self.order_id.partner_id.state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id)],limit=1)
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

            l10n_br_fcp_aliquota = self.order_id.partner_id.state_id.l10n_br_fcp_aliquota
            ncm_uf = self.env["l10n_br_ciel_it_account.ncm.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id)],limit=1)
            ncm_cliente_uf = self.env["l10n_br_ciel_it_account.ncm.cliente.uf"].search([('state_de_id','=',self._get_tax_company_id().state_id.id),('state_para_id','=',self.order_id.partner_id.state_id.id),('l10n_br_ncm_id','=',self.product_id.l10n_br_ncm_id.id),('partner_ids','in',self.order_id.partner_id.id)],limit=1)
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
            if self._get_tax_company_id().l10n_br_regime_tributario == '3':

                bIncideFCP = False
                # operação interna
                if self.l10n_br_cfop_id.l10n_br_destino_operacao == '1':
                    # operação é consumidor final e estado incide para consumidor final
                    if self._get_tax_company_id().l10n_br_fcp_interno_consumidor_final and \
                    self.order_id.l10n_br_operacao_consumidor == '1' and \
                    self.order_id.partner_id.l10n_br_indicador_ie == '9':
                        if self.l10n_br_icms_cst in ['00','10','20','51','70','90']:
                            bIncideFCP = True

                # operação interestadual
                if self.l10n_br_cfop_id.l10n_br_destino_operacao == '2' and \
                    self.order_id.l10n_br_operacao_consumidor == '1' and \
                    self.order_id.partner_id.l10n_br_indicador_ie == '9':
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
            if self._get_tax_company_id().l10n_br_regime_tributario == '3':
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
                if self._get_tax_company_id().l10n_br_exclui_icms_piscofins:
                    values_to_update['l10n_br_pis_base'] -= self.l10n_br_icms_valor
                values_to_update['l10n_br_pis_base'] = values_to_update['l10n_br_pis_base'] * (1.00 - (l10n_br_pis_reducao_base/100.00))

            values_to_update['l10n_br_pis_aliquota'] = 0.00
            if values_to_update['l10n_br_pis_cst'] == '01':
                # Lucro Presumido
                if self._get_tax_company_id().l10n_br_incidencia_cumulativa == '2':
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
            if self._get_tax_company_id().l10n_br_regime_tributario == '3':
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
                if self._get_tax_company_id().l10n_br_exclui_icms_piscofins:
                    values_to_update['l10n_br_cofins_base'] -= self.l10n_br_icms_valor
                values_to_update['l10n_br_cofins_base'] = values_to_update['l10n_br_cofins_base'] * (1.00 - (l10n_br_cofins_reducao_base/100.00))

            values_to_update['l10n_br_cofins_aliquota'] = 0.00
            if values_to_update['l10n_br_cofins_cst'] == '01':
                # Lucro Presumido
                if self._get_tax_company_id().l10n_br_incidencia_cumulativa == '2':
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

    @api.depends('l10n_br_icms_valor','l10n_br_icmsst_valor','l10n_br_frete','l10n_br_seguro','l10n_br_despesas_acessorias','l10n_br_ipi_valor','price_unit','discount','product_uom_qty','l10n_br_pis_valor','l10n_br_cofins_valor')
    def _l10n_br_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for line in self:
            
            price_unit_discount = line.price_unit - line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            l10n_br_desc_valor = round(price_unit_discount * line.product_uom_qty,2)

            l10n_br_prod_valor = round(line.price_unit * line.product_uom_qty,2)
            l10n_br_total_nfe = l10n_br_prod_valor - l10n_br_desc_valor + line.l10n_br_icmsst_valor + line.l10n_br_frete + line.l10n_br_seguro + line.l10n_br_despesas_acessorias + line.l10n_br_ipi_valor
            l10n_br_total_tributos = line.l10n_br_icms_valor + line.l10n_br_icmsst_valor + line.l10n_br_ipi_valor + line.l10n_br_pis_valor + line.l10n_br_cofins_valor + line.l10n_br_iss_valor + line.l10n_br_irpj_valor + line.l10n_br_csll_valor

            line.update({
                'l10n_br_desc_valor': l10n_br_desc_valor,
                'l10n_br_prod_valor': l10n_br_prod_valor,
                'l10n_br_total_nfe': l10n_br_total_nfe,
                'l10n_br_total_tributos': l10n_br_total_tributos,
            })

    def _prepare_invoice_line(self):
    
        invoice_line_vals = super(SaleOrderLine, self)._prepare_invoice_line()

        if self.company_id.country_id != self.env.ref('base.br'):
            return invoice_line_vals

        invoice_line_vals['l10n_br_operacao_id'] = self.l10n_br_operacao_id.id
        invoice_line_vals['l10n_br_cfop_id'] = self.l10n_br_cfop_id.id
        invoice_line_vals['l10n_br_frete'] = self.l10n_br_frete
        invoice_line_vals['l10n_br_seguro'] = self.l10n_br_seguro
        invoice_line_vals['l10n_br_despesas_acessorias'] = self.l10n_br_despesas_acessorias
        invoice_line_vals['l10n_br_informacao_adicional'] = self.l10n_br_informacao_adicional
        invoice_line_vals['l10n_br_pedido_compra'] = self.l10n_br_pedido_compra
        invoice_line_vals['l10n_br_item_pedido_compra'] = self.l10n_br_item_pedido_compra
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
        invoice_line_vals['l10n_br_icmsst_retido_base'] = self.l10n_br_icmsst_retido_base
        invoice_line_vals['l10n_br_icmsst_retido_aliquota'] = self.l10n_br_icmsst_retido_aliquota
        invoice_line_vals['l10n_br_icmsst_substituto_valor'] = self.l10n_br_icmsst_substituto_valor
        invoice_line_vals['l10n_br_icmsst_retido_valor'] = self.l10n_br_icmsst_retido_valor
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
        invoice_line_vals['l10n_br_iss_valor'] = self.l10n_br_iss_valor
        invoice_line_vals['l10n_br_irpj_valor'] = self.l10n_br_irpj_valor
        invoice_line_vals['l10n_br_csll_valor'] = self.l10n_br_csll_valor
        invoice_line_vals['l10n_br_irpj_ret_valor'] = self.l10n_br_irpj_ret_valor
        invoice_line_vals['l10n_br_inss_ret_valor'] = self.l10n_br_inss_ret_valor
        invoice_line_vals['l10n_br_iss_ret_valor'] = self.l10n_br_iss_ret_valor
        invoice_line_vals['l10n_br_csll_ret_valor'] = self.l10n_br_csll_ret_valor
        invoice_line_vals['l10n_br_pis_ret_valor'] = self.l10n_br_pis_ret_valor
        invoice_line_vals['l10n_br_cofins_ret_valor'] = self.l10n_br_cofins_ret_valor
        
        if 'tax_ids' in invoice_line_vals and len(invoice_line_vals['tax_ids']) > 0:
            tax_key = str(uuid.uuid4())[:8]
            tax_ids = []
            for tax_id in invoice_line_vals['tax_ids'][0][-1]:
                tax = self.env["account.tax"].browse(tax_id)
                new_tax = self._handle_taxes(tax.description, tax_key, tax.price_include, tax.amount, tax.amount_type)
                tax_ids.append(new_tax.id)
            invoice_line_vals['tax_ids'] = [(6,0,tax_ids)]

        return invoice_line_vals

class L10nBrMensagemFiscal(models.Model):
    _name = 'l10n_br_ciel_it_account.mensagem.fiscal'
    _description = 'Mensagem Fiscal'

    name = fields.Char(string='Mensagem',required=True)

class L10nBrCfop(models.Model):
    _name = 'l10n_br_ciel_it_account.cfop'
    _description = 'CFOP'

    name = fields.Char(string='Descrição',required=True)
    codigo_cfop = fields.Char( string='Código CFOP', required=True, copy=False )
    l10n_br_destino_operacao = fields.Selection( LOCAL_DESTINO_OPERACAO, string='Destino Operação' )

    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )
    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )

    _sql_constraints = [
        ('codigo_cfop_uniq', 'unique(codigo_cfop)', 'O código CFOP deve ser unico !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'codigo_cfop': self.codigo_cfop + '(2)'})
        return super(L10nBrCfop, self).copy(dict(default or {}))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {}".format(record.codigo_cfop, record.name)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        elif operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', '|', ('name', operator, name), ('codigo_cfop', operator, name), ('codigo_cfop', operator, name[:4])]
            ])
        cfop_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(cfop_ids).with_user(name_get_uid))

class L10nBrOperacao(models.Model):
    _name = 'l10n_br_ciel_it_account.operacao'
    _description = 'Operação'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Nome',required=True)
    descricao_nf = fields.Char( string='Descrição NF', required=True )

    l10n_br_tipo_operacao = fields.Selection( TIPO_OPERACAO, string='Tipo de Operação' )
    l10n_br_tipo_pedido = fields.Selection( TIPO_PEDIDO_SAIDA, string='Tipo de Pedido (Saída)' )
    l10n_br_tipo_produto = fields.Selection( TIPO_PRODUTO, string='Tipo de Produto' )
    l10n_br_tipo_cliente = fields.Selection( TIPO_CLIENTE, string='Tipo de Cliente' )
    l10n_br_indicador_ie = fields.Selection( INDICADOR_IE, string='Indicador da I.E.' )
    l10n_br_tipo_destinacao = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso' )
    l10n_br_operacao_icmsst = fields.Selection( OPERACAO_ICMSST, string='Operação ICMSST' )
    l10n_br_destino_operacao = fields.Selection( LOCAL_DESTINO_OPERACAO, string='Destino Operação' )
    
    categ_ids = fields.Many2many('product.category', string='Categorias de Produto')
    product_ids = fields.Many2many('product.product', string='Produtos')
    partner_ids = fields.Many2many('res.partner', string='Clientes')
    categ_is_set = fields.Boolean(string='Categorias de Produto Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )
    product_is_set = fields.Boolean(string='Produtos Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )
    partner_is_set = fields.Boolean(string='Clientes Set', store=True, compute_sudo=False, compute='_l10n_br_m2m_set' )

    l10n_br_finalidade = fields.Selection( FINALIDADE_NFE, string='Finalidade Emissão NF-e' )
    l10n_br_intra_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP Interna' )
    l10n_br_inter_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP Interestadual' )
    l10n_br_ext_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP Exterior' )
    l10n_br_documento_id = fields.Many2one( 'l10n_br_ciel_it_account.tipo.documento', string='Tipo de Documento Fiscal', check_company=True)

    l10n_br_icms_cst = fields.Selection( ICMS_CST, string='Código de Situação Tributária do ICMS' )
    l10n_br_icms_modalidade_base = fields.Selection( MODALIDADE_ICMS, string='Modalidade de Determinação da BC do ICMS' )
    l10n_br_icms_reducao_base = fields.Float( string='Aliquota de Redução da BC do ICMS (%)', digits = (12,4) )
    l10n_br_icms_aliquota = fields.Float( string='Aliquota do ICMS (%)' )
    l10n_br_icmsst_modalidade_base = fields.Selection( MODALIDADE_ICMSST, string='Modalidade de Determinação da BC do ICMSST' )
    l10n_br_icmsst_reducao_base = fields.Float( string='Aliquota de Redução da BC do ICMSST (%)', digits = (12,4) )
    l10n_br_icmsst_mva = fields.Float( string='Aliquota da Margem de Valor Adicionado do ICMSST (%)' )
    l10n_br_icmsst_aliquota = fields.Float( string='Aliquota do ICMSST (%)' )
    l10n_br_icmsst_icmsfora = fields.Boolean( string='Não subtrair ICMS do ICMSST' )
    l10n_br_mensagem_fiscal_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal' )

    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )

    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_pis_reducao_base = fields.Float( string='Aliquota de Redução da BC do PIS (%)', digits = (12,4) )
    l10n_br_pis_aliquota = fields.Float( string='Aliquota do PIS (%)' )

    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )
    l10n_br_cofins_reducao_base = fields.Float( string='Aliquota de Redução da BC do Cofins (%)', digits = (12,4) )
    l10n_br_cofins_aliquota = fields.Float( string='Aliquota do Cofins (%)' )

    l10n_br_iss_aliquota = fields.Float( string='Aliquota do ISS (%)' )
    l10n_br_irpj_aliquota = fields.Float( string='Aliquota do IRPJ (%)' )
    l10n_br_csll_aliquota = fields.Float( string='Aliquota do CSLL (%)' )

    l10n_br_irpj_ret_aliquota = fields.Float( string='Aliquota do IRPJ Retido (%)' )
    l10n_br_inss_ret_aliquota = fields.Float( string='Aliquota do INSS Retido (%)' )
    l10n_br_iss_ret_aliquota = fields.Float( string='Aliquota do ISS Retido (%)' )
    l10n_br_csll_ret_aliquota = fields.Float( string='Aliquota do CSLL (%) Retido' )
    l10n_br_pis_ret_aliquota = fields.Float( string='Aliquota do PIS (%) Retido' )
    l10n_br_cofins_ret_aliquota = fields.Float( string='Aliquota do Cofins (%) Retido' )
    
    l10n_br_movimento_estoque = fields.Boolean( string='Movimenta Estoque', default=True )

    _sql_constraints = [	
        ('name_uniq', 'unique(name)', 'O Nome deve ser unico !')	
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrOperacao, self).copy(dict(default or {}))

    @api.depends('categ_ids','product_ids','partner_ids')
    def _l10n_br_m2m_set(self):
        for line in self:
            line.update({
                'categ_is_set': True if line.categ_ids else False,
                'product_is_set': True if line.product_ids else False,
                'partner_is_set': True if line.partner_ids else False,
            })

class L10nBrTipoDocumento(models.Model):
    _name = 'l10n_br_ciel_it_account.tipo.documento'
    _description = 'Tipo de Documento Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char(string='Nome',required=True)
    l10n_br_versao = fields.Selection( VERSAO_NFE, string='Versão do Leiaute' )
    l10n_br_modelo = fields.Char( string='Modelo do Documento Fiscal' )
    l10n_br_formato_impressao = fields.Selection( FORMATO_IMPRESSAO_NFE, string='Formato Impressão' )
    l10n_br_tipo_emissao = fields.Selection( TIPO_EMISSAO_NFE, string='Tipo Emissão' )
    l10n_br_data_contingencia = fields.Datetime(string="Data Entrada em Contingência")
    l10n_br_motivo_contingencia = fields.Char(string="Motivo Contingência")
    l10n_br_ambiente = fields.Selection( AMBIENTE_NFE, string='Ambiente' )
    l10n_br_numero_nfe_id = fields.Many2one('ir.sequence', string='Número da NF' )
    l10n_br_serie_nfe = fields.Char( string='Série do NF' )
    l10n_br_cidadeuf = fields.Char( string='Cidade UF' )
    l10n_br_grupo = fields.Char( string='Grupo' )
    l10n_br_url = fields.Char( string='URL' )
    l10n_br_usuario = fields.Char( string='Usuário' )
    l10n_br_senha = fields.Char( string='Senha' )
    l10n_br_url_cnpj = fields.Char( string='URL CNPJ' )
    l10n_br_token_cnpj = fields.Char( string='Senha CNPJ' )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'O Nome deve ser unico !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrTipoDocumento, self).copy(dict(default or {}))

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _unlink_order(self):
        if self.group_id:
            self.group_id.update({'sale_id': False})
        self.update({'sale_id': False,'purchase_id': False})
        self.move_lines.update({'purchase_line_id': False})
        self.move_ids_without_package.update({'purchase_line_id': False})
