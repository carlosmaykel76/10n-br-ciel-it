# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import pycep_correios
from pycpfcnpj import cpf, cnpj, compatible
from odoo.osv import expression
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *

import logging
_logger = logging.getLogger(__name__)

ORIGEM_MERCADORIA = [
    ('0', '0 - Nacional, exceto as indicadas nos códigos 3, 4, 5 e 8;'),
    ('1', '1 - Estrangeira - Importação direta, exceto a indicada no código 6;'),
    ('2', '2 - Estrangeira - Adquirida no mercado interno, exceto a indicada no código 7;'),
    ('3', '3 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 40% e inferior ou igual a 70%;'),
    ('4', '4 - Nacional, cuja produção tenha sido feita em conformidade com os processos produtivos básicos de quetratam as legislações citadas nos Ajustes;'),
    ('5', '5 - Nacional, mercadoria ou bem com Conteúdo de Importação inferior ou igual a 40%;'),
    ('6', '6 - Estrangeira - Importação direta, sem similar nacional, constante em lista da CAMEX e gás natural;'),
    ('7', '7 - Estrangeira - Adquirida no mercado interno, sem similar nacional, constante lista CAMEX e gás natural.'),
    ('8', '8 - Nacional, mercadoria ou bem com Conteúdo de Importação superior a 70%;'),
]

TIPO_PRODUTO = [
    ('00', '00 - Mercadoria para Revenda'),
    ('01', '01 - Matéria Prima'),
    ('02', '02 - Embalagem'),
    ('03', '03 - Produto em Processo'),
    ('04', '04 - Produto Acabado'),
    ('05', '05 - Subproduto'),
    ('06', '06 - Produto Intermediário'),
    ('07', '07 - Material de Uso e Consumo'),
    ('08', '08 - Ativo Imobilizado'),
    ('09', '09 - Serviços'),
    ('10', '10 - Outros insumos'),
    ('99', '99 - Outras    '),
]

class ProductCategory(models.Model):
    _inherit = "product.category"

    l10n_br_tipo_produto = fields.Selection( TIPO_PRODUTO, string='Tipo do Produto' )

class Product(models.Model):
    _inherit = "product.template"

    l10n_br_origem = fields.Selection( ORIGEM_MERCADORIA, string='Origem do Produto' )
    l10n_br_fci = fields.Char( string='FCI' )
    l10n_br_fator_utrib = fields.Float( string='Fator Unidade Tributável', digits = (12,8) )
    l10n_br_ncm_id = fields.Many2one( 'l10n_br_ciel_it_account.ncm', string='NCM' )
    l10n_br_codigo_servico = fields.Char( string='Código Serviço' )
    l10n_br_codigo_tributacao_servico = fields.Char( string='Código Tributação Serviço' )
    l10n_br_indescala = fields.Boolean( string='Indicador de Escala Relevante', default=True )
    l10n_br_cnpj_fabricante = fields.Char( string='CNPJ Fabricante' )
    l10n_br_grupo_id = fields.Many2one( 'l10n_br_ciel_it_account.product.group', string='Grupo' )
    l10n_br_informacao_adicional = fields.Text( string='Informações Adicionais' )

class L10nBrProductGroup(models.Model):
    _name = 'l10n_br_ciel_it_account.product.group'
    _description = 'Grupo de Produtos'

    name = fields.Char(string='Grupo',required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'O Grupo deve ser unico !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrProductGroup, self).copy(dict(default or {}))

class L10nBrIestUf(models.Model):
    _name = 'l10n_br_ciel_it_account.iest.uf'
    _description = 'IE ST por UF'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company, tracking=True)
    state_de_id = fields.Many2one('res.country.state', string='UF Origem', domain="[('country_id.code', '=', 'BR')]", required=True, tracking=True)
    state_para_id = fields.Many2one('res.country.state', string='UF Destino', domain="[('country_id.code', '=', 'BR')]", required=True, tracking=True)
    l10n_br_iest = fields.Char( string='Inscrição Estadual do Substituto Tributário', tracking=True )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {} - {}".format(record.state_de_id.code, record.state_para_id.code, record.l10n_br_iest)))
        return result

class L10nBrNcmUf(models.Model):
    _name = 'l10n_br_ciel_it_account.ncm.uf'
    _description = 'NCM por UF'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    state_de_id = fields.Many2one('res.country.state', string='UF Origem', domain="[('country_id.code', '=', 'BR')]", required=True)
    state_para_id = fields.Many2one('res.country.state', string='UF Destino', domain="[('country_id.code', '=', 'BR')]", required=True)
    l10n_br_ncm_id = fields.Many2one( 'l10n_br_ciel_it_account.ncm', string='NCM' )
    l10n_br_fcp_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%)' )
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

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {} - {}".format(record.state_de_id.code, record.state_para_id.code, record.l10n_br_ncm_id.codigo_ncm)))
        return result

