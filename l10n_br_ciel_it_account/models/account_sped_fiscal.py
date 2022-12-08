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

from sped.efd.icms_ipi.arquivos import ArquivoDigital
from sped.efd.icms_ipi.registros import *

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

GRUPO_DE_CONTA = {
    'asset': '01',
    'expense': '02',
    'liability': '02',
    'equity': '03',
    'income': '04',
    'off_balance': '09',
}

class AccountSpedFiscalUfDIFALFCP(models.Model):
    _name = 'l10n_br_ciel_it_account.sped.fiscal.uf.difal.fcp'
    _description = 'Sped Fiscal UF DIFAL'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    sped_fiscal_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.sped.fiscal', string='Sped Fiscal' )
    state_id = fields.Many2one('res.country.state', string='UF')

    e310_vl_sld_cred_ant_difal = fields.Float( string="E310 - DIFAL - Saldo credor de período anterior", compute="_get_e310_vl_sld_cred_ant_difal" )
    e310_vl_tot_debitos_difal = fields.Float( string="E310 - DIFAL - Valor total dos débitos" )
    e310_vl_out_deb_difal = fields.Float( string="E310 - DIFAL - Valor total dos ajustes Debitos" )
    e310_vl_tot_creditos_difal = fields.Float( string="E310 - DIFAL - Valor total dos créditos" )
    e310_vl_out_cred_difal = fields.Float( string="E310 - DIFAL - Valor total de Ajustes Creditos" )
    e310_vl_sld_dev_ant_difal = fields.Float( string="E310 - DIFAL - Saldo devedor", compute="_get_e310_vl_sld_dev_ant_difal" )
    e310_vl_deducoes_difal = fields.Float( string="E310 - DIFAL - Deduções" )
    e310_vl_recol_difal = fields.Float( string="E310 - DIFAL - Valor recolhido ou a recolher", compute="_get_e310_vl_recol_difal" )
    e310_vl_sld_cred_transportar_difal = fields.Float( string="E310 - DIFAL - Saldo credor a transportar", compute="_get_e310_vl_sld_cred_transportar_difal" )
    e310_deb_esp_difal  = fields.Float( string="E310 - DIFAL - Valores recolhidos" )

    e310_vl_sld_cred_ant_fcp = fields.Float( string="E310 - FCP - Saldo credor de período anterior", compute="_get_e310_vl_sld_cred_ant_fcp" )
    e310_vl_tot_deb_fcp = fields.Float( string="E310 - FCP - Valor total dos débitos" )
    e310_vl_out_deb_fcp = fields.Float( string="E310 - FCP - Valor total dos ajustes Debitos" )
    e310_vl_tot_cred_fcp = fields.Float( string="E310 - FCP - Valor total dos créditos" )
    e310_vl_out_cred_fcp = fields.Float( string="E310 - FCP - Valor total de Ajustes Creditos" )
    e310_vl_sld_dev_ant_fcp = fields.Float( string="E310 - FCP - Saldo devedor", compute="_get_e310_vl_sld_dev_ant_fcp" )
    e310_vl_deducoes_fcp = fields.Float( string="E310 - FCP - Deduções" )
    e310_vl_recol_fcp  = fields.Float( string="E310 - FCP - Valor recolhido ou a recolher", compute="_get_e310_vl_recol_fcp" )
    e310_vl_sld_cred_transportar_fcp = fields.Float( string="E310 - FCP - Saldo credor a transportar", compute="_get_e310_vl_sld_cred_transportar_fcp" )
    e310_deb_esp_fcp  = fields.Float( string="E310 - FCP - Valores recolhidos" )

    def _get_e310_vl_sld_cred_ant_difal(self):
        pass

    def _get_e310_vl_sld_dev_ant_difal(self):
        pass

    def _get_e310_vl_recol_difal(self):
        pass

    def _get_e310_vl_sld_cred_transportar_difal(self):
        pass

    def _get_e310_vl_sld_cred_ant_fcp(self):
        pass

    def _get_e310_vl_sld_dev_ant_fcp(self):
        pass

    def _get_e310_vl_recol_fcp(self):
        pass

    def _get_e310_vl_sld_cred_transportar_fcp(self):
        pass
    
class AccountSpedFiscalUfICMSST(models.Model):
    _name = 'l10n_br_ciel_it_account.sped.fiscal.uf.icmsst'
    _description = 'Sped Fiscal UF ICMSST'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    sped_fiscal_id = fields.Many2one( comodel_name='l10n_br_ciel_it_account.sped.fiscal', string='Sped Fiscal' )
    state_id = fields.Many2one('res.country.state', string='UF')
    
    e210_vl_sld_cred_ant_st = fields.Float( string="E210 - Saldo credor de período anterior", compute="_get_e210_vl_sld_cred_ant_st" )
    e210_vl_devol_st = fields.Float( string="E210 - ICMS-ST de devolução" )
    e210_vl_ressarc_st = fields.Float( string="E210 - ICMS-ST de ressarcimentos" )
    e210_vl_out_cred_st = fields.Float( string="E210 - Outros créditos ST" )
    e210_vl_aj_creditos_st = fields.Float( string="E210 - Ajustes a crédito de ICMS-ST" )
    e210_vl_retencao_st = fields.Float( string="E210 - ICMS retido por Substituição Tributária" )
    e210_vl_out_deb_st = fields.Float( string="E210 - Outros débitos ST" )
    e210_vl_aj_debitos_st = fields.Float( string="E210 - Ajustes a débito de ICMS-ST" )
    e210_vl_sld_dev_ant_st = fields.Float( string="E210 - Saldo devedor antes das deduções", compute="_get_e210_vl_sld_dev_ant_st" )
    e210_vl_deducoes_st = fields.Float( string="E210 - Deduções ST" )
    e210_vl_icms_recol_st = fields.Float( string="E210 - Imposto a recolher ST", compute="_get_e210_vl_icms_recol_st" )
    e210_vl_sld_cred_st_transportar = fields.Float( string="E210 - Saldo credor de ST", compute="_get_e210_vl_sld_cred_st_transportar" )
    e210_deb_esp_st = fields.Float( string="E210 - Valores recolhidos" )

    @api.depends('sped_fiscal_id','state_id')
    def _get_e210_vl_sld_cred_ant_st(self):
        for record in self:
            record_ant = record.sped_fiscal_id.search([('date_ini','=',record.sped_fiscal_id.date_ini + relativedelta(months=-1))],limit=1)
            record_ant = record_ant.line_icmsst_ids.filtered(lambda l: l.state_id.id == record.state_id.id)
            record.e210_vl_sld_cred_ant_st = record_ant.e210_vl_sld_cred_st_transportar if record_ant else 0.00

    @api.depends('e210_vl_retencao_st','e210_vl_out_deb_st','e210_vl_aj_debitos_st','e210_vl_sld_cred_ant_st',
                 'e210_vl_devol_st','e210_vl_ressarc_st','e210_vl_out_cred_st','e210_vl_aj_creditos_st')
    def _get_e210_vl_sld_dev_ant_st(self):
        for record in self:
            e210_vl_sld_dev_ant_st = (record.e210_vl_retencao_st + record.e210_vl_out_deb_st + record.e210_vl_aj_debitos_st) - \
                (record.e210_vl_sld_cred_ant_st + record.e210_vl_devol_st + record.e210_vl_ressarc_st + record.e210_vl_out_cred_st + record.e210_vl_aj_creditos_st)
            record.e210_vl_sld_dev_ant_st = e210_vl_sld_dev_ant_st if e210_vl_sld_dev_ant_st > 0.00 else 0.00

    @api.depends('e210_vl_retencao_st','e210_vl_out_deb_st','e210_vl_aj_debitos_st','e210_vl_sld_cred_ant_st',
                 'e210_vl_devol_st','e210_vl_ressarc_st','e210_vl_out_cred_st','e210_vl_aj_creditos_st')
    def _get_e210_vl_sld_cred_st_transportar(self):
        for record in self:
            e210_vl_sld_cred_st_transportar = (record.e210_vl_retencao_st + record.e210_vl_out_deb_st + record.e210_vl_aj_debitos_st) - \
                (record.e210_vl_sld_cred_ant_st + record.e210_vl_devol_st + record.e210_vl_ressarc_st + record.e210_vl_out_cred_st + record.e210_vl_aj_creditos_st)
            record.e210_vl_sld_cred_st_transportar = abs(e210_vl_sld_cred_st_transportar) if e210_vl_sld_cred_st_transportar < 0.00 else 0.00

    @api.depends('e210_vl_sld_dev_ant_st','e210_vl_deducoes_st')
    def _get_e210_vl_icms_recol_st(self):
        for record in self:
            e210_vl_icms_recol_st = record.e210_vl_sld_dev_ant_st - record.e210_vl_deducoes_st
            record.e210_vl_icms_recol_st = e210_vl_icms_recol_st if e210_vl_icms_recol_st > 0.00 else 0.00

