# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

{
    'name': "CIEL IT - Localização Brazil (Sale Output)",

    'summary': """
        CIEL IT - Localização Brazil (Sale Output)
        """,

    'description': """
        CIEL IT - Localização Brazil (Sale Output)
    """,

    'author': "CIEL IT, Inc.",
    'website': "https://www.ciel-it.com",

    'category': 'Localization',
    'version': '13.0',
    'application': True,
    'license': 'Other proprietary',

    'depends': [
        'l10n_br_ciel_it_account',
        'sale',
    ],

    'data': [
        'report/sale_report_template.xml'
    ],
    'demo': [
    ],
}
