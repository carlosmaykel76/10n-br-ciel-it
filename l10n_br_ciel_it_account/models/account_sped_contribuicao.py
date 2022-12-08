# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *
from odoo.addons.l10n_br_ciel_it_account.models.purchase import *
from odoo.addons.l10n_br_ciel_it_account.models.account_payment_term import *
from odoo.addons.l10n_br_ciel_it_account.models.account import *
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

from sped.efd.pis_cofins.arquivos import ArquivoDigital
from sped.efd.pis_cofins.registros import *

from itertools import groupby
from operator import itemgetter

import pytz
from datetime import datetime, timedelta, time as dtime
from dateutil.relativedelta import relativedelta
from calendar import monthrange
import time

import json
import requests
from requests.auth import HTTPBasicAuth
import base64

import zipfile
import io

import logging
_logger = logging.getLogger(__name__)

class AccountSpedContribuicao(models.Model):
    _name = 'l10n_br_ciel_it_account.sped.contribuicao'
    _description = 'Sped Contribuição'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    name = fields.Char( string="Protocolo", readonly=True )
    date_ini = fields.Date( string="Data Inicial", required=True )
    date_fim = fields.Date( string="Data Final", required=True )    
    arquivo = fields.Char( string="Arquivo", readonly=True )
    situacao = fields.Char( string="Situação", readonly=True )
    arquivo_sped = fields.Binary( string="Arquivo SPED", readonly=True )
    arquivo_sped_fname = fields.Char( string="Arquivo SPED", compute="_get_arquivo_sped_fname" )
    arquivo_sped_erros = fields.Binary( string="Arquivo SPED (Erros)", readonly=True )
    arquivo_sped_erros_fname = fields.Char( string="Arquivo SPED (Erros)", compute="_get_arquivo_sped_erros_fname" )
    
    _arq = None

    def _get_arquivo_sped_fname(self):
        for record in self:
            record.arquivo_sped_fname = "%s.TXT" % record.name

    def _get_arquivo_sped_erros_fname(self):
        for record in self:
            record.arquivo_sped_erros_fname = "%s-erros.TXT" % record.name

    def gerar_sped(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        self._arq = ArquivoDigital()

        cfop_ids_list = []
        product_ids_list = []
        partner_ids_list = []

        self.enviar_registro_A001()
        self.enviar_registro_A990()

        self.enviar_registro_C001()
        self.enviar_registro_C010()
        self.enviar_registro_C100(product_ids_list, partner_ids_list, cfop_ids_list)
        self.enviar_registro_C990()

        self.enviar_registro_D001()
        self.enviar_registro_D010()
        self.enviar_registro_D100(partner_ids_list, cfop_ids_list)
        self.enviar_registro_D990()

        self.enviar_registro_F001()
        self.enviar_registro_F990()

        self.enviar_registro_I001()
        self.enviar_registro_I990()

        self.enviar_registro_M001()
        self.enviar_registro_M990()

        self.enviar_registro_P001()
        self.enviar_registro_P990()

        self.enviar_registro_1001()
        self.enviar_registro_1990()

        self.enviar_registro_0000()
        self.enviar_registro_0001()
        self.enviar_registro_0100()
        self.enviar_registro_0110()
        self.enviar_registro_0140()
        self.enviar_registro_0150(partner_ids_list)
        self.enviar_registro_0190(product_ids_list)
        self.enviar_registro_0200(product_ids_list)
        self.enviar_registro_0400(cfop_ids_list)
        self.enviar_registro_0450()
        self.enviar_registro_0500()
        self.enviar_registro_0600()
        self.enviar_registro_0990()

        self.enviar_registro_9001()
        self.enviar_registro_9900()
        self.enviar_registro_9990()
        
        time.sleep(60*60*12)

        to_write = {}
        to_write["arquivo"] = str(uuid.uuid4())[:8] + "_%s_%s.TXT" % (_format_date(self.date_ini).replace('-',''),_format_date(self.date_fim).replace('-',''))
        to_write["name"] = to_write["arquivo"][:-4]
        to_write["situacao"] = "PROCESSADO"
        to_write["arquivo_sped"] = base64.b64encode(self._arq.getstring().encode('utf-8'))
        self.write(to_write)

    def enviar_registro_0000(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self._arq._registro_abertura.COD_VER = '006'
        self._arq._registro_abertura.TIPO_ESCRIT = '0'
        self._arq._registro_abertura.IND_SIT_ESP = ''
        self._arq._registro_abertura.NUM_REC_ANTERIOR = ''
        self._arq._registro_abertura.DT_INI = self.date_ini
        self._arq._registro_abertura.DT_FIN = self.date_fim
        self._arq._registro_abertura.NOME = self.env.company.l10n_br_razao_social or self.env.company.name
        self._arq._registro_abertura.CNPJ = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)
        self._arq._registro_abertura.UF = self.env.company.state_id.code
        self._arq._registro_abertura.COD_MUN = self.env.company.l10n_br_municipio_id.codigo_ibge
        self._arq._registro_abertura.SUFRAMA = ""
        self._arq._registro_abertura.IND_NAT_PJ = '00' 
        self._arq._registro_abertura.IND_ATIV = '0'

    def enviar_registro_0001(self):
        
        self._arq._blocos['0'].registro_abertura.IND_MOV = '0'
    
    def enviar_registro_0100(self):
    
        registro0100 = Registro0100()
        registro0100.NOME = 'EDSON TELES DA SILVA'
        registro0100.CPF = '71158502915'
        registro0100.CRC = '0330840'
        registro0100.CNPJ = '07122204000144'
        registro0100.CEP = '87015200'
        registro0100.END = 'AV. CARLOS GOMES'
        registro0100.NUM = '617'
        registro0100.COMPL = ''
        registro0100.BAIRRO = 'ZONA 05'
        registro0100.FONE = '4421012502'
        registro0100.FAX = '4421012502'
        registro0100.EMAIL = 'conteles@conteles.com.br'
        registro0100.COD_MUN = '4115200'

        self._arq._blocos['0'].add(registro0100)

    def enviar_registro_0110(self):
        
        registro0110 = Registro0110()

        registro0110.COD_INC_TRIB = '1'
        registro0110.IND_APRO_CRED = '1'
        registro0110.COD_TIPO_CONT = '1'
        registro0110.IND_REG_CUM = ''

        self._arq._blocos['0'].add(registro0110)

    def enviar_registro_0140(self):
    
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        registro0140 = Registro0140()

        registro0140.COD_EST = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)
        registro0140.NOME = self.env.company.l10n_br_razao_social or self.env.company.name
        registro0140.CNPJ = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)
        registro0140.UF = self.env.company.state_id.code
        registro0140.IE = self.env.company.l10n_br_ie or ""
        registro0140.COD_MUN = self.env.company.l10n_br_municipio_id.codigo_ibge
        registro0140.IM = self.env.company.l10n_br_im or ""
        registro0140.SUFRAMA = ""

        self._arq._blocos['0'].add(registro0140)

    def enviar_registro_0150(self, partner_ids_list):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        partner_ids_list = list(set(partner_ids_list))
        for partner_id in self.env['res.partner'].browse(partner_ids_list):

            registro0150 = Registro0150()

            registro0150.COD_PART = str(partner_id.id)
            registro0150.NOME = partner_id.l10n_br_razao_social or partner_id.name
            registro0150.COD_PAIS = partner_id.country_id.l10n_br_codigo_bacen
            registro0150.CNPJ = _format_cnpj_cpf(partner_id.l10n_br_cnpj)
            registro0150.CPF = _format_cnpj_cpf(partner_id.l10n_br_cpf)
            registro0150.IE = partner_id.l10n_br_ie or ""
            registro0150.COD_MUN = partner_id.l10n_br_municipio_id.codigo_ibge
            registro0150.SUFRAMA = partner_id.l10n_br_is or ""
            registro0150.END = partner_id.street
            registro0150.NUM = partner_id.l10n_br_endereco_numero
            registro0150.COMPL = partner_id.street2
            registro0150.BAIRRO = partner_id.l10n_br_endereco_bairro

            self._arq._blocos['0'].add(registro0150)

    def enviar_registro_0190(self, product_ids_list):
    
        uom_ids_list = []
    
        product_ids_list = list(set(product_ids_list))
        for product_id in self.env['product.product'].browse(product_ids_list):
            uom_ids_list.append(product_id.uom_id.id)
    
        grouper = itemgetter("l10n_br_codigo_sefaz")
        uom_ids_list = list(set(uom_ids_list))
        uom_ids = self.env['uom.uom'].browse(uom_ids_list)
        for keygrp, grp in groupby(sorted(uom_ids, key = grouper), grouper):

            registro0190 = Registro0190()

            registro0190.UNID = keygrp
            registro0190.DESCR = dict(uom_ids._fields['l10n_br_codigo_sefaz'].selection).get(keygrp)

            self._arq._blocos['0'].add(registro0190)

    def enviar_registro_0200(self, product_ids_list):
        
        product_ids_list = list(set(product_ids_list))
        for product_id in self.env['product.product'].browse(product_ids_list):

            registro0200 = Registro0200()

            registro0200.COD_ITEM = product_id.default_code
            registro0200.DESCR_ITEM = product_id.name
            registro0200.COD_BARRA = product_id.barcode or ''
            registro0200.COD_ANT_ITEM = ''

            registro0200.UNID_INV = product_id.uom_id.l10n_br_codigo_sefaz or ''

            registro0200.TIPO_ITEM = product_id.categ_id.l10n_br_tipo_produto or ''
            registro0200.COD_NCM = product_id.l10n_br_ncm_id.codigo_ncm or ''
            registro0200.EX_IPI = ''
            registro0200.COD_GEN = (product_id.l10n_br_ncm_id.codigo_ncm or '')[0:2]
            registro0200.COD_LST = ''
            registro0200.ALIQ_ICMS = 0.00

            self._arq._blocos['0'].add(registro0200)

    def enviar_registro_0400(self, cfop_ids_list):

        cfop_ids_list = list(set(cfop_ids_list))
        for cfop_id in self.env['l10n_br_ciel_it_account.cfop'].browse(cfop_ids_list):

            registro0400 = Registro0400()

            registro0400.COD_NAT = cfop_id.codigo_cfop
            registro0400.DESCR_NAT = cfop_id.name

            self._arq._blocos['0'].add(registro0400)

    def enviar_registro_0450(self):

        registro0450 = Registro0450()

        registro0450.COD_INF = '1'
        registro0450.TXT = '%%TEXTO%%'

        self._arq._blocos['0'].add(registro0450)

    def enviar_registro_0500(self):

        for account_id in self.env['account.account'].search([('deprecated','=',False)]):
    
            registro0500 = Registro0500()

            group_id = account_id.group_id
            nivel = 1
            while group_id.parent_id:
                nivel += 1
                group_id = group_id.parent_id

            dt_alt_1 = account_id.write_date.date()
            if dt_alt_1 > self.date_fim:
                dt_alt_1 = self.date_fim

            registro0500.DT_ALT = dt_alt_1
            registro0500.COD_NAT_CC = "0"+str(group_id.code_prefix)
            registro0500.IND_CTA = 'A'
            registro0500.NIVEL = str(nivel)
            registro0500.COD_CTA = account_id.code
            registro0500.NOME_CTA = account_id.name
            registro0500.COD_CTA_REF = ''
            registro0500.CNPJ_EST = ''

            self._arq._blocos['0'].add(registro0500)

    def enviar_registro_0600(self):
        pass

    def enviar_registro_0990(self):
            
        self._arq._blocos['0'].registro_encerramento.QTD_LIN_0 = len(self._arq._blocos['0'].registros) + 1

    def enviar_registro_A001(self):

        self._arq._blocos['A'].registro_abertura.IND_MOV = '1'

    def enviar_registro_A990(self):
    
        self._arq._blocos['A'].registro_encerramento.QTD_LIN_A = len(self._arq._blocos['A'].registros)

    def enviar_registro_C001(self):

        self._arq._blocos['C'].registro_abertura.IND_MOV = '0'

    def enviar_registro_C010(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        registroC010 = RegistroC010()

        registroC010.CNPJ = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)
        registroC010.IND_ESCRI = '2'

        self._arq._blocos['C'].add(registroC010)

    def enviar_registro_C100(self, product_ids_list, partner_ids_list, cfop_ids_list):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        l10n_br_tipo_documentos_sel = ["01","1B","04","55"]

        move_ids = self.env['account.move'].search([('l10n_br_numero_nf','>',0),('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('l10n_br_tipo_documento','in',l10n_br_tipo_documentos_sel),('state','!=','draft')])
        
        for move_id in move_ids:
            
            if move_id.state == 'cancel' and not move_id.l10n_br_chave_nf:
                continue

            registroC100 = RegistroC100()

            registroC100.IND_OPER = str(TIPO_NF[move_id.type])

            if move_id.l10n_br_chave_nf and _format_cnpj_cpf(move_id.company_id.l10n_br_cnpj) in move_id.l10n_br_chave_nf:
                registroC100.IND_EMIT = '0'

                if move_id.l10n_br_cstat_nf == '302':
                    registroC100.COD_SIT = '04'
    
                elif move_id.l10n_br_cstat_nf == '135' and move_id.state == 'cancel':
                    registroC100.COD_SIT = '02'

                elif (move_id.l10n_br_cstat_nf == '100' or  move_id.l10n_br_cstat_nf == '135') and move_id.state == 'posted':

                    if move_id.l10n_br_operacao_id.l10n_br_finalidade == '2':
                        registroC100.COD_SIT = '06'

                    else:
                        registroC100.COD_SIT = '00'

            else:
                if move_id.l10n_br_chave_nf and move_id.l10n_br_chave_nf[6:20] != _format_cnpj_cpf(move_id.partner_id.l10n_br_cnpj):
                    registroC100.COD_SIT = '08'
                else:
                    registroC100.COD_SIT = '00'
                
                registroC100.IND_EMIT = '1'

            registroC100.COD_MOD = move_id.l10n_br_tipo_documento
            
            registroC100.CHV_NFE = move_id.l10n_br_chave_nf

            registroC100.SER = move_id.l10n_br_serie_nf
            registroC100.NUM_DOC = str(move_id.l10n_br_numero_nf)

            if not registroC100.COD_SIT in ['02','03','04']:
                partner_ids_list.append(move_id.partner_id.id)
                registroC100.COD_PART = str(move_id.partner_id.id)
                registroC100.DT_DOC = move_id.invoice_date
                registroC100.DT_E_S = move_id.date if move_id.date >= move_id.invoice_date else move_id.invoice_date
                registroC100.VL_DOC = move_id.l10n_br_total_nfe
                registroC100.IND_PGTO = move_id.invoice_payment_term_id.l10n_br_indicador or "1"
                registroC100.VL_DESC = move_id.l10n_br_desc_valor
                registroC100.VL_ABAT_NT = 0.00
                registroC100.VL_MERC = move_id.l10n_br_prod_valor
                registroC100.IND_FRT = move_id.invoice_incoterm_id.l10n_br_modalidade_frete or "9"
                registroC100.VL_FRT = move_id.l10n_br_frete
                registroC100.VL_SEG = move_id.l10n_br_seguro
                registroC100.VL_OUT_DA = move_id.l10n_br_despesas_acessorias
                registroC100.VL_BC_ICMS = move_id.l10n_br_icms_base
                
                l10n_br_icms_valor = move_id.l10n_br_icms_valor + sum([line.l10n_br_icms_valor_outros for line in move_id.invoice_line_ids if TIPO_NF[line.move_id.type] == 0 and line.l10n_br_icms_cst == '90'])
                registroC100.VL_ICMS = l10n_br_icms_valor
                
                registroC100.VL_BC_ICMS_ST = move_id.l10n_br_icmsst_base
                registroC100.VL_ICMS_ST = move_id.l10n_br_icmsst_valor+move_id.l10n_br_icmsst_substituto_valor+move_id.l10n_br_icmsst_retido_valor
                registroC100.VL_IPI = move_id.l10n_br_ipi_valor
                registroC100.VL_PIS = move_id.l10n_br_pis_valor
                registroC100.VL_COFINS = move_id.l10n_br_cofins_valor
                registroC100.VL_PIS_ST = move_id.l10n_br_pis_ret_valor
                registroC100.VL_COFINS_ST = move_id.l10n_br_cofins_ret_valor

            self._arq._blocos['C'].add(registroC100)

            if not registroC100.COD_SIT in ['02','03','04']:
                self.enviar_registro_C110(move_id)
                if not registroC100.IND_EMIT == '0':
                    self.enviar_registro_C170(move_id, product_ids_list, cfop_ids_list)


    def enviar_registro_C110(self, move_id):

        def _format_obs(texto):
            return str(texto).replace('"',' ').replace("¬"," ").replace("§","").replace("°","").replace("º","").replace("ª","").replace("\n"," ").replace("&","E").replace("%","")

        if move_id.l10n_br_informacao_fiscal:

            registroC110 = RegistroC110()

            registroC110.COD_INF = '1'
            registroC110.TXT_COMPL = _format_obs(move_id.l10n_br_informacao_fiscal)

            self._arq._blocos['C'].add(registroC110)

        elif len(move_id.referencia_ids) > 0:
            
            registroC110 = RegistroC110()

            registroC110.COD_INF = '1'
            registroC110.TXT_COMPL = _format_obs(",".join([invoice_ref.l10n_br_chave_nf for invoice_ref in move_id.referencia_ids]))

            self._arq._blocos['C'].add(registroC110)


    def enviar_registro_C170(self, move_id, product_ids_list, cfop_ids_list):

        invoice_lines = []
        invoice_line_ids = move_id.invoice_line_ids.filtered(lambda l: not l.display_type)
        for nItem, invoice_line in enumerate(sorted(invoice_line_ids, key=lambda l: l[0].sequence)):

            registroC170 = RegistroC170()

            registroC170.NUM_ITEM = str(nItem + 1)

            product_ids_list.append(invoice_line.product_id.id)
            registroC170.COD_ITEM = invoice_line.product_id.default_code or ""
            registroC170.DESCR_COMPL = invoice_line.l10n_br_informacao_adicional or ""
            registroC170.QTD = invoice_line.quantity
            registroC170.UNID = invoice_line.product_id.uom_id.l10n_br_codigo_sefaz
            registroC170.VL_ITEM = invoice_line.l10n_br_prod_valor
            registroC170.VL_DESC = invoice_line.l10n_br_desc_valor
            registroC170.IND_MOV = '0' if invoice_line.l10n_br_operacao_id.l10n_br_movimento_estoque else '1'
            registroC170.CST_ICMS = str(invoice_line.l10n_br_icms_cst or "").zfill(3)
            
            cfop_ids_list.append(invoice_line.l10n_br_cfop_id.id)
            registroC170.CFOP = invoice_line.l10n_br_cfop_id.codigo_cfop
            registroC170.COD_NAT = invoice_line.l10n_br_cfop_id.codigo_cfop

            registroC170.VL_BC_ICMS = invoice_line.l10n_br_icms_base
            registroC170.ALIQ_ICMS = invoice_line.l10n_br_icms_aliquota
            registroC170.VL_ICMS = invoice_line.l10n_br_icms_valor + (invoice_line.l10n_br_icms_valor_outros if TIPO_NF[invoice_line.move_id.type] == 0 and invoice_line.l10n_br_icms_cst == '90' else 0.00)
            registroC170.VL_BC_ICMS_ST = invoice_line.l10n_br_icmsst_base
            registroC170.ALIQ_ST = invoice_line.l10n_br_icmsst_aliquota
            registroC170.VL_ICMS_ST = invoice_line.l10n_br_icmsst_valor+invoice_line.l10n_br_icmsst_substituto_valor+invoice_line.l10n_br_icmsst_retido_valor
            registroC170.IND_APUR = '0'
            registroC170.CST_IPI = invoice_line.l10n_br_ipi_cst
            registroC170.COD_ENQ = ''
            registroC170.VL_BC_IPI = invoice_line.l10n_br_ipi_base
            registroC170.ALIQ_IPI = invoice_line.l10n_br_ipi_aliquota
            registroC170.VL_IPI = invoice_line.l10n_br_ipi_valor
            registroC170.CST_PIS = invoice_line.l10n_br_pis_cst
            registroC170.VL_BC_PIS = invoice_line.l10n_br_pis_base
            registroC170.ALIQ_PIS = invoice_line.l10n_br_pis_aliquota
            registroC170.QUANT_BC_PIS = 0
            registroC170.ALIQ_PIS_QUANT = 0
            registroC170.VL_PIS = invoice_line.l10n_br_pis_valor
            registroC170.CST_COFINS = invoice_line.l10n_br_cofins_cst
            registroC170.VL_BC_COFINS = invoice_line.l10n_br_cofins_base
            registroC170.ALIQ_COFINS = invoice_line.l10n_br_cofins_aliquota
            registroC170.QUANT_BC_COFINS = 0
            registroC170.ALIQ_COFINS_QUANT = 0
            registroC170.VL_COFINS = invoice_line.l10n_br_cofins_valor
            registroC170.COD_CTA = invoice_line.account_id.code

            self._arq._blocos['C'].add(registroC170)

    def enviar_registro_C990(self):
            
        self._arq._blocos['C'].registro_encerramento.QTD_LIN_C = len(self._arq._blocos['C'].registros)

    def enviar_registro_D001(self):
    
        self._arq._blocos['D'].registro_abertura.IND_MOV = '0'

    def enviar_registro_D010(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        registroD010 = RegistroD010()

        registroD010.CNPJ = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)

        self._arq._blocos['D'].add(registroD010)

    def enviar_registro_D100(self, partner_ids_list, cfop_ids_list):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        l10n_br_tipo_documentos_sel = ["07","08","8B","09","10","11","26","27","57","63","67"]

        move_ids = self.env['account.move'].search([('l10n_br_numero_nf','>',0),('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('l10n_br_tipo_documento','in',l10n_br_tipo_documentos_sel),('state','!=','draft')])
        
        for move_id in move_ids:
            
            if move_id.state == 'cancel' and not move_id.l10n_br_chave_nf:
                continue

            registroD100 = RegistroD100()

            registroD100.IND_OPER = str(TIPO_NF[move_id.type])
            
            if move_id.l10n_br_chave_nf and _format_cnpj_cpf(move_id.company_id.l10n_br_cnpj) in move_id.l10n_br_chave_nf:
                registroD100.IND_EMIT = '0'

                if move_id.l10n_br_cstat_nf == '302':
                    registroD100.COD_SIT = '04'
    
                elif move_id.l10n_br_cstat_nf == '135' and move_id.state == 'cancel':
                    registroD100.COD_SIT = '02'

                if move_id.l10n_br_cstat_nf == '100' and move_id.state == 'posted':

                    if move_id.l10n_br_operacao_id.l10n_br_finalidade == '2':
                        registroD100.COD_SIT = '06'

                    else:
                        registroD100.COD_SIT = '00'

            else:
                registroD100.IND_EMIT = '1'
                registroD100.COD_SIT = '00'

            registroD100.COD_MOD = move_id.l10n_br_tipo_documento
            registroD100.CHV_CTE = move_id.l10n_br_chave_nf

            if not registroD100.COD_SIT in ['02','03','04']:
                partner_ids_list.append(move_id.partner_id.id)
                registroD100.COD_PART = str(move_id.partner_id.id)
                registroD100.SER = move_id.l10n_br_serie_nf
                registroD100.SUB = ""
                registroD100.NUM_DOC = str(move_id.l10n_br_numero_nf)
                registroD100.DT_DOC = move_id.invoice_date
                registroD100.DT_A_P = move_id.date if move_id.date >= move_id.invoice_date else move_id.invoice_date
                registroD100.TP_CTE = ""
                registroD100.CHV_CTE_REF = ""
                registroD100.VL_DOC = move_id.l10n_br_total_nfe
                registroD100.VL_DESC = move_id.l10n_br_desc_valor
                registroD100.IND_FRT = move_id.invoice_incoterm_id.l10n_br_modalidade_frete or "9"
                registroD100.VL_SERV = move_id.l10n_br_prod_valor
                registroD100.VL_BC_ICMS = move_id.l10n_br_icms_base
                
                l10n_br_icms_valor = move_id.l10n_br_icms_valor + sum([line.l10n_br_icms_valor_outros for line in move_id.invoice_line_ids if TIPO_NF[line.move_id.type] == 0 and line.l10n_br_icms_cst == '90'])
                registroD100.VL_ICMS = l10n_br_icms_valor
                
                registroD100.VL_NT = 0.00
                registroD100.COD_INF = ""
                registroD100.COD_CTA = move_id.invoice_line_ids[0].account_id.code

            self._arq._blocos['D'].add(registroD100)

            if not registroD100.COD_SIT in ['02','03','04']:
                self.enviar_registro_D101(move_id, cfop_ids_list)
                self.enviar_registro_D105(move_id, cfop_ids_list)

    def enviar_registro_D101(self, move_id, cfop_ids_list):
    
        for invoice_line_id in move_id.invoice_line_ids.filtered(lambda l: not l.display_type):
    
            registroD101 = RegistroD101()

            registroD101.IND_NAT_FRT = '2'
            registroD101.VL_ITEM = invoice_line_id.l10n_br_prod_valor+invoice_line_id.l10n_br_frete+invoice_line_id.l10n_br_seguro+invoice_line_id.l10n_br_despesas_acessorias+invoice_line_id.l10n_br_icmsst_valor+invoice_line_id.l10n_br_icmsst_valor_outros+invoice_line_id.l10n_br_fcp_st_valor+invoice_line_id.l10n_br_ipi_valor+invoice_line_id.l10n_br_ipi_valor_outros+invoice_line_id.l10n_br_ipi_valor_isento-invoice_line_id.l10n_br_desc_valor
            registroD101.CST_PIS = invoice_line_id.l10n_br_cofins_cst
            registroD101.NAT_BC_CRED = '03'
            registroD101.VL_BC_PIS = invoice_line_id.l10n_br_cofins_base
            registroD101.ALIQ_PIS = invoice_line_id.l10n_br_cofins_aliquota
            registroD101.VL_PIS = invoice_line_id.l10n_br_cofins_valor
            registroD101.COD_CTA = '420104021'

            self._arq._blocos['D'].add(registroD101)

    def enviar_registro_D105(self, move_id, cfop_ids_list):
    
        for invoice_line_id in move_id.invoice_line_ids.filtered(lambda l: not l.display_type):
    
            registroD105 = RegistroD105()

            registroD105.IND_NAT_FRT = '2'
            registroD105.VL_ITEM = invoice_line_id.l10n_br_prod_valor+invoice_line_id.l10n_br_frete+invoice_line_id.l10n_br_seguro+invoice_line_id.l10n_br_despesas_acessorias+invoice_line_id.l10n_br_icmsst_valor+invoice_line_id.l10n_br_icmsst_valor_outros+invoice_line_id.l10n_br_fcp_st_valor+invoice_line_id.l10n_br_ipi_valor+invoice_line_id.l10n_br_ipi_valor_outros+invoice_line_id.l10n_br_ipi_valor_isento-invoice_line_id.l10n_br_desc_valor
            registroD105.CST_COFINS = invoice_line_id.l10n_br_cofins_cst
            registroD105.NAT_BC_CRED = '03'
            registroD105.VL_BC_COFINS = invoice_line_id.l10n_br_cofins_base
            registroD105.ALIQ_COFINS = invoice_line_id.l10n_br_cofins_aliquota
            registroD105.VL_COFINS = invoice_line_id.l10n_br_cofins_valor
            registroD105.COD_CTA = '420104021'

            self._arq._blocos['D'].add(registroD105)

    def enviar_registro_D990(self):
            
        self._arq._blocos['D'].registro_encerramento.QTD_LIN_D = len(self._arq._blocos['D'].registros)

    def enviar_registro_F001(self):
    
        self._arq._blocos['F'].registro_abertura.IND_MOV = '1'

    def enviar_registro_F990(self):
    
        self._arq._blocos['F'].registro_encerramento.QTD_LIN_F = len(self._arq._blocos['F'].registros)

    def enviar_registro_I001(self):
    
        self._arq._blocos['I'].registro_abertura.IND_MOV = '1'

    def enviar_registro_I990(self):
    
        self._arq._blocos['I'].registro_encerramento.QTD_LIN_I = len(self._arq._blocos['I'].registros)

    def enviar_registro_M001(self):
    
        self._arq._blocos['M'].registro_abertura.IND_MOV = '1'

    def enviar_registro_M990(self):
    
        self._arq._blocos['M'].registro_encerramento.QTD_LIN_M = len(self._arq._blocos['M'].registros)

    def enviar_registro_P001(self):
    
        self._arq._blocos['P'].registro_abertura.IND_MOV = '1'

    def enviar_registro_P990(self):
    
        self._arq._blocos['P'].registro_encerramento.QTD_LIN_P = len(self._arq._blocos['P'].registros)

    def enviar_registro_1001(self):
    
        self._arq._blocos['1'].registro_abertura.IND_MOV = '1'

    def enviar_registro_1990(self):
    
        self._arq._blocos['1'].registro_encerramento.QTD_LIN_1 = len(self._arq._blocos['1'].registros)

    def enviar_registro_9001(self):
    
        self._arq._blocos['9'].registro_abertura.IND_MOV = '0'

    def enviar_registro_9900(self):
    
        for key in self._arq._blocos.keys():
            
            if key == '9':
                registro9900 = Registro9900()

                registro9900.REG_BLC = '0000'
                registro9900.QTD_REG_BLC = 1

                self._arq._blocos['9'].add(registro9900)

            bloco = self._arq._blocos[key]
            
            regkeys = sorted(list(set([registro.REG for registro in bloco.registros])))

            for regkey in regkeys:
                
                qtdreg = len([1 for registro in bloco.registros if registro.REG == regkey])
    
                registro9900 = Registro9900()

                registro9900.REG_BLC = regkey
                registro9900.QTD_REG_BLC = qtdreg

                self._arq._blocos['9'].add(registro9900)
            
            if key == '9':
                registro9900 = Registro9900()

                registro9900.REG_BLC = '9999'
                registro9900.QTD_REG_BLC = 1

                self._arq._blocos['9'].add(registro9900)

    def enviar_registro_9990(self):
    
        self._arq._blocos['9'].registro_encerramento.QTD_LIN_9 = len(self._arq._blocos['9'].registros) + 1
