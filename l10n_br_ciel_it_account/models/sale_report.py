# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SaleReport(models.Model):
    _inherit = "sale.report"

    partner_zone_id = fields.Many2one('partner.zone', string="Zones", readonly="True")
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
    purchase_price = fields.Float(string='Cost', readonly=True)


    def _query(self, with_clause='', fields={}, groupby='', from_clause=''):
        fields['partner_zone_id'] = ", partner.zone_id as partner_zone_id"
        fields['l10n_br_icms_aliquota'] = ", l.l10n_br_icms_aliquota as l10n_br_icms_aliquota"
        fields['l10n_br_icms_valor'] = ", l.l10n_br_icms_valor as l10n_br_icms_valor"
        fields['l10n_br_icmsst_aliquota'] = ", l.l10n_br_icmsst_aliquota as l10n_br_icmsst_aliquota"
        fields['l10n_br_icmsst_valor'] = ", l.l10n_br_icmsst_valor as l10n_br_icmsst_valor"
        fields['l10n_br_icmsst_mva'] = ", l.l10n_br_icmsst_mva as l10n_br_icmsst_mva"
        fields['l10n_br_ipi_aliquota'] = ", l.l10n_br_ipi_aliquota as l10n_br_ipi_aliquota"
        fields['l10n_br_ipi_valor'] = ", l.l10n_br_ipi_valor as l10n_br_ipi_valor"
        fields['l10n_br_pis_aliquota'] = ", l.l10n_br_pis_aliquota as l10n_br_pis_aliquota"
        fields['l10n_br_pis_valor'] = ", l.l10n_br_pis_valor as l10n_br_pis_valor"
        fields['l10n_br_cofins_aliquota'] = ", l.l10n_br_cofins_aliquota as l10n_br_cofins_aliquota"
        fields['l10n_br_cofins_valor'] = ", l.l10n_br_cofins_valor as l10n_br_cofins_valor"
        fields['purchase_price'] = ", l.purchase_price as purchase_price"

        groupby += ', partner.zone_id , l.l10n_br_icms_aliquota  , l.l10n_br_icms_valor , l.l10n_br_icmsst_aliquota' \
                   ', l.l10n_br_icmsst_valor , l.l10n_br_icmsst_mva , l.l10n_br_ipi_aliquota ,  l.l10n_br_pis_aliquota' \
                   ', l.l10n_br_ipi_valor, l.l10n_br_pis_valor ' \
                   ', l.l10n_br_cofins_aliquota , l.l10n_br_cofins_valor , l.purchase_price'
        return super(SaleReport, self)._query(with_clause, fields, groupby, from_clause)
