# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

{
    'name': "CIEL IT - Localização Brazil (Account EE)",

    'summary': """
        CIEL IT - Localização Brazil (Account EE)
        """,

    'description': """
        CIEL IT - Localização Brazil (Account EE)
    """,

    'author': "CIEL IT, Inc.",
    'website': "https://www.ciel-it.com",

    'category': 'Localization',
    'version': '13.0',
    'application': True,
    'license': 'Other proprietary',

    'depends': [
        'l10n_br_ciel_it_account',
        'account_accountant',
    ],

    'data': [
        'views/res_partner_view.xml',
    ],
    'demo': [
    ],
}
