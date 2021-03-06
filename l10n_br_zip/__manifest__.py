# -*- coding: utf-8 -*-
# Copyright (C) 2009  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Brazilian Localisation ZIP Codes',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'version': '10.0.2.0.0',
    'depends': [
        'l10n_br_base',
        'sales_team',
    ],
    'data': [
        # 'views/l10n_br_zip_view.xml',
        # 'views/res_partner_view.xml',
        # 'views/res_company_view.xml',
        # 'views/res_bank_view.xml',
        'wizard/l10n_br_zip_search_view.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
        'test/zip_demo.yml'
    ],
    'category': 'Localization',
    'installable': True,
}
