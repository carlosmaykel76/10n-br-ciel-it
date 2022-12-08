# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    l10n_br_icms_aliquota = fields.Float(string='Aliquota do ICMS (%)', readonly=True)
    l10n_br_icms_valor = fields.Float(string='Valor do ICMS', readonly=True)
    l10n_br_icmsst_aliquota = fields.Float(string='Aliquota do ICMSST (%)', readonly=True)
    l10n_br_icmsst_valor = fields.Float(string='Valor do ICMSST', readonly=True)
    l10n_br_icmsst_mva = fields.Float(string='Aliquota da Margem de Valor Adicionado do ICMSST (%)', readonly=True)
    l10n_br_ipi_aliquota = fields.Float(string='Aliquota do ICMSST (%)', readonly=True)
    l10n_br_ipi_valor = fields.Float( string='Valor do IPI', readonly=True)
    l10n_br_pis_aliquota = fields.Float(string='Aliquota do PIS (%)', readonly=True)
    l10n_br_pis_valor = fields.Float(string='Valor do PIS', readonly=True)
    l10n_br_cofins_aliquota = fields.Float(string='Aliquota do Cofins (%)', readonly=True)
    l10n_br_cofins_valor = fields.Float(string='Valor do Cofins', readonly=True)

    @api.model
    def _select(self):
        res = super(AccountInvoiceReport, self)._select()
        res += ''', line.l10n_br_icms_aliquota AS l10n_br_icms_aliquota 
        , line.l10n_br_icms_valor AS l10n_br_icms_valor 
        , line.l10n_br_icmsst_aliquota AS l10n_br_icmsst_aliquota 
        , line.l10n_br_icmsst_valor AS l10n_br_icmsst_valor
        , line.l10n_br_icmsst_mva AS l10n_br_icmsst_mva 
        , line.l10n_br_ipi_aliquota AS l10n_br_ipi_aliquota 
        , line.l10n_br_ipi_valor AS l10n_br_ipi_valor
        , line.l10n_br_pis_aliquota AS l10n_br_pis_aliquota
        , line.l10n_br_pis_valor AS l10n_br_pis_valor 
        , line.l10n_br_cofins_aliquota AS l10n_br_cofins_aliquota
        , line.l10n_br_cofins_valor AS l10n_br_cofins_valor'''
        return res

    @api.model
    def _group_by(self):
        res = super(AccountInvoiceReport, self)._group_by()
        res += ''', line.l10n_br_icms_aliquota
        , line.l10n_br_icms_valor
        , line.l10n_br_icmsst_aliquota 
        , line.l10n_br_icmsst_valor
        , line.l10n_br_icmsst_mva 
        , line.l10n_br_ipi_aliquota 
        , line.l10n_br_ipi_valor
        , line.l10n_br_pis_aliquota
        , line.l10n_br_pis_valor 
        , line.l10n_br_cofins_aliquota
        , line.l10n_br_cofins_valor '''
        return res
