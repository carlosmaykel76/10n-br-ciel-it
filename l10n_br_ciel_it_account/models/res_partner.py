# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import pycep_correios
from pycpfcnpj import cpf, cnpj, compatible
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *

import json
import requests
from requests.auth import HTTPBasicAuth

import xml.etree.ElementTree as ET

import base64

import logging
_logger = logging.getLogger(__name__)

ADDRESS_FIELDS = ('street', 'street2', 'zip', 'city', 'state_id', 'country_id', 'l10n_br_endereco_numero', 'l10n_br_endereco_bairro')


class ResAgencia(models.Model):
    _name = 'res.agencia'

    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    bank_id = fields.Many2one('res.bank',string="Bank")


class ResPartnerReferenciaComercial(models.Model):
    _name = 'res.partner.referencia.comercial'

    empresa = fields.Char(string="Empresa")
    contato = fields.Char(string="Contato")
    telefone = fields.Char(string="Telefone")
    pontualidade = fields.Boolean(string="Pontualidade")
    recorrencia = fields.Char(string="Recorrencia")
    prazo_pagamento = fields.Char(string="Prazo Pagamento")
    valor_ultima_compra = fields.Float(string="Valor Ultima Compra")
    data_ultima_compra = fields.Date(string="Data Ultima Compra")
    cliente_desde = fields.Date(string="Cliente Desde")
    valor_maior_compra = fields.Float(string="Valor Maior Compra")
    limite_credito = fields.Float(string="Limite Credito")
    partner_id = fields.Many2one('res.partner', string="Customer")


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    manager = fields.Char(string="Manager")
    phone = fields.Char(string="Phone")
    data_abertura = fields.Date(string="Abertura Date")
    agencia_id = fields.Many2one('res.agencia',string="Agencia")


class ResPartnerCNAE(models.Model):
    _name = 'res.partner.cnae'

    code = fields.Char(string="Code")
    text = fields.Char(string="Text")
    principal = fields.Boolean(string="Principal")
    partner_id = fields.Many2one('res.partner', string="Customer")


