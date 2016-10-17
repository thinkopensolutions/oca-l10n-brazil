# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
# Copyright (C) 2009 - TODAY Renato Lima - Akretion                           #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

{
    'name': 'Brazilian Localisation Data Extension for Base',
    'license': 'AGPL-3',
    'author': 'Akretion, Odoo Community Association (OCA)',
    'version': '9.0.1.0.1',
    'depends': [
        'l10n_br_base',
    ],
    'data': [
        'data/res.bank.csv',
    ],
    'demo': [],
    'category': 'Localisation',
    'installable': False,
    'auto_install': True,
}
