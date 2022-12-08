# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResCountry(models.Model):
    _inherit = 'res.country'

    l10n_br_codigo_bacen = fields.Char( string='Código BACEN' )

class CountryState(models.Model):
    _inherit = 'res.country.state'

    l10n_br_codigo_ibge = fields.Char( string='Código IBGE' )
    l10n_br_fcp_aliquota = fields.Float( string='Aliquota do Fundo de Combate a Pobreza (%)' )

class L10nBrResMunicipio(models.Model):
    _name = 'l10n_br_ciel_it_account.res.municipio'
    _description = 'Município'

    name = fields.Char(string='Nome do Município',required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=?', country_id)]", required=True)
    codigo_ibge = fields.Char( string='Código IBGE' )

    _sql_constraints = [
        ('name_code_uniq', 'unique(state_id, name)', 'O nome deve ser unico por UF !')
    ]

    def copy(self, default=None):
        if default is None:
            default = {}

        default.update({'name': self.name + '(2)'})
        return super(L10nBrResMunicipio, self).copy(dict(default or {}))

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "{} ({})".format(record.name, record.state_id.code)))
        return result