class L10nBrNcmUf(models.Model):
    _name = 'l10n_br_ciel_it_account.ncm.cliente.uf'
    _description = 'NCM por UF e Cliente'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    state_de_id = fields.Many2one('res.country.state', string='UF Origem', domain="[('country_id.code', '=', 'BR')]", required=True)
    state_para_id = fields.Many2one('res.country.state', string='UF Destino', domain="[('country_id.code', '=', 'BR')]", required=True)
    l10n_br_ncm_id = fields.Many2one( 'l10n_br_ciel_it_account.ncm', string='NCM' )
    partner_ids = fields.Many2many( 'res.partner', string='Clientes' )
    l10n_br_fcp_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%)' )
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

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {} - {}".format(record.state_de_id.code, record.state_para_id.code, record.l10n_br_ncm_id.codigo_ncm)))
        return result

class L10nBrIcmsUf(models.Model):
    _name = 'l10n_br_ciel_it_account.icms.uf'
    _description = 'ICMS por UF'

    state_de_id = fields.Many2one('res.country.state', string='UF Origem', domain="[('country_id.code', '=', 'BR')]", required=True)
    state_para_id = fields.Many2one('res.country.state', string='UF Destino', domain="[('country_id.code', '=', 'BR')]", required=True)
    l10n_br_icms_aliquota = fields.Float( string='Aliquota do ICMS (%)' )
    l10n_br_icms_ext_aliquota = fields.Float( string='Aliquota do ICMS (Origem Exterior) (%)' )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {}".format(record.state_de_id.code, record.state_para_id.code)))
        return result

class L10nBrIcmsBeneficio(models.Model):
    _name = 'l10n_br_ciel_it_account.icms.beneficio'
    _description = 'Código Benefício ICMS'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_ncm_id = fields.Many2one( 'l10n_br_ciel_it_account.ncm', string='NCM' )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP' )
    l10n_br_icms_cst = fields.Selection( ICMS_CST, string='Código de Situação Tributária do ICMS' )
    l10n_br_codigo_beneficio = fields.Char( string='Código do Benefício Fiscal' )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {} - {}".format(record.l10n_br_ncm_id.codigo_ncm, record.l10n_br_cfop_id.codigo_cfop, record.l10n_br_icms_cst)))
        return result

class L10nBrIpiEnquadramento(models.Model):
    _name = 'l10n_br_ciel_it_account.ipi.enquadramento'
    _description = 'Código Enquadramento IPI'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    l10n_br_ncm_id = fields.Many2one( 'l10n_br_ciel_it_account.ncm', string='NCM' )
    l10n_br_cfop_id = fields.Many2one( 'l10n_br_ciel_it_account.cfop', string='CFOP' )
    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )
    l10n_br_codigo_enquadramento = fields.Char( string='Código do Enquadramento' )

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} - {} - {}".format(record.l10n_br_ncm_id.codigo_ncm, record.l10n_br_cfop_id.codigo_cfop, record.l10n_br_ipi_cst)))
        return result

class L10nBrNcm(models.Model):
    _name = 'l10n_br_ciel_it_account.ncm'
    _description = 'NCM'

    name = fields.Char(string='Descrição',required=True)
    codigo_ncm = fields.Char( string='Código NCM', required=True )
    codigo_cest = fields.Char( string='Código CEST' )
    uom_id = fields.Many2one('uom.uom', string='Unidade Tributável')

    l10n_br_ipi_cst = fields.Selection( IPI_CST, string='Código de Situação Tributária do IPI' )
    l10n_br_ipi_aliquota = fields.Float( string='Aliquota do IPI (%)' )
    l10n_br_ipi_enq = fields.Char( string='Código Enquadramento' )

    l10n_br_pis_cst = fields.Selection( PIS_CST, string='Código de Situação Tributária do PIS' )
    l10n_br_pis_reducao_base = fields.Float( string='Aliquota de Redução da BC do PIS (%)', digits = (12,4) )
    l10n_br_pis_aliquota = fields.Float( string='Aliquota do PIS (%)' )

    l10n_br_cofins_cst = fields.Selection( COFINS_CST, string='Código de Situação Tributária do Cofins' )
    l10n_br_cofins_reducao_base = fields.Float( string='Aliquota de Redução da BC do Cofins (%)', digits = (12,4) )
    l10n_br_cofins_aliquota = fields.Float( string='Aliquota do Cofins (%)' )

    _sql_constraints = [
        ('codigo_ncm_codigo_cest_uniq', 'unique(codigo_ncm,codigo_cest)', 'O código NCM/CEST deve ser unico !')
    ]

    def name_get(self):
        result = []
        for record in self:
            if record.codigo_cest:
                result.append((record.id, "{} - {} ({})".format(record.codigo_ncm, record.name, record.codigo_cest)))
            else:
                result.append((record.id, "{} - {}".format(record.codigo_ncm, record.name)))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        elif operator in ('ilike', 'like', '=', '=like', '=ilike'):
            domain = expression.AND([
                args or [],
                ['|', '|', ('name', operator, name), ('codigo_ncm', operator, name[:8]), ('codigo_cest', operator, name)]
            ])
        ncm_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(ncm_ids).with_user(name_get_uid))

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'codigo_ncm': self.codigo_ncm + '(2)'})
        return super(L10nBrNcm, self).copy(dict(default or {}))

class ProductSupplierinfo(models.Model):
    _inherit = "product.supplierinfo"

    fator_un = fields.Float( string="Fator Unidade de Medida", default=1, digits = (12,6) )