class AccountSpedFiscal(models.Model):
    _name = 'l10n_br_ciel_it_account.sped.fiscal'
    _description = 'Sped Fiscal'
    _check_company_auto = True

    company_id = fields.Many2one('res.company', 'Empresa', required=True, index=True, default=lambda self: self.env.company)
    line_icmsst_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.sped.fiscal.uf.icmsst', string='Sped Fiscal UF ICMSST', inverse_name='sped_fiscal_id' )
    line_difalfcp_ids = fields.One2many( comodel_name='l10n_br_ciel_it_account.sped.fiscal.uf.difal.fcp', string='Sped Fiscal UF DIFAL/FCP', inverse_name='sped_fiscal_id' )

    name = fields.Char( string="Protocolo", readonly=True )
    date_ini = fields.Date( string="Data Inicial", required=True )
    date_fim = fields.Date( string="Data Final", required=True )    
    arquivo = fields.Char( string="Arquivo", readonly=True )
    situacao = fields.Char( string="Situação", readonly=True )
    arquivo_sped = fields.Binary( string="Arquivo SPED", readonly=True )
    arquivo_sped_fname = fields.Char( string="Arquivo SPED", compute="_get_arquivo_sped_fname" )
    arquivo_sped_erros = fields.Binary( string="Arquivo SPED (Erros)", readonly=True )
    arquivo_sped_erros_fname = fields.Char( string="Arquivo SPED (Erros)", compute="_get_arquivo_sped_erros_fname" )

    e110_vl_tot_debitos = fields.Float( string="E110 - Saídas e prestações com débito do imposto" )
    e110_vl_aj_debitos = fields.Float( string="E110 - Ajustes a débito decorrentes do documento fiscal" )
    e110_vl_tot_aj_debitos = fields.Float( string="E110 - Ajustes a débito" )
    e110_vl_estornos_cred = fields.Float( string="E110 - Estornos de créditos" )
    e110_vl_tot_creditos = fields.Float( string="E110 - Entradas e aquisições com crédito do imposto" )
    e110_vl_aj_creditos = fields.Float( string="E110 - Ajustes a crédito decorrentes do documento fiscal " )
    e110_vl_tot_aj_creditos = fields.Float( string="E110 - Ajustes a crédito" )
    e110_vl_estornos_deb = fields.Float( string="E110 - Estornos de Débitos" )
    e110_vl_sld_credor_ant = fields.Float( string="E110 - Saldo credor do período anterior", compute="_get_e110_vl_sld_credor_ant" )
    e110_vl_sld_apurado = fields.Float( string="E110 - Saldo devedor apurado", compute="_get_e110_vl_sld_apurado" )
    e110_vl_tot_ded = fields.Float( string="E110 - Deduções" )
    e110_vl_icms_recolher = fields.Float( string="E110 - ICMS a recolher", compute="_get_e110_vl_icms_recolher" )
    e110_vl_sld_credor_transportar = fields.Float( string="E110 - Saldo credor a transportar para o período seguinte", compute="_get_e110_vl_sld_credor_transportar" )
    e110_deb_esp = fields.Float( string="E110 - Valores recolhidos ou a recolher, extra-apuração" )

    e520_vl_sd_ant_ipi = fields.Float( string="E520 - Saldo credor do IPI do período anterior", compute="_get_e520_vl_sd_ant_ipi" )
    e520_vl_deb_ipi = fields.Float( string="E520 - Valor total dos débitos" )
    e520_vl_cred_ipi = fields.Float( string="E520 - Valor total dos créditos" )
    e520_vl_od_ipi = fields.Float( string="E520 - Valor de Outros débitos" )
    e520_vl_oc_ipi = fields.Float( string="E520 - Valor de Outros créditos" )
    e520_vl_sc_ipi = fields.Float( string="E520 - Valor do saldo credor", compute="_get_e520_vl_sc_ipi" )
    e520_vl_sd_ipi = fields.Float( string="E520 - Valor do saldo devedor", compute="_get_e520_vl_sd_ipi" )
    
    h005_vl_inv = fields.Float( string="H005 - Valor do Inventario" )

    _arq = None

    def _get_e520_vl_sd_ant_ipi(self):
        for record in self:
            record_ant = record.search([('date_ini','=',record.date_ini + relativedelta(months=-1))],limit=1)
            record.e520_vl_sd_ant_ipi = record_ant.e520_vl_sc_ipi if record_ant else 0.00

    @api.depends('e520_vl_deb_ipi','e520_vl_od_ipi','e520_vl_sd_ant_ipi','e520_vl_cred_ipi','e520_vl_oc_ipi')
    def _get_e520_vl_sc_ipi(self):
        for record in self:
            e520_vl_sc_ipi = ( record.e520_vl_deb_ipi + record.e520_vl_od_ipi ) - ( record.e520_vl_sd_ant_ipi + record.e520_vl_cred_ipi + record.e520_vl_oc_ipi )
            e520_vl_sc_ipi = abs(e520_vl_sc_ipi) if e520_vl_sc_ipi < 0.00 else 0.00
            record.e520_vl_sc_ipi = e520_vl_sc_ipi

    @api.depends('e520_vl_deb_ipi','e520_vl_od_ipi','e520_vl_sd_ant_ipi','e520_vl_cred_ipi','e520_vl_oc_ipi')
    def _get_e520_vl_sd_ipi(self):
        for record in self:
            e520_vl_sd_ipi = ( record.e520_vl_deb_ipi + record.e520_vl_od_ipi ) - ( record.e520_vl_sd_ant_ipi + record.e520_vl_cred_ipi + record.e520_vl_oc_ipi )
            e520_vl_sd_ipi = e520_vl_sd_ipi if e520_vl_sd_ipi > 0.00 else 0.00
            record.e520_vl_sd_ipi = e520_vl_sd_ipi

    def _get_e110_vl_sld_credor_ant(self):
        for record in self:
            record_ant = record.search([('date_ini','=',record.date_ini + relativedelta(months=-1))],limit=1)
            record.e110_vl_sld_credor_ant = record_ant.e110_vl_sld_credor_transportar if record_ant else 0.00

    @api.depends('e110_vl_tot_debitos','e110_vl_aj_debitos','e110_vl_tot_aj_debitos','e110_vl_estornos_cred','e110_vl_tot_creditos',
                 'e110_vl_aj_creditos','e110_vl_tot_aj_creditos','e110_vl_estornos_deb','e110_vl_sld_credor_ant')
    def _get_e110_vl_sld_apurado(self):
        for record in self:
            e110_vl_sld_apurado = (record.e110_vl_tot_debitos + record.e110_vl_aj_debitos + record.e110_vl_tot_aj_debitos + record.e110_vl_estornos_cred) - \
                (record.e110_vl_tot_creditos + record.e110_vl_aj_creditos + record.e110_vl_tot_aj_creditos + record.e110_vl_estornos_deb + record.e110_vl_sld_credor_ant)
            record.e110_vl_sld_apurado = e110_vl_sld_apurado if e110_vl_sld_apurado > 0.00 else 0.00

    @api.depends('e110_vl_tot_debitos','e110_vl_aj_debitos','e110_vl_tot_aj_debitos','e110_vl_estornos_cred','e110_vl_tot_creditos',
                 'e110_vl_aj_creditos','e110_vl_tot_aj_creditos','e110_vl_estornos_deb','e110_vl_sld_credor_ant')
    def _get_e110_vl_sld_credor_transportar(self):
        for record in self:
            e110_vl_sld_credor_transportar = (record.e110_vl_tot_debitos + record.e110_vl_aj_debitos + record.e110_vl_tot_aj_debitos + record.e110_vl_estornos_cred) - \
                (record.e110_vl_tot_creditos + record.e110_vl_aj_creditos + record.e110_vl_tot_aj_creditos + record.e110_vl_estornos_deb + record.e110_vl_sld_credor_ant)
            record.e110_vl_sld_credor_transportar = abs(e110_vl_sld_credor_transportar) if e110_vl_sld_credor_transportar < 0.00 else 0.00

    @api.depends('e110_vl_sld_apurado','e110_vl_tot_ded')
    def _get_e110_vl_icms_recolher(self):
        for record in self:
            e110_vl_icms_recolher = record.e110_vl_sld_apurado - record.e110_vl_tot_ded
            record.e110_vl_icms_recolher = e110_vl_icms_recolher if e110_vl_icms_recolher > 0.00 else 0.00

    def _get_arquivo_sped_fname(self):
        for record in self:
            record.arquivo_sped_fname = "%s.TXT" % record.name

    def _get_arquivo_sped_erros_fname(self):
        for record in self:
            record.arquivo_sped_erros_fname = "%s-erros.zip" % record.name

    def gerar_sped(self):
        
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        self._arq = ArquivoDigital()

        cfop_ids_list = []
        product_ids_list = []
        partner_ids_list = []
        qtd_cod_inf = [0]

        self.enviar_registro_B001()
        self.enviar_registro_B990()

        self.enviar_registro_C001()
        self.enviar_registro_C100(product_ids_list, partner_ids_list, cfop_ids_list, qtd_cod_inf)
        self.enviar_registro_C990()
        
        self.enviar_registro_D001()
        self.enviar_registro_D100(partner_ids_list, cfop_ids_list)
        self.enviar_registro_D990()

        self.enviar_registro_E001()
        self.enviar_registro_E100()

        pos = len(self._arq._blocos['E'].registros) - 2
        self.enviar_registro_E111("PR020210")
        self.enviar_registro_E111("PR020207")
        self.enviar_registro_E110(pos)

        self.enviar_registro_E116()
        self.enviar_registro_E200()
        self.enviar_registro_E300()
        self.enviar_registro_E500()
        self.enviar_registro_E510()
        self.enviar_registro_E520()
        self.enviar_registro_E990()

        self.enviar_registro_G001()
        self.enviar_registro_G990()

        self.enviar_registro_H001()
        self.enviar_registro_H005(product_ids_list)
        self.enviar_registro_H990()

        self.enviar_registro_K001()
        self.enviar_registro_K100()
        self.enviar_registro_K200()
        self.enviar_registro_K990()

        self.enviar_registro_1001()
        self.enviar_registro_1010()
        self.enviar_registro_1990()
        
        self.enviar_registro_0000()
        self.enviar_registro_0001()
        self.enviar_registro_0002()
        self.enviar_registro_0005()
        self.enviar_registro_0100()
        self.enviar_registro_0150(partner_ids_list)
        self.enviar_registro_0175()
        self.enviar_registro_0190(product_ids_list)
        self.enviar_registro_0200(product_ids_list)
        self.enviar_registro_0205()
        self.enviar_registro_0220()
        self.enviar_registro_0300()
        self.enviar_registro_0305()
        self.enviar_registro_0400(cfop_ids_list)
        self.enviar_registro_0450(qtd_cod_inf)
        self.enviar_registro_0500()
        self.enviar_registro_0600()
        self.enviar_registro_0990()
        
        self.enviar_registro_9001()
        self.enviar_registro_9900()
        self.enviar_registro_9990()

        to_write = {}
        to_write["arquivo"] = str(uuid.uuid4())[:8] + "_%s_%s.TXT" % (_format_date(self.date_ini).replace('-',''),_format_date(self.date_fim).replace('-',''))
        to_write["name"] = to_write["arquivo"][:-4]
        to_write["situacao"] = "PROCESSADO"
        to_write["arquivo_sped"] = base64.b64encode(self._arq.getstring().encode('utf-8'))
        self.write(to_write)

    def get_icmsst_line(self, state_id):
        line_icmsst_id = self.line_icmsst_ids.filtered(lambda l: l.state_id.id == state_id.id)
        if not line_icmsst_id:
            line_icmsst_id = self.env['l10n_br_ciel_it_account.sped.fiscal.uf.icmsst'].create({'state_id': state_id.id, 'sped_fiscal_id': self.id})
            self.line_icmsst_ids += line_icmsst_id
        return line_icmsst_id

    def get_difalfcp_line(self, state_id):
        line_difalfcp_id = self.line_difalfcp_ids.filtered(lambda l: l.state_id.id == state_id.id)
        if not line_difalfcp_id:
            line_difalfcp_id = self.env['l10n_br_ciel_it_account.sped.fiscal.uf.difal.fcp'].create({'state_id': state_id.id, 'sped_fiscal_id': self.id})
            self.line_difalfcp_ids += line_difalfcp_id
        return line_difalfcp_id

    def enviar_registro_0000(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        self._arq._registro_abertura.COD_VER = '014'
        self._arq._registro_abertura.COD_FIN = '0'
        self._arq._registro_abertura.DT_INI = self.date_ini
        self._arq._registro_abertura.DT_FIN = self.date_fim
        self._arq._registro_abertura.NOME = self.env.company.l10n_br_razao_social or self.env.company.name
        self._arq._registro_abertura.CNPJ = _format_cnpj_cpf(self.env.company.l10n_br_cnpj)
        self._arq._registro_abertura.UF = self.env.company.state_id.code
        self._arq._registro_abertura.IE = self.env.company.l10n_br_ie
        self._arq._registro_abertura.COD_MUN = self.env.company.l10n_br_municipio_id.codigo_ibge
        self._arq._registro_abertura.IM = self.env.company.l10n_br_im or ""
        self._arq._registro_abertura.IND_PERFIL = 'A'
        self._arq._registro_abertura.IND_ATIV = '0'

    def enviar_registro_0001(self):
        
        self._arq._blocos['0'].registro_abertura.IND_MOV = '0'

    def enviar_registro_0002(self):
    
        registro0002 = Registro0002()

        registro0002.CLAS_ESTAB_IND = '00'

        self._arq._blocos['0'].add(registro0002)

    def enviar_registro_0005(self):
    
        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_cep(texto):
            return str(texto).replace("-","").replace(".","")

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        registro0005 = Registro0005()

        registro0005.FANTASIA = self.env.company.name or self.env.company.l10n_br_razao_social
        registro0005.CEP = _format_cep(self.env.company.zip)
        registro0005.END = self.env.company.street
        registro0005.NUM = self.env.company.l10n_br_endereco_numero
        registro0005.COMPL = self.env.company.street2
        registro0005.BAIRRO = self.env.company.l10n_br_endereco_bairro
        registro0005.FONE = _format_fone(self.env.company.phone)
        registro0005.EMAIL = self.env.company.email

        self._arq._blocos['0'].add(registro0005)

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
        registro0100.FAX = ''
        registro0100.EMAIL = 'conteles@conteles.com.br'
        registro0100.COD_MUN = '4115200'
        
        self._arq._blocos['0'].add(registro0100)

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


    def enviar_registro_0175(self):
        pass

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
            registro0200.CEST = ''

            self._arq._blocos['0'].add(registro0200)

    def enviar_registro_0205(self):
        pass

    def enviar_registro_0220(self):
        pass

    def enviar_registro_0300(self):
        pass

    def enviar_registro_0305(self):
        pass

    def enviar_registro_0400(self, cfop_ids_list):

        cfop_ids_list = list(set(cfop_ids_list))
        for cfop_id in self.env['l10n_br_ciel_it_account.cfop'].browse(cfop_ids_list):

            if not cfop_id.codigo_cfop:
                continue

            registro0400 = Registro0400()

            registro0400.COD_NAT = cfop_id.codigo_cfop
            registro0400.DESCR_NAT = cfop_id.name

            self._arq._blocos['0'].add(registro0400)

    def enviar_registro_0450(self, qtd_cod_inf):

        for i in range(1,qtd_cod_inf[0]+1,1):
            registro0450 = Registro0450()
        
            registro0450.COD_INF = str(i)
            registro0450.TXT = '%%TEXTO%%'

            self._arq._blocos['0'].add(registro0450)

    def enviar_registro_0500(self):
        
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        for account_id in self.env['account.account'].search([('deprecated','=',False)]):

            group_id = account_id.group_id
            nivel = 1
            while group_id.parent_id:
                nivel += 1
                group_id = group_id.parent_id
            
            dt_alt_1 = account_id.write_date.date()
            if dt_alt_1 > self.date_fim:
                dt_alt_1 = self.date_fim

            registro0500 = Registro0500()

            registro0500.DT_ALT = dt_alt_1
            registro0500.COD_NAT_CC = "0"+str(group_id.code_prefix)
            registro0500.IND_CTA = 'A'
            registro0500.NIVEL = str(nivel)
            registro0500.COD_CTA = account_id.code
            registro0500.NOME_CTA = account_id.name

            self._arq._blocos['0'].add(registro0500)

    def enviar_registro_0600(self):
        pass

    def enviar_registro_0990(self):
            
        self._arq._blocos['0'].registro_encerramento.QTD_LIN_0 = len(self._arq._blocos['0'].registros) +1

    def enviar_registro_B001(self):
    
        self._arq._blocos['B'].registro_abertura.IND_MOV = '1'
    
    def enviar_registro_B990(self):
            
        self._arq._blocos['B'].registro_encerramento.QTD_LIN_B = len(self._arq._blocos['B'].registros)

    def enviar_registro_C001(self):

        self._arq._blocos['C'].registro_abertura.IND_MOV = '0'
    
    def enviar_registro_C100(self, product_ids_list, partner_ids_list, cfop_ids_list, qtd_cod_inf):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        tx2_items = []

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
            
            registroC100.COD_SIT = ""
            if move_id.l10n_br_chave_nf and _format_cnpj_cpf(move_id.company_id.l10n_br_cnpj) in move_id.l10n_br_chave_nf:
                registroC100.IND_EMIT = '0'

                if move_id.l10n_br_cstat_nf in ['301','302','303']:
                    registroC100.COD_SIT = '04'
    
                elif move_id.l10n_br_cstat_nf == '135' and move_id.state == 'cancel':
                    registroC100.COD_SIT = '02'

                elif move_id.l10n_br_cstat_nf in ['100','135','690','501'] and move_id.state == 'posted':

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
                self.enviar_registro_C110(move_id, qtd_cod_inf)
                self.enviar_registro_C113(move_id)
                if not registroC100.IND_EMIT == '0':
                    self.enviar_registro_C170(move_id, product_ids_list, cfop_ids_list)
                if registroC100.COD_MOD in ["01", "1B", "04", "55"]:
                    self.enviar_registro_C190(move_id)

    def enviar_registro_C110(self, move_id, qtd_cod_inf):
    
        def _format_obs(texto):
            return str(texto).replace('"',' ').replace("¬"," ").replace("§","").replace("°","").replace("º","").replace("ª","").replace("\n"," ").replace("&","E").replace("%","")

        spedtx2 = ""
        if move_id.l10n_br_informacao_fiscal:

            n = 255 # chunk length
            l10n_br_informacao_fiscal = _format_obs(move_id.l10n_br_informacao_fiscal)
            chunks = [l10n_br_informacao_fiscal[i:i+n] for i in range(0, len(l10n_br_informacao_fiscal), n)]
            for cod_inf, txt_compl in enumerate(chunks):

                registroC110 = RegistroC110()

                qtd_cod_inf[0] = max([1,cod_inf+1,qtd_cod_inf[0]])
                registroC110.COD_INF = str(cod_inf+1)
                registroC110.TXT_COMPL = txt_compl

                self._arq._blocos['C'].add(registroC110)
                

        elif len(move_id.referencia_ids) > 0:
            
            registroC110 = RegistroC110()
            
            registroC110.COD_INF = '1'
            registroC110.TXT_COMPL = _format_obs(",".join([invoice_ref.l10n_br_chave_nf for invoice_ref in move_id.referencia_ids]))
            
            self._arq._blocos['C'].add(registroC110)

    def enviar_registro_C113(self, move_id):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        for invoice_ref in move_id.referencia_ids:

            move_ref_id = self.env['account.move'].search([('l10n_br_chave_nf','=',invoice_ref.l10n_br_chave_nf)],limit=1)
            if move_ref_id:
                registroC113 = RegistroC113()

                registroC113.IND_OPER = str(TIPO_NF[move_ref_id.type])

                if move_ref_id.l10n_br_chave_nf and _format_cnpj_cpf(move_ref_id.company_id.l10n_br_cnpj) in move_ref_id.l10n_br_chave_nf:
                    registroC113.IND_EMIT = '0'
                else:
                    registroC113.IND_EMIT = '1'

                registroC113.COD_PART = str(move_ref_id.partner_id.id)
                registroC113.COD_MOD = move_ref_id.l10n_br_tipo_documento
                registroC113.SER = move_ref_id.l10n_br_serie_nf
                registroC113.SUB = ""
                registroC113.NUM_DOC = str(move_ref_id.l10n_br_numero_nf)
                registroC113.DT_DOC = move_ref_id.invoice_date
            
                registroC113.CHV_DOCE = invoice_ref.l10n_br_chave_nf
                
                self._arq._blocos['C'].add(registroC113)

    def enviar_registro_C170(self, move_id, product_ids_list, cfop_ids_list):

        invoice_line_ids = move_id.invoice_line_ids.filtered(lambda l: not l.display_type)
        for nItem, invoice_line in enumerate(sorted(invoice_line_ids, key=lambda l: l[0].sequence)):
            registroC170 = RegistroC170()

            registroC170.NUM_ITEM = nItem + 1 
            
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
            registroC170.ALIQ_ICMS = invoice_line.l10n_br_icms_aliquota or 0.00
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
            registroC170.VL_ABAT_NT = 0.00

            self._arq._blocos['C'].add(registroC170)

    def enviar_registro_C190(self, move_id):

        grouper = itemgetter("l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota")
        invoice_line_ids = [dict(zip(["l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota", "l10n_br_prod_valor", "l10n_br_frete", "l10n_br_seguro", "l10n_br_despesas_acessorias", "l10n_br_icmsst_valor", "l10n_br_icmsst_substituto_valor", "l10n_br_icmsst_retido_valor", "l10n_br_icmsst_valor_outros", "l10n_br_fcp_st_valor", "l10n_br_ipi_valor", "l10n_br_ipi_valor_isento", "l10n_br_ipi_valor_outros", "l10n_br_icms_base", "l10n_br_icms_valor", "l10n_br_icmsst_base", "l10n_br_icms_reducao_base","l10n_br_desc_valor"], [line_id.l10n_br_icms_cst, line_id.l10n_br_cfop_id.codigo_cfop, line_id.l10n_br_icms_aliquota, line_id.l10n_br_prod_valor, line_id.l10n_br_frete, line_id.l10n_br_seguro, line_id.l10n_br_despesas_acessorias, line_id.l10n_br_icmsst_valor, line_id.l10n_br_icmsst_substituto_valor, line_id.l10n_br_icmsst_retido_valor, line_id.l10n_br_icmsst_valor_outros, line_id.l10n_br_fcp_st_valor, line_id.l10n_br_ipi_valor, line_id.l10n_br_ipi_valor_isento, line_id.l10n_br_ipi_valor_outros, line_id.l10n_br_icms_base, line_id.l10n_br_icms_valor + (line_id.l10n_br_icms_valor_outros if TIPO_NF[line_id.move_id.type] == 0  and line_id.l10n_br_icms_cst == '90' else 0.00), line_id.l10n_br_icmsst_base, line_id.l10n_br_icms_reducao_base, line_id.l10n_br_desc_valor])) for line_id in move_id.invoice_line_ids.filtered(lambda l: not l.display_type)]

        # Fix null values to prevent error
        # TypeError: '<' not supported between instances of 'bool' and 'str'
        for idx, item in enumerate(invoice_line_ids):
            invoice_line_ids[idx]["l10n_br_icms_cst"] = invoice_line_ids[idx]["l10n_br_icms_cst"] or ""
            invoice_line_ids[idx]["l10n_br_cfop_id"] = invoice_line_ids[idx]["l10n_br_cfop_id"] or ""
        
        for key, grp in groupby(sorted(invoice_line_ids, key = grouper), grouper):
            
            invoice_lines_list = list(grp)

            registroC190 = RegistroC190()

            key_vals = dict(zip(["l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota"], key))
            
            registroC190.CST_ICMS = str(key_vals['l10n_br_icms_cst'] or "").zfill(3)
            registroC190.CFOP = key_vals['l10n_br_cfop_id']
            registroC190.ALIQ_ICMS = key_vals['l10n_br_icms_aliquota'] or 0.00

            registroC190.VL_OPR = sum(item["l10n_br_prod_valor"]+item["l10n_br_frete"]+item["l10n_br_seguro"]+item["l10n_br_despesas_acessorias"]+item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_valor_outros"]+item["l10n_br_fcp_st_valor"]+item["l10n_br_ipi_valor"]+item["l10n_br_ipi_valor_outros"]+item["l10n_br_ipi_valor_isento"]-item["l10n_br_desc_valor"] for item in invoice_lines_list)
            registroC190.VL_BC_ICMS = sum(item["l10n_br_icms_base"] for item in invoice_lines_list)
            if TIPO_NF[move_id.type] == 1:
                self.e110_vl_tot_debitos += sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)
            else:
                self.e110_vl_tot_creditos += sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)
            registroC190.VL_ICMS = sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)
            registroC190.VL_BC_ICMS_ST = sum(item["l10n_br_icmsst_base"] for item in invoice_lines_list)

            if sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list) > 0.00:
                if TIPO_NF[move_id.type] == 0:
                    if key_vals['l10n_br_cfop_id'] in ['1410', '1411', '1414', '1415', '1660', '1661', '1662', '2410', '2411', '2414', '2415', '2660', '2661', '2662']:
                        self.get_icmsst_line(move_id.partner_id.state_id).e210_vl_devol_st += sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list)
                    elif key_vals['l10n_br_cfop_id'] in ['1603', '2603']:
                        self.get_icmsst_line(move_id.partner_id.state_id).e210_vl_ressarc_st += sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list)
                    else:
                        self.get_icmsst_line(move_id.partner_id.state_id).e210_vl_out_cred_st += sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list)
                else:
                    self.get_icmsst_line(move_id.partner_id.state_id).e210_vl_retencao_st += sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list)
                    
            registroC190.VL_ICMS_ST = sum(item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_substituto_valor"]+item["l10n_br_icmsst_retido_valor"] for item in invoice_lines_list)

            VL_RED_BC_9 = 0.00
            for item in invoice_lines_list:
                if ( 1 - ( item["l10n_br_icms_reducao_base"] / 100.00 ) ) > 0.00:
                    VL_RED_BC_9 += ( item['l10n_br_icms_base'] / ( 1 - ( item["l10n_br_icms_reducao_base"] / 100.00 ) ) ) - item['l10n_br_icms_base']
            registroC190.VL_RED_BC = VL_RED_BC_9

            registroC190.VL_IPI = sum(item["l10n_br_ipi_valor"] for item in invoice_lines_list)
            registroC190.COD_OBS = ''

            self._arq._blocos['C'].add(registroC190)

    def enviar_registro_C990(self):
            
        self._arq._blocos['C'].registro_encerramento.QTD_LIN_C = len(self._arq._blocos['C'].registros)

    def enviar_registro_D001(self):
    
        self._arq._blocos['D'].registro_abertura.IND_MOV = '0'
    
    def enviar_registro_D100(self, partner_ids_list, cfop_ids_list):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')
        
        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        l10n_br_tipo_documentos_sel = ["06","07","08","8B","09","10","11","26","27","57","63","67"]

        move_ids = self.env['account.move'].search([('l10n_br_numero_nf','>',0),('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('l10n_br_tipo_documento','in',l10n_br_tipo_documentos_sel),('state','!=','draft')])
        
        for move_id in move_ids:
            
            if move_id.state == 'cancel' and not move_id.l10n_br_chave_nf:
                continue

            registroD100 = RegistroD100()

            registroD100.IND_OPER = str(TIPO_NF[move_id.type])
            
            registroD100.COD_SIT = ""
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
                registroD100.COD_MUN_ORIG = move_id.l10n_br_municipio_inicio_id.codigo_ibge or ""
                registroD100.COD_MUN_DEST = move_id.l10n_br_municipio_fim_id.codigo_ibge or ""

            self._arq._blocos['D'].add(registroD100)

            if not registroD100.COD_SIT in ['02','03','04']:
                self.enviar_registro_D190(move_id, cfop_ids_list)

    def enviar_registro_D190(self, move_id, cfop_ids_list):
    
        grouper = itemgetter("l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota")
        invoice_line_ids = [dict(zip(["l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota", "l10n_br_prod_valor", "l10n_br_frete", "l10n_br_seguro", "l10n_br_despesas_acessorias", "l10n_br_icmsst_valor", "l10n_br_icmsst_substituto_valor", "l10n_br_icmsst_retido_valor", "l10n_br_icmsst_valor_outros", "l10n_br_fcp_st_valor", "l10n_br_ipi_valor", "l10n_br_ipi_valor_isento", "l10n_br_ipi_valor_outros", "l10n_br_icms_base", "l10n_br_icms_valor", "l10n_br_icmsst_base", "l10n_br_icms_reducao_base","l10n_br_desc_valor"], [line_id.l10n_br_icms_cst, line_id.l10n_br_cfop_id.codigo_cfop, line_id.l10n_br_icms_aliquota, line_id.l10n_br_prod_valor, line_id.l10n_br_frete, line_id.l10n_br_seguro, line_id.l10n_br_despesas_acessorias, line_id.l10n_br_icmsst_valor, line_id.l10n_br_icmsst_substituto_valor, line_id.l10n_br_icmsst_retido_valor, line_id.l10n_br_icmsst_valor_outros, line_id.l10n_br_fcp_st_valor, line_id.l10n_br_ipi_valor, line_id.l10n_br_ipi_valor_isento, line_id.l10n_br_ipi_valor_outros, line_id.l10n_br_icms_base, line_id.l10n_br_icms_valor + (line_id.l10n_br_icms_valor_outros if TIPO_NF[line_id.move_id.type] == 0 and line_id.l10n_br_icms_cst == '90' else 0.00), line_id.l10n_br_icmsst_base, line_id.l10n_br_icms_reducao_base, line_id.l10n_br_desc_valor])) for line_id in move_id.invoice_line_ids.filtered(lambda l: not l.display_type)]
        for key, grp in groupby(sorted(invoice_line_ids, key = grouper), grouper):

            registroD190 = RegistroD190()
            invoice_lines_list = list(grp)

            key_vals = dict(zip(["l10n_br_icms_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota"], key))

            registroD190.CST_ICMS = str(key_vals['l10n_br_icms_cst'] or "").zfill(3)
            
            registroD190.CFOP = key_vals['l10n_br_cfop_id']

            registroD190.ALIQ_ICMS = key_vals['l10n_br_icms_aliquota'] or 0.00

            registroD190.VL_OPR = sum(item["l10n_br_prod_valor"]+item["l10n_br_frete"]+item["l10n_br_seguro"]+item["l10n_br_despesas_acessorias"]+item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_valor_outros"]+item["l10n_br_fcp_st_valor"]+item["l10n_br_ipi_valor"]+item["l10n_br_ipi_valor_outros"]+item["l10n_br_ipi_valor_isento"]-item["l10n_br_desc_valor"] for item in invoice_lines_list)
            registroD190.VL_BC_ICMS = sum(item["l10n_br_icms_base"] for item in invoice_lines_list)
            if TIPO_NF[move_id.type] == 1:
                self.e110_vl_tot_debitos += sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)
            else:
                self.e110_vl_tot_creditos += sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)
            registroD190.VL_ICMS = sum(item["l10n_br_icms_valor"] for item in invoice_lines_list)

            VL_RED_BC_7 = 0.00
            for item in invoice_lines_list:
                if ( 1 - ( item["l10n_br_icms_reducao_base"] / 100.00 ) ) > 0.00:
                    VL_RED_BC_7 += ( item['l10n_br_icms_base'] / ( 1 - ( item["l10n_br_icms_reducao_base"] / 100.00 ) ) ) - item['l10n_br_icms_base']
            registroD190.VL_RED_BC = VL_RED_BC_7

            registroD190.COD_OBS = ''

            self._arq._blocos['D'].add(registroD190)

    def enviar_registro_D990(self):

        self._arq._blocos['D'].registro_encerramento.QTD_LIN_D = len(self._arq._blocos['D'].registros)

    def enviar_registro_E001(self):
        
        self._arq._blocos['E'].registro_abertura.IND_MOV = '0'
    
    def enviar_registro_E100(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        registroE100 = RegistroE100()

        registroE100.DT_INI = self.date_ini
        registroE100.DT_FIN = self.date_fim

        self._arq._blocos['E'].add(registroE100)

    def enviar_registro_E110(self, pos):

        registroE110 = RegistroE110()

        registroE110.VL_TOT_DEBITOS = self.e110_vl_tot_debitos
        registroE110.VL_AJ_DEBITOS = self.e110_vl_aj_debitos
        registroE110.VL_TOT_AJ_DEBITOS = self.e110_vl_tot_aj_debitos
        registroE110.VL_ESTORNOS_CRED = self.e110_vl_estornos_cred
        registroE110.VL_TOT_CREDITOS = self.e110_vl_tot_creditos
        registroE110.VL_AJ_CREDITOS = self.e110_vl_aj_creditos
        registroE110.VL_TOT_AJ_CREDITOS = self.e110_vl_tot_aj_creditos
        registroE110.VL_ESTORNOS_DEB = self.e110_vl_estornos_deb
        registroE110.VL_SLD_CREDOR_ANT = self.e110_vl_sld_credor_ant
        registroE110.VL_SLD_APURADO = self.e110_vl_sld_apurado
        registroE110.VL_TOT_DED = self.e110_vl_tot_ded
        registroE110.VL_ICMS_RECOLHER = self.e110_vl_icms_recolher
        registroE110.VL_SLD_CREDOR_TRANSPORTAR = self.e110_vl_sld_credor_transportar
        registroE110.DEB_ESP = self.e110_deb_esp

        self._arq._blocos['E'].add(registroE110, pos)

    def enviar_registro_E111(self, COD_AJ_APUR):

        DESCR_COMPL_AJ = {}
        DESCR_COMPL_AJ["PR020210"] = "Crédito decorrente de recuperação do imposto por substituição tributária conforme § 11 do art. 25 do RICMS/2017"
        DESCR_COMPL_AJ["PR020207"] = "Crédito de aquisições de contribuintes do Simples Nacional, conforme § 16 do art. 26 do RICMS/2017"

        registroE111 = RegistroE111()

        registroE111.COD_AJ_APUR = COD_AJ_APUR
        registroE111.DESCR_COMPL_AJ = DESCR_COMPL_AJ[COD_AJ_APUR]
        
        pos = len(self._arq._blocos['E'].registros) - 2
        
        VL_AJ_APUR = self.enviar_registro_E113(COD_AJ_APUR)
        
        if VL_AJ_APUR > 0.00:

            registroE111.VL_AJ_APUR = VL_AJ_APUR

            if COD_AJ_APUR[2:4] == "00":
                self.e110_vl_tot_aj_debitos += VL_AJ_APUR
            elif COD_AJ_APUR[2:4] == "01":
                self.e110_vl_estornos_cred += VL_AJ_APUR
            elif COD_AJ_APUR[2:4] == "02":
                self.e110_vl_tot_aj_creditos += VL_AJ_APUR
            elif COD_AJ_APUR[2:4] == "03":
                self.e110_vl_estornos_deb += VL_AJ_APUR
            elif COD_AJ_APUR[2:4] == "04":
                self.e110_vl_tot_ded += VL_AJ_APUR
            elif COD_AJ_APUR[2:4] == "05":
                self.e110_deb_esp += VL_AJ_APUR

        self._arq._blocos['E'].add(registroE111, pos)

    def enviar_registro_E113(self, COD_AJ_APUR):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        l10n_br_tipo_documentos_sel = ["01","1B","04","55"]
        spedtx2 = ""
        
        domain = [('l10n_br_numero_nf','>',0),('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('l10n_br_tipo_documento','in',l10n_br_tipo_documentos_sel),('state','!=','draft'),('state','!=','cancel')]
        if COD_AJ_APUR == 'PR020207':
            domain_sn = [('simples_nacional','=',True)]
            domain = expression.AND([domain,domain_sn])

        move_ids = self.env['account.move'].search(domain)

        VL_AJ_APUR = 0.00
        for move_id in move_ids:

            if move_id.l10n_br_chave_nf and _format_cnpj_cpf(move_id.company_id.l10n_br_cnpj) in move_id.l10n_br_chave_nf:
                    continue

            invoice_line_ids = move_id.invoice_line_ids.filtered(lambda l: not l.display_type)
            if COD_AJ_APUR == 'PR020207':
                invoice_line_ids = invoice_line_ids.filtered(lambda l: l.l10n_br_icms_valor > 0.00 or (l.l10n_br_icms_cst == '90' and l.l10n_br_icms_valor_outros > 0.00))

            if COD_AJ_APUR == 'PR020210':
                invoice_line_ids = invoice_line_ids.filtered(lambda l: l.l10n_br_icmsst_valor > 0.00 or l.l10n_br_icmsst_substituto_valor > 0.00 or l.l10n_br_icmsst_retido_valor > 0.00)

            for invoice_line in sorted(invoice_line_ids, key=lambda l: l[0].sequence):

                registroE113 = RegistroE113()

                registroE113.COD_PART = str(move_id.partner_id.id)
                registroE113.COD_MOD = move_id.l10n_br_tipo_documento
                registroE113.SER = move_id.l10n_br_serie_nf
                registroE113.SUB = ""
                registroE113.NUM_DOC = str(move_id.l10n_br_numero_nf)

                registroE113.DT_DOC = move_id.invoice_date

                registroE113.COD_ITEM = invoice_line.product_id.default_code or ""

                if COD_AJ_APUR == 'PR020207':
                    VL_AJ_APUR += invoice_line.l10n_br_icms_valor + invoice_line.l10n_br_icms_valor_outros
                    registroE113.VL_AJ_ITEM = invoice_line.l10n_br_icms_valor + invoice_line.l10n_br_icms_valor_outros

                if COD_AJ_APUR == 'PR020210':
                    VL_AJ_APUR += invoice_line.l10n_br_icmsst_valor + invoice_line.l10n_br_icmsst_substituto_valor + invoice_line.l10n_br_icmsst_retido_valor
                    registroE113.VL_AJ_ITEM = invoice_line.l10n_br_icmsst_valor + invoice_line.l10n_br_icmsst_substituto_valor + invoice_line.l10n_br_icmsst_retido_valor

                registroE113.CHV_DOCE = move_id.l10n_br_chave_nf

                self._arq._blocos['E'].add(registroE113)

        return VL_AJ_APUR

    def enviar_registro_E116(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        def _format_mesref(date):
            return datetime.strftime(date,'%m%Y')

        registroE116 = RegistroE116()

        registroE116.COD_OR = "000"
        registroE116.VL_OR = self.e110_vl_icms_recolher
        registroE116.DT_VCTO = self.date_ini.replace(day=12)
        registroE116.COD_REC = "1015"
        registroE116.NUM_PROC = ""
        registroE116.IND_PROC = ""
        registroE116.PROC = ""
        registroE116.TXT_COMPL = ""
        registroE116.MES_REF = _format_mesref(self.date_ini + relativedelta(months=-1))

        self._arq._blocos['E'].add(registroE116)

    def enviar_registro_E200(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        for line_icmsst_id in self.line_icmsst_ids:
            
            registroE200 = RegistroE200()
            registroE200.UF = line_icmsst_id.state_id.code
            registroE200.DT_INI = self.date_ini
            registroE200.DT_FIN = self.date_fim

            self._arq._blocos['E'].add(registroE200)

            self.enviar_registro_E210(line_icmsst_id)
            
    def enviar_registro_E210(self, line_icmsst_id):
    
        registroE210 = RegistroE210()

        registroE210.IND_MOV_ST = "1"
        registroE210.VL_SLD_CRED_ANT_ST = line_icmsst_id.e210_vl_sld_cred_ant_st
        registroE210.VL_DEVOL_ST = line_icmsst_id.e210_vl_devol_st
        registroE210.VL_RESSARC_ST = line_icmsst_id.e210_vl_ressarc_st
        registroE210.VL_OUT_CRED_ST = line_icmsst_id.e210_vl_out_cred_st
        registroE210.VL_AJ_CREDITOS_ST = line_icmsst_id.e210_vl_aj_creditos_st
        registroE210.VL_RETENCAO_ST = line_icmsst_id.e210_vl_retencao_st
        registroE210.VL_OUT_DEB_ST = line_icmsst_id.e210_vl_out_deb_st
        registroE210.VL_AJ_DEBITOS_ST = line_icmsst_id.e210_vl_aj_debitos_st
        registroE210.VL_SLD_DEV_ANT_ST = line_icmsst_id.e210_vl_sld_dev_ant_st
        registroE210.VL_DEDUCOES_ST = line_icmsst_id.e210_vl_deducoes_st
        registroE210.VL_ICMS_RECOL_ST = line_icmsst_id.e210_vl_icms_recol_st
        registroE210.VL_SLD_CRED_ST_TRANSPORTAR = line_icmsst_id.e210_vl_sld_cred_st_transportar
        registroE210.DEB_ESP_ST = line_icmsst_id.e210_deb_esp_st

        self._arq._blocos['E'].add(registroE210)
        
        if line_icmsst_id.e210_vl_icms_recol_st > 0.00:
            self.enviar_registro_E250(line_icmsst_id)

    def enviar_registro_E250(self, line_icmsst_id):
    
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        def _format_mesref(date):
            return datetime.strftime(date,'%m%Y')

        registroE250 = RegistroE250()

        registroE250.COD_OR = "999" if line_icmsst_id.state_id.id != self.env.company.state_id.id else "002"
        registroE250.VL_OR = line_icmsst_id.e210_vl_icms_recol_st
        registroE250.DT_VCTO = self.date_ini.replace(day=12)
        registroE250.COD_REC = "100099"
        registroE250.NUM_PROC = ""
        registroE250.IND_PROC = ""
        registroE250.PROC = ""
        registroE250.TXT_COMPL = ""
        registroE250.MES_REF = _format_mesref(self.date_ini + relativedelta(months=-1))

        self._arq._blocos['E'].add(registroE250)

    def enviar_registro_E300(self):
    
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        for line_difalfcp_id in self.line_difalfcp_ids:
            
            registroE300 = RegistroE300()
            registroE300.UF = line_difalfcp_id.state_id.code
            registroE300.DT_INI = self.date_ini
            registroE300.DT_FIN = self.date_fim

            self._arq._blocos['E'].add(registroE300)

            self.enviar_registro_E310(line_difalfcp_id)
            
    def enviar_registro_E310(self, line_difalfcp_id):
    
        registroE310 = RegistroE300()

        registroE310.IND_MOV_FCP_DIFA = "1"

        registroE310.VL_SLD_CRED_ANT_DIFAL = 0.00
        registroE310.VL_TOT_DEBITOS_DIFAL = 0.00
        registroE310.VL_OUT_DEB_DIFAL = 0.00
        registroE310.VL_TOT_CREDITOS_DIFAL = 0.00
        registroE310.VL_OUT_CRED_DIFAL = 0.00
        registroE310.VL_SLD_DEV_ANT_DIFAL = 0.00
        registroE310.VL_DEDUÇÕES_DIFAL = 0.00
        registroE310.VL_RECOL_DIFAL = 0.00
        registroE310.VL_SLD_CRED_TRANSPORTAR_DIFAL = 0.00
        registroE310.DEB_ESP_DIFAL = 0.00

        registroE310.VL_SLD_CRED_ANT_FCP = 0.00
        registroE310.VL_TOT_DEB_FCP = 0.00
        registroE310.VL_OUT_DEB_FCP = 0.00
        registroE310.VL_TOT_CRED_FCP = 0.00
        registroE310.VL_OUT_CRED_FCP = 0.00
        registroE310.VL_SLD_DEV_ANT_FCP = 0.00
        registroE310.VL_DEDUÇÕES_FCP = 0.00
        registroE310.VL_RECOL_FCP = 0.00
        registroE310.VL_SLD_CRED_TRANSPORTAR_FCP = 0.00
        registroE310.DEB_ESP_FCP = 0.00

        self._arq._blocos['E'].add(registroE310)

        if line_difalfcp_id.e210_vl_icms_recol_st > 0.00:
            self.enviar_registro_E316(line_icmsst_id)

    def enviar_registro_E316(self, line_icmsst_id):
    
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        def _format_mesref(date):
            return datetime.strftime(date,'%m%Y')

        registroE316 = RegistroE316()

        registroE316.COD_OR = "999" if line_icmsst_id.state_id.id != self.env.company.state_id.id else "002"
        registroE316.VL_OR = line_icmsst_id.e210_vl_icms_recol_st
        registroE316.DT_VCTO = self.date_ini.replace(day=12)
        registroE316.COD_REC = "100099"
        registroE316.NUM_PROC = ""
        registroE316.IND_PROC = ""
        registroE316.PROC = ""
        registroE316.TXT_COMPL = ""
        registroE316.MES_REF = _format_mesref(self.date_ini + relativedelta(months=-1))

        self._arq._blocos['E'].add(registroE316)

    def enviar_registro_1001(self):
        
        self._arq._blocos['1'].registro_abertura.IND_MOV = '0'
    
    def enviar_registro_1010(self):

        registro1010 = Registro1010()

        registro1010.IND_EXP = 'N'
        registro1010.IND_CCRF = 'N'
        registro1010.IND_COMB = 'N'
        registro1010.IND_USINA = 'N'
        registro1010.IND_VA = 'N'
        registro1010.IND_EE = 'N'
        registro1010.IND_CART = 'N'
        registro1010.IND_FORM = 'N'
        registro1010.IND_AER = 'N'
        registro1010.IND_GIAF1 = 'N'
        registro1010.IND_GIAF3 = 'N'
        registro1010.IND_GIAF4 = 'N'
        registro1010.IND_REST_RESSARC_COMPL_ICMS = 'N'

        self._arq._blocos['1'].add(registro1010)

    def enviar_registro_1990(self):
        
        self._arq._blocos['1'].registro_encerramento.QTD_LIN_1 = len(self._arq._blocos['1'].registros)

    def enviar_registro_E500(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        registroE500 = RegistroE500()

        registroE500.IND_APUR = '0'
        registroE500.DT_INI = self.date_ini
        registroE500.DT_FIN = self.date_fim

        self._arq._blocos['E'].add(registroE500)
    
    def enviar_registro_E510(self):

        def _format_cnpj_cpf(cnpj_cpf):
            if cnpj_cpf:
                return cnpj_cpf.replace("/","").replace("-","").replace(".","")
            else:
                return ""

        data_ini = self.date_ini.strftime(DEFAULT_SERVER_DATE_FORMAT)
        data_fim = self.date_fim.strftime(DEFAULT_SERVER_DATE_FORMAT)
        types_sel = ["out_invoice","in_refund","out_refund","in_invoice"]
        l10n_br_tipo_documentos_sel = ["01","1B","04","55"]
        
        move_ids = self.env['account.move'].search([('l10n_br_numero_nf','>',0),('date','>=',data_ini),('date','<=',data_fim),('type','in',types_sel),('l10n_br_tipo_documento','in',l10n_br_tipo_documentos_sel),('state','!=','draft'),('state','!=','cancel')])
        move_ids_filtered = []
        for move_id in move_ids:

            COD_SIT = ""
            if move_id.l10n_br_chave_nf and _format_cnpj_cpf(move_id.company_id.l10n_br_cnpj) in move_id.l10n_br_chave_nf:
                if move_id.l10n_br_cstat_nf in ['301','302','303']:
                    COD_SIT = '04'
    
                elif move_id.l10n_br_cstat_nf == '135' and move_id.state == 'cancel':
                    COD_SIT = '02'

                elif move_id.l10n_br_cstat_nf in ['100','135','690','501'] and move_id.state == 'posted':

                    if move_id.l10n_br_operacao_id.l10n_br_finalidade == '2':
                        COD_SIT = '06'

                    else:
                        COD_SIT = '00'

            else:
                if move_id.l10n_br_chave_nf and move_id.l10n_br_chave_nf[6:20] != _format_cnpj_cpf(move_id.partner_id.l10n_br_cnpj):
                    COD_SIT = '08'
                else:
                    COD_SIT = '00'
        
            if not COD_SIT in ['02','03','04']:
                move_ids_filtered.append(move_id.id)
                

        grouper = itemgetter("l10n_br_ipi_cst", "l10n_br_cfop_id")
        invoice_lines_mapped = self.env['account.move'].browse(move_ids_filtered).mapped('invoice_line_ids').filtered(lambda l: (not l.display_type) and l.l10n_br_ipi_valor > 0.00)
        invoice_line_ids = [dict(zip(["l10n_br_ipi_cst", "l10n_br_cfop_id", "l10n_br_icms_aliquota", "l10n_br_prod_valor", "l10n_br_frete", "l10n_br_seguro", "l10n_br_despesas_acessorias", "l10n_br_icmsst_valor", "l10n_br_icmsst_substituto_valor", "l10n_br_icmsst_retido_valor", "l10n_br_icmsst_valor_outros", "l10n_br_fcp_st_valor", "l10n_br_ipi_base", "l10n_br_ipi_valor", "l10n_br_ipi_valor_isento", "l10n_br_ipi_valor_outros", "l10n_br_icms_base", "l10n_br_icms_valor", "l10n_br_icmsst_base", "l10n_br_icms_reducao_base","l10n_br_desc_valor"], [line_id.l10n_br_ipi_cst, line_id.l10n_br_cfop_id.codigo_cfop or "", line_id.l10n_br_icms_aliquota, line_id.l10n_br_prod_valor, line_id.l10n_br_frete, line_id.l10n_br_seguro, line_id.l10n_br_despesas_acessorias, line_id.l10n_br_icmsst_valor, line_id.l10n_br_icmsst_substituto_valor, line_id.l10n_br_icmsst_retido_valor, line_id.l10n_br_icmsst_valor_outros, line_id.l10n_br_fcp_st_valor, line_id.l10n_br_ipi_base, line_id.l10n_br_ipi_valor, line_id.l10n_br_ipi_valor_isento, line_id.l10n_br_ipi_valor_outros, line_id.l10n_br_icms_base, line_id.l10n_br_icms_valor + (line_id.l10n_br_icms_valor_outros if TIPO_NF[line_id.move_id.type] == 0  and line_id.l10n_br_icms_cst == '90' else 0.00), line_id.l10n_br_icmsst_base, line_id.l10n_br_icms_reducao_base, line_id.l10n_br_desc_valor])) for line_id in invoice_lines_mapped]
        for key, grp in groupby(sorted(invoice_line_ids, key = grouper), grouper):
            
            invoice_lines_list = list(grp)
            
            registroE510 = RegistroE510()

            key_vals = dict(zip(["l10n_br_ipi_cst", "l10n_br_cfop_id"], key))
            
            registroE510.CFOP = key_vals['l10n_br_cfop_id']
            registroE510.CST_IPI = key_vals['l10n_br_ipi_cst']
            registroE510.VL_CONT_IPI = sum(item["l10n_br_prod_valor"]+item["l10n_br_frete"]+item["l10n_br_seguro"]+item["l10n_br_despesas_acessorias"]+item["l10n_br_icmsst_valor"]+item["l10n_br_icmsst_valor_outros"]+item["l10n_br_fcp_st_valor"]+item["l10n_br_ipi_valor"]+item["l10n_br_ipi_valor_outros"]+item["l10n_br_ipi_valor_isento"]-item["l10n_br_desc_valor"] for item in invoice_lines_list)
            registroE510.VL_BC_IPI = sum(item["l10n_br_ipi_base"] for item in invoice_lines_list)
            registroE510.VL_IPI = sum(item["l10n_br_ipi_valor"] for item in invoice_lines_list)
            
            if key_vals['l10n_br_cfop_id'][0:1] in ['5','6']:
                self.e520_vl_deb_ipi += sum(item["l10n_br_ipi_valor"] for item in invoice_lines_list)

            if key_vals['l10n_br_cfop_id'][0:1] in ['1','2']:
                self.e520_vl_cred_ipi += sum(item["l10n_br_ipi_valor"] for item in invoice_lines_list)

            self._arq._blocos['E'].add(registroE510)

    def enviar_registro_E520(self):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        registroE520 = RegistroE520()

        registroE520.VL_SD_ANT_IPI = self.e520_vl_sd_ant_ipi
        registroE520.VL_DEB_IPI = self.e520_vl_deb_ipi
        registroE520.VL_CRED_IPI = self.e520_vl_cred_ipi
        registroE520.VL_OD_IPI = self.e520_vl_od_ipi
        registroE520.VL_OC_IPI = self.e520_vl_oc_ipi
        registroE520.VL_SC_IPI = self.e520_vl_sc_ipi
        registroE520.VL_SD_IPI = self.e520_vl_sd_ipi

        self._arq._blocos['E'].add(registroE520)
    
    def enviar_registro_E990(self):
    
        self._arq._blocos['E'].registro_encerramento.QTD_LIN_E = len(self._arq._blocos['E'].registros)

    def enviar_registro_G001(self):
        
        self._arq._blocos['G'].registro_abertura.IND_MOV = '1'
    
    def enviar_registro_G990(self):
            
        self._arq._blocos['G'].registro_encerramento.QTD_LIN_G = len(self._arq._blocos['G'].registros)

    def enviar_registro_H001(self):

        self._arq._blocos['H'].registro_abertura.IND_MOV = '0'

    def enviar_registro_H005(self, product_ids_list):

        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        pos = len(self._arq._blocos['H'].registros) - 2

        self.enviar_registro_H010(product_ids_list)

        registroH005 = RegistroH005()

        registroH005.DT_INV = self.date_ini.replace(day = monthrange(self.date_ini.year, self.date_ini.month)[1])
        registroH005.VL_INV = self.h005_vl_inv
        registroH005.MOT_INV = '01'

        self._arq._blocos['H'].add(registroH005, pos)

    def enviar_registro_H010(self, product_ids_list):

        stock_valuations = self.env['stock.valuation.layer'].search([('create_date', '<', self.date_ini + relativedelta(months=1)),('quantity','!=',0.00)])
        for key, grp in groupby(sorted(stock_valuations, key = lambda l: l.product_id.id), lambda l: l.product_id.id):
            
            stock_valuation_list = list(grp)
            key_vals = {'product_id': self.env['product.product'].browse(key)} #dict(zip(["product_id"], key))
            
            product_ids_list.append(key_vals['product_id'].id)

            registroH010 = RegistroH010()

            registroH010.COD_ITEM = key_vals['product_id'].default_code
            registroH010.UNID = stock_valuation_list[0]['uom_id'].l10n_br_codigo_sefaz or ''
            qtd = sum(item["quantity"] for item in stock_valuation_list)
            if qtd < 0.00:
                qtd = 0.00
            registroH010.QTD = qtd
            
            vl_unit = sum(item["unit_cost"] for item in stock_valuation_list)
            if vl_unit < 0.00:
                vl_unit = 0.00
            registroH010.VL_UNIT = vl_unit
            vl_item = sum(item["value"] for item in stock_valuation_list)
            if vl_item < 0.00:
                vl_item = 0.00
            registroH010.VL_ITEM = vl_item
            self.h005_vl_inv += vl_item
            
            registroH010.IND_PROP = '0'
            registroH010.COD_PART = ''
            registroH010.TXT_COMPL = ''
            registroH010.COD_CTA = key_vals['product_id'].property_account_income_id.code or key_vals['product_id'].categ_id.property_account_income_categ_id.code
            registroH010.VL_ITEM_IR = 0.00

            self._arq._blocos['H'].add(registroH010)

    def enviar_registro_H990(self):

        self._arq._blocos['H'].registro_encerramento.QTD_LIN_H = len(self._arq._blocos['H'].registros)

    def enviar_registro_K001(self):
    
        self._arq._blocos['K'].registro_abertura.IND_MOV = '0'

    def enviar_registro_K100(self):
    
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        registroK100 = RegistroK100()

        registroK100.DT_INI = self.date_ini
        registroK100.DT_FIN = self.date_fim

        self._arq._blocos['K'].add(registroK100)

    def enviar_registro_K200(self):
    
        def _format_date(date):
            return datetime.strftime(date,'%d%m%Y')

        stock_valuations = self.env['stock.valuation.layer'].search([('create_date', '<', self.date_ini + relativedelta(months=1)),('quantity','!=',0.00)])
        for key, grp in groupby(sorted(stock_valuations, key = lambda l: l.product_id.id), lambda l: l.product_id.id):
            
            stock_valuation_list = list(grp)
            key_vals = {'product_id': self.env['product.product'].browse(key)} #dict(zip(["product_id"], key))
            
            if not str(key_vals['product_id'].categ_id.l10n_br_tipo_produto) in ['00','01','02','03','04','05','06','10']:
                continue

            registroK200 = RegistroK200()

            registroK200.DT_EST = self.date_fim
            registroK200.COD_ITEM = key_vals['product_id'].default_code
            qtd = sum(item["quantity"] for item in stock_valuation_list)
            if qtd < 0.00:
                qtd = 0.00
            registroK200.QTD = qtd
            registroK200.IND_EST = '0'
            registroK200.COD_PART = ''

            self._arq._blocos['K'].add(registroK200)

    def enviar_registro_K990(self):

        self._arq._blocos['K'].registro_encerramento.QTD_LIN_K = len(self._arq._blocos['K'].registros)

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
                
                if regkey == '9900':
                    qtdreg += 3
    
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
