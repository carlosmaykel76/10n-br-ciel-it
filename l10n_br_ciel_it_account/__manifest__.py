# -*- coding: utf-8 -*-
# Part of CIEL IT. See LICENSE file for full copyright and licensing details.

{
    'name': "CIEL IT - Localização Brazil (Account CE)",

    'summary': """
        CIEL IT - Localização Brazil (Account CE)
        """,

    'description': """
        CIEL IT - Localização Brazil (Account CE)
    """,

    'author': "CIEL IT, Inc.",
    'website': "https://www.ciel-it.com",

    'category': 'Localization',
    'version': '13.0',
    'application': True,
    'license': 'Other proprietary',

    'depends': [
        'base',
        'web',
        'mail',
        'contacts',
        'delivery',
        'account',
        'purchase',
        'uom',
        'stock',
        'sale',
        'l10n_generic_coa',
        'purchase_discount', # https://github.com/OCA/purchase-workflow
        'product_expiry'
    ],

    'data': [
        'security/company_security.xml',
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'data/product_data.xml',
        'data/account_data.xml',
        'data/sale_data.xml',
        'data/res_country_data.xml',
        'data/res_config_settings.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/res_country_view.xml',
        'views/delivery_carrier_view.xml',
        'views/account_incoterms_view.xml',
        'views/account_payment_term_view.xml',
        'views/uom_uom_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/account_view.xml',
        'views/purchase_view.xml',
        'views/account_report_view.xml',
        'views/account_sped_fiscal_view.xml',
        'views/account_sped_contribuicao_view.xml',
        'views/account_comission_view.xml',
    ],
    'demo': [
    ],
}
