# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import pycep_correios
from pycpfcnpj import cpf, cnpj, compatible
from odoo.addons.l10n_br_ciel_it_account.models.sale_order import *

import logging
_logger = logging.getLogger(__name__)

REGIME_TRIBUTARIO = [
    ('1', 'Simples Nacional'),
    ('2', 'Simples Nacional, excesso sublimite de receita bruta'),
    ('3', 'Regime Normal'),
]

INCIDENCIA_CUMULATIVA = [
    ('1', 'Lucro Real'),
    ('2', 'Lucro Presumido'),
]

class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_br_cnpj = fields.Char( string='CNPJ', compute_sudo=False, compute='_compute_fiscal', inverse='_inverse_l10n_br_cnpj' )
    l10n_br_im = fields.Char( string='Inscrição Municipal', compute_sudo=False, compute='_compute_fiscal', inverse='_inverse_l10n_br_im' )
    l10n_br_ie = fields.Char( string='Inscrição Estadual', compute_sudo=False, compute='_compute_fiscal', inverse='_inverse_l10n_br_ie' )
    l10n_br_razao_social = fields.Char( string='Razão Social', compute_sudo=False, compute='_compute_fiscal', inverse='_inverse_l10n_br_razao_social' )
    l10n_br_cnae = fields.Char( string='CNAE' )
    l10n_br_regime_tributario = fields.Selection( REGIME_TRIBUTARIO, string='Regime Tributário' )
    l10n_br_incidencia_cumulativa = fields.Selection( INCIDENCIA_CUMULATIVA, string='Incidência Cumulativa' )
    l10n_br_endereco_numero = fields.Char( string='Número', compute_sudo=False, compute='_compute_address', inverse='_inverse_l10n_br_endereco_numero' )
    l10n_br_endereco_bairro = fields.Char( string='Bairro', compute_sudo=False, compute='_compute_address', inverse='_inverse_l10n_br_endereco_bairro' )
    l10n_br_consultar_cep = fields.Boolean( string='Consultar CEP' )
    l10n_br_municipio_id = fields.Many2one('l10n_br_ciel_it_account.res.municipio', string='Município', ondelete='restrict', domain="[('state_id', '=?', state_id)]")
    l10n_br_exclui_icms_piscofins = fields.Boolean( string='Exclui ICMS da Base do PIS/COFINS' )
    l10n_br_fcp_interno_consumidor_final = fields.Boolean( string='Operação Interna incide % FCP para Consumidor Final' )
    l10n_br_icms_credito_aliquota = fields.Float( string='Alíquota aplicável de cálculo do crédito (Simples Nacional)' )
    l10n_br_contador_partner_id = fields.Many2one('res.partner', string='Contador', ondelete='restrict')

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
        for company in self:
            if company.l10n_br_cnpj and not cnpj.validate(company.l10n_br_cnpj):
                raise ValidationError(_('CNPJ informado não é válido!'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('l10n_br_cnpj'):
                if cnpj.validate(vals['l10n_br_cnpj']):
                    vals['l10n_br_cnpj'] = compatible.clear_punctuation(vals['l10n_br_cnpj'])
                    vals['l10n_br_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['l10n_br_cnpj'][:2], vals['l10n_br_cnpj'][2:5], vals['l10n_br_cnpj'][5:8], vals['l10n_br_cnpj'][8:12], vals['l10n_br_cnpj'][12:])
        return super(ResCompany, self).create(vals_list)

    def write(self, vals):
        if vals.get('l10n_br_cnpj'):
            if cnpj.validate(vals['l10n_br_cnpj']):
                vals['l10n_br_cnpj'] = compatible.clear_punctuation(vals['l10n_br_cnpj'])
                vals['l10n_br_cnpj'] = '{}.{}.{}/{}-{}'.format(vals['l10n_br_cnpj'][:2], vals['l10n_br_cnpj'][2:5], vals['l10n_br_cnpj'][5:8], vals['l10n_br_cnpj'][8:12], vals['l10n_br_cnpj'][12:])
        return super(ResCompany, self).write(vals)

    def _get_company_address_fields(self, partner):
        result = super()._get_company_address_fields(partner)
        result.update({
            'l10n_br_endereco_numero': partner.l10n_br_endereco_numero,
            'l10n_br_endereco_bairro': partner.l10n_br_endereco_bairro,
        })

        return result

    def _inverse_l10n_br_endereco_numero(self):
        for company in self:
            company.partner_id.l10n_br_endereco_numero = company.l10n_br_endereco_numero

    def _inverse_l10n_br_endereco_bairro(self):
        for company in self:
            company.partner_id.l10n_br_endereco_bairro = company.l10n_br_endereco_bairro

    def _get_company_fiscal_fields(self, partner):
        return {
            'l10n_br_cnpj': partner.l10n_br_cnpj,
            'l10n_br_im': partner.l10n_br_im,
            'l10n_br_ie': partner.l10n_br_ie,
            'l10n_br_razao_social': partner.l10n_br_razao_social,
        }

    def _compute_fiscal(self):
        for company in self.filtered(lambda company: company.partner_id):
            company.update(company._get_company_fiscal_fields(company.partner_id))

    def _inverse_l10n_br_cnpj(self):
        for company in self:
            company.partner_id.l10n_br_cnpj = company.l10n_br_cnpj

    def _inverse_l10n_br_im(self):
        for company in self:
            company.partner_id.l10n_br_im = company.l10n_br_im

    def _inverse_l10n_br_ie(self):
        for company in self:
            company.partner_id.l10n_br_ie = company.l10n_br_ie

    def _inverse_l10n_br_razao_social(self):
        for company in self:
            company.partner_id.l10n_br_razao_social = company.l10n_br_razao_social

    def _consulta_cep(self, cep):
        self.ensure_one()
        if self.zip:
            try:
                return pycep_correios.get_address_from_cep(cep)
            except:
                return False
        else:
            return False

    @api.onchange('l10n_br_consultar_cep')
    def onchange_l10n_br_consultar_cep(self):
        for company in self:
            endereco = self._consulta_cep(company.zip)
            if endereco:
                company.street = endereco['logradouro']
                company.street2 = endereco['complemento']
                company.l10n_br_endereco_bairro = endereco['bairro']
                company.city = endereco['cidade']

                company.state_id = False
                company.country_id = False
                br_country = self.env.ref('base.br')
                if br_country:
                    company.country_id = br_country.id
                    state_id = self.env['res.country.state'].search([('code','=',endereco["uf"]),('country_id','=',br_country.id)])
                    if state_id:
                        company.state_id = state_id.id
