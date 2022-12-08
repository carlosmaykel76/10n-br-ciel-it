# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

UOM_SEFAZ = [
    ('AMPOLA', 'AMPOLA'),
    ('BALDE', 'BALDE'),
    ('BANDEJ', 'BANDEJA'),
    ('BARRA', 'BARRA'),
    ('BISNAG', 'BISNAGA'),
    ('BLOCO', 'BLOCO'),
    ('BOBINA', 'BOBINA'),
    ('BOMB', 'BOMBONA'),
    ('CAPS', 'CAPSULA'),
    ('CART', 'CARTELA'),
    ('CENTO', 'CENTO'),
    ('CJ', 'CONJUNTO'),
    ('CM', 'CENTIMETRO'),
    ('CM2', 'CENTIMETRO QUADRADO'),
    ('CX', 'CAIXA'),
    ('CX2', 'CAIXA COM 2 UNIDADES'),
    ('CX3', 'CAIXA COM 3 UNIDADES'),
    ('CX5', 'CAIXA COM 5 UNIDADES'),
    ('CX10', 'CAIXA COM 10 UNIDADES'),
    ('CX15', 'CAIXA COM 15 UNIDADES'),
    ('CX20', 'CAIXA COM 20 UNIDADES'),
    ('CX25', 'CAIXA COM 25 UNIDADES'),
    ('CX50', 'CAIXA COM 50 UNIDADES'),
    ('CX100', 'CAIXA COM 100 UNIDADES'),
    ('DISP', 'DISPLAY'),
    ('DUZIA', 'DUZIA'),
    ('EMBAL', 'EMBALAGEM'),
    ('FARDO', 'FARDO'),
    ('FOLHA', 'FOLHA'),
    ('FRASCO', 'FRASCO'),
    ('GALAO', 'GALÃO'),
    ('GF', 'GARRAFA'),
    ('GRAMAS', 'GRAMAS'),
    ('JOGO', 'JOGO'),
    ('KG', 'QUILOGRAMA'),
    ('KIT', 'KIT'),
    ('LATA', 'LATA'),
    ('LITRO', 'LITRO'),
    ('M', 'METRO'),
    ('M2', 'METRO QUADRADO'),
    ('M3', 'METRO CÚBICO'),
    ('MILHEI', 'MILHEIRO'),
    ('ML', 'MILILITRO'),
    ('MWH', 'MEGAWATT HORA'),
    ('PACOTE', 'PACOTE'),
    ('PALETE', 'PALETE'),
    ('PARES', 'PARES'),
    ('PC', 'PEÇA'),
    ('POTE', 'POTE'),
    ('K', 'QUILATE'),
    ('RESMA', 'RESMA'),
    ('ROLO', 'ROLO'),
    ('SACO', 'SACO'),
    ('SACOLA', 'SACOLA'),
    ('TAMBOR', 'TAMBOR'),
    ('TANQUE', 'TANQUE'),
    ('TON', 'TONELADA'),
    ('TUBO', 'TUBO'),
    ('UNID', 'UNIDADE'),
    ('VASIL', 'VASILHAME'),
    ('VIDRO', 'VIDRO'),
]

UOM_COMEX_SEFAZ = [
    ('UN', 'Unidade'),
    ('KG', 'Quilograma'),
    ('DUZIA', 'Duzia'),
    ('G', 'Grama'),
    ('TON', 'Tonel Metr Liquida'),
    ('LT', 'Litro'),
    ('1000UN', 'Mil Unidades'),
    ('M3', 'Metro Cubico'),
    ('MWHORA', 'Megawatt Hora'),
    ('QUILAT', 'Quilate'),
    ('M2', 'Metro Quadrado'),
    ('METRO', 'Metro'),
    ('PARES', 'Pares'),
]
class UoM(models.Model):
    _inherit = 'uom.uom'

    l10n_br_codigo_sefaz = fields.Selection( UOM_SEFAZ, string='UoM Sefaz' )
    l10n_br_codigo_comex_sefaz = fields.Selection( UOM_COMEX_SEFAZ, string='UoM COMEX Sefaz' )