class ResPartnerQSA(models.Model):
    _name = 'res.partner.qsa'

    nome = fields.Char(string="Nome")
    qual = fields.Char(string="Qual")
    pais_origem = fields.Char(string="Pais Origem")
    nome_rep_legal = fields.Char(string="Nome Rep Legal")
    qual_rep_legal = fields.Char(string="Qual Rep Legal")
    partner_id = fields.Many2one('res.partner', string="Customer")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_br_cnpj = fields.Char( string='CNPJ' )
    l10n_br_cpf = fields.Char( string='CPF' )
    l10n_br_id_estrangeiro = fields.Char( string='Id Estrangeiro' )
    l10n_br_im = fields.Char( string='Inscrição Municipal' )
    l10n_br_is = fields.Char( string='Inscrição Suframa' )
    l10n_br_ie = fields.Char( string='Inscrição Estadual' )
    l10n_br_razao_social = fields.Char( string='Razão Social' )
    l10n_br_indicador_ie = fields.Selection( INDICADOR_IE, string='Indicador da I.E.' )
    l10n_br_endereco_numero = fields.Char( string='Número' )
    l10n_br_endereco_bairro = fields.Char( string='Bairro' )
    l10n_br_consultar_cep = fields.Boolean( string='Consultar CEP' )
    l10n_br_consultar_cnpj = fields.Boolean( string='Consultar CNPJ' )
    l10n_br_municipio_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município', ondelete='restrict', domain="[('state_id', '=?', state_id)]")
    l10n_br_mensagem_fiscal_01_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal 1' )
    l10n_br_mensagem_fiscal_02_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal 2' )
    l10n_br_mensagem_fiscal_03_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal 3' )
    l10n_br_mensagem_fiscal_04_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal 4' )
    l10n_br_mensagem_fiscal_05_id = fields.Many2one( 'l10n_br_ciel_it_account.mensagem.fiscal', string='Observação Fiscal 5' )
    l10n_br_receber_nfe = fields.Boolean( string='Receber NF-e' )
    l10n_br_compra_indcom = fields.Selection( TIPO_DESTINACAO, string='Destinação de Uso', default='uso' )

    #Added New Field - Ankit
    natureza_juridica = fields.Char(string="Natureza Juridica")
    capital_social = fields.Char(string="Capital Social")
    partner_cnae_ids = fields.One2many('res.partner.cnae','partner_id', string="Partner CNAE")
    partner_qsa_ids = fields.One2many('res.partner.qsa', 'partner_id', string="Partner QSA")
    partner_referencia_ids = fields.One2many('res.partner.referencia.comercial', 'partner_id', string="Partner Referencia")


    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id and self.state_id != self.l10n_br_municipio_id.state_id:
            self.l10n_br_municipio_id = False

    @api.onchange('l10n_br_municipio_id')
    def _onchange_l10n_br_municipio_id(self):
        self.city = self.l10n_br_municipio_id.name
        if self.l10n_br_municipio_id.state_id:
            self.state_id = self.l10n_br_municipio_id.state_id

    @api.constrains('l10n_br_cnpj')
    def _check_l10n_br_cnpj(self):
        for partner in self:
            if partner.l10n_br_cnpj and not cnpj.validate(partner.l10n_br_cnpj):
                raise ValidationError(_('CNPJ informado não é válido!'))

    @api.constrains('l10n_br_cpf')
    def _check_l10n_br_cpf(self):
        for partner in self:
            if partner.l10n_br_cpf and not cpf.validate(partner.l10n_br_cpf):
                raise ValidationError(_('CPF informado não é válido!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('l10n_br_cnpj'):
                if cnpj.validate(vals['l10n_br_cnpj']):
                    vals['l10n_br_cnpj'] = compatible.clear_punctuation(vals['l10n_br_cnpj'])
                    vals['l10n_br_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['l10n_br_cnpj'][:2], vals['l10n_br_cnpj'][2:5], vals['l10n_br_cnpj'][5:8], vals['l10n_br_cnpj'][8:12], vals['l10n_br_cnpj'][12:])
            if vals.get('l10n_br_cpf'):
                if cpf.validate(vals['l10n_br_cpf']):
                    vals['l10n_br_cpf'] = compatible.clear_punctuation(vals['l10n_br_cpf'])
                    vals['l10n_br_cpf'] = '{}.{}.{}-{}'.format(vals['l10n_br_cpf'][:3], vals['l10n_br_cpf'][3:6], vals['l10n_br_cpf'][6:9], vals['l10n_br_cpf'][9:])
        return super(ResPartner, self).create(vals_list)

    def write(self, vals):
        if vals.get('l10n_br_cnpj'):
            if cnpj.validate(vals['l10n_br_cnpj']):
                vals['l10n_br_cnpj'] = compatible.clear_punctuation(vals['l10n_br_cnpj'])
                vals['l10n_br_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['l10n_br_cnpj'][:2], vals['l10n_br_cnpj'][2:5], vals['l10n_br_cnpj'][5:8], vals['l10n_br_cnpj'][8:12], vals['l10n_br_cnpj'][12:])
        if vals.get('l10n_br_cpf'):
            if cpf.validate(vals['l10n_br_cpf']):
                vals['l10n_br_cpf'] = compatible.clear_punctuation(vals['l10n_br_cpf'])
                vals['l10n_br_cpf'] = '{}.{}.{}-{}'.format(vals['l10n_br_cpf'][:3], vals['l10n_br_cpf'][3:6], vals['l10n_br_cpf'][6:9], vals['l10n_br_cpf'][9:])
        return super(ResPartner, self).write(vals)

    def _consulta_cnpj(self, cnpj, cpf, ie, uf, receita):
        partner_cnae = self.env['res.partner.cnae']
        partner_qsa = self.env['res.partner.qsa']
        if cnpj or cpf or ie:
            try:

                def _format_cnpj_cpf(cnpj_cpf):
                    if cnpj_cpf:
                        return cnpj_cpf.replace("/","").replace("-","").replace(".","")
                    else:
                        return ""

                l10n_br_documento_id = self.env['l10n_br_ciel_it_account.tipo.documento'].search([],limit=1)

                if receita:
                    
                    if not l10n_br_documento_id.l10n_br_url_cnpj:
                        return False

                    url = "%s/v1/cnpj/%s/days/3" % (
                        l10n_br_documento_id.l10n_br_url_cnpj,
                        _format_cnpj_cpf(cnpj),
                    )

                    payload = {}

                    headers = {
                        'Authorization': 'Bearer %s' % l10n_br_documento_id.l10n_br_token_cnpj,
                    }

                    response = requests.request("GET", url, headers=headers, data = payload)

                    json_data = json.loads(response.text.encode('utf8'))
                    
                    if json_data['status'] == 'OK':
                        dados = {}

                        dados['CNPJ'] = json_data['cnpj']
                        dados['xNome'] = json_data['nome']
                        dados['fantasia'] = json_data['fantasia']
                        dados['xLgr'] = json_data['logradouro']
                        dados['complemento'] = json_data['complemento']
                        dados['nro'] = json_data['numero']
                        dados['xBairro'] = json_data['bairro']
                        dados['CEP'] = json_data['cep']
                        dados['telefone'] = json_data['telefone']
                        dados['UF'] = json_data['uf']
                        dados['cMun'] = json_data['municipio']
                        dados['email'] = json_data['email']

                        #Added New Field
                        dados['natureza_juridica'] = json_data['natureza_juridica']
                        dados['capital_social'] = json_data['capital_social']

                        for atividade_principal in json_data['atividade_principal']:
                            atividade_principal_rec = partner_cnae.search([('code','=',atividade_principal.get('code'))])
                            if not atividade_principal_rec:
                                partner_cnae.create({
                                    'code': atividade_principal.get('code'),
                                    'text':atividade_principal.get('text'),
                                    'principal': True,
                                    'partner_id': self.id
                                })
                        for atividades_secundarias in json_data['atividades_secundarias']:
                            atividades_secundarias_rec = partner_cnae.search(
                                [('code', '=', atividades_secundarias.get('code'))])
                            if not atividades_secundarias_rec:
                                partner_cnae.create({
                                    'code': atividades_secundarias.get('code'),
                                    'text':atividades_secundarias.get('text'),
                                    'principal': False,
                                    'partner_id': self.id
                                })
                        for qsa in json_data['qsa']:
                            qsa_rec = partner_qsa.search(
                                [('nome', '=', qsa.get('nome'))])
                            if not qsa_rec:
                                partner_qsa.create({
                                    'qual': qsa.get('qual'),
                                    'nome': qsa.get('nome'),
                                    'pais_origem': qsa.get('pais_origem'),
                                    'nome_rep_legal': qsa.get('nome_rep_legal'),
                                    'qual_rep_legal': qsa.get('qual_rep_legal'),
                                    'partner_id': self.id
                                })

                        return dados

                    else:                
                        return False

                else:

                    url = "%s/ManagerAPIWeb/nfe/conscad?Grupo=%s&CNPJ=%s&UF=%s" % (
                        l10n_br_documento_id.l10n_br_url,
                        l10n_br_documento_id.l10n_br_grupo,
                        _format_cnpj_cpf(self.env.user.company_id.l10n_br_cnpj),
                        uf or self.env.user.company_id.state_id.code,
                    )
                    
                    if cnpj:
                        url += "&CNPJConsCad=%s" % _format_cnpj_cpf(cnpj)

                    elif cpf:                    
                        url += "&CPF=%s" % _format_cnpj_cpf(cpf)
                        
                    elif ie:
                        url += "&IE=%s" % ie

                    headers = {
                        'Content-Type': "application/x-www-form-urlencoded",
                    }

                    basic_auth = HTTPBasicAuth(
                        l10n_br_documento_id.l10n_br_usuario,
                        l10n_br_documento_id.l10n_br_senha,
                    )
                    
                    response = requests.get(url, auth=basic_auth, headers=headers)
                    
                    if 'EXCEPTION' in response.text:
                        raise UserError(str(response.text))                
                    
                    tree = ET.fromstring(response.text)
                    dados = {}
                    for node in tree.iter('{http://www.portalfiscal.inf.br/nfe}infCons'):
                        for elem in node.iter():
                            if not elem.tag==node.tag:
                                dados[elem.tag.replace('{http://www.portalfiscal.inf.br/nfe}','')] = elem.text

                    if dados.get('cStat') == '111':
                        dados = {}
                        for node in tree.iter('{http://www.portalfiscal.inf.br/nfe}infCad'):
                            for elem in node.iter():
                                if not elem.tag==node.tag:
                                    dados[elem.tag.replace('{http://www.portalfiscal.inf.br/nfe}','')] = elem.text
                        return dados

                    else:                
                        return False

            except Exception as e:
                raise UserError(_(str(e).split(',')[-1]))
        else:
            return False

    def _consulta_cep(self, cep):
        if cep:
            try:
                return pycep_correios.get_address_from_cep(cep)
            except:
                return False
        else:
            return False

    @api.onchange('l10n_br_consultar_cep')
    def onchange_l10n_br_consultar_cep(self):
        for partner in self:
            endereco = self._consulta_cep(partner.zip)
            if endereco:
                partner.street = endereco['logradouro']
                partner.street2 = endereco['complemento']
                partner.l10n_br_endereco_bairro = endereco['bairro']

                partner.l10n_br_municipio_id = False
                partner.state_id = False
                partner.country_id = False
                br_country = self.env.ref('base.br')
                if br_country:
                    partner.country_id = br_country.id
                    state_id = self.env['res.country.state'].search([('code','=',endereco["uf"]),('country_id','=',br_country.id)],limit=1)
                    if state_id:
                        partner.state_id = state_id.id
                        municipio_id = self.env['l10n_br_ciel_it_account.res.municipio'].search([('name','=',endereco['cidade']),('state_id','=',state_id.id)],limit=1)
                        if municipio_id:
                            partner.l10n_br_municipio_id = municipio_id.id

    @api.onchange('l10n_br_consultar_cnpj')
    def onchange_l10n_br_consultar_cnpj(self):

        def _format_fone(fone):
            fone = "".join([s for s in fone if s.isdigit()])
            if len(fone) > 11 and fone[0:2] == "55":
                fone = fone[2:]
            return fone

        def _format_cep(texto):
            return str(texto).replace("-","").replace(".","")

        for partner in self:
            
            try:
            
                dados = self._consulta_cnpj(partner.l10n_br_cnpj,partner.l10n_br_cpf,partner.l10n_br_ie,partner.state_id.code, True)
                if dados:
                    partner.l10n_br_cnpj = dados.get('CNPJ')
                    partner.name = dados.get('fantasia') or dados.get('xNome')
                    partner.l10n_br_razao_social = dados.get('xNome')
                    partner.street = dados.get('xLgr')
                    partner.street2 = dados.get('complemento')
                    partner.phone = _format_fone(dados.get('telefone'))
                    partner.l10n_br_endereco_numero = dados.get('nro')
                    partner.l10n_br_endereco_bairro = dados.get('xBairro')
                    partner.zip = _format_cep(dados.get('CEP'))
                    partner.email = dados.get('email')

                    partner.state_id = False
                    partner.country_id = False
                    br_country = self.env.ref('base.br')
                    if br_country:
                        partner.country_id = br_country.id
                        state_id = self.env['res.country.state'].search([('code','=',dados.get('UF')),('country_id','=',br_country.id)],limit=1)
                        if state_id:
                            partner.state_id = state_id.id

                            municipio_id = self.env['l10n_br_ciel_it_account.res.municipio'].search([('state_id','=',state_id.id),('name','ilike',dados.get('cMun'))],limit=1)
                            if municipio_id:
                                partner.l10n_br_municipio_id = municipio_id.id

                dados = self._consulta_cnpj(partner.l10n_br_cnpj,partner.l10n_br_cpf,partner.l10n_br_ie,partner.state_id.code, False)
                if dados:
                    partner.l10n_br_cpf = dados.get('CPF')
                    partner.l10n_br_ie = dados.get('IE')
                    if not partner.l10n_br_cnpj:
                        partner.l10n_br_indicador_ie = '9'
                    else:
                        if partner.l10n_br_ie:
                            partner.l10n_br_indicador_ie = '1'
                        else:
                            partner.l10n_br_indicador_ie = '2'
                else:
                    partner.l10n_br_indicador_ie = '9'

            except Exception as e:
                pass                                
