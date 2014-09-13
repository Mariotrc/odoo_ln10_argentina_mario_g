# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2012 OpenERP - Team de Localización Argentina.
# https://launchpad.net/~openerp-l10n-ar-localization
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{   'active': False,
    'author': 'OpenERP - Team de Localizaci\xc3\xb3n Argentina',
    'category': 'Accounting & Finance',
    'data': [   
                'account_voucher_view.xml',
                'account_voucher_receipt_view.xml',
                'account_voucher_receiptbook_view.xml',
                'workflow/account_voucher_receipt_workflow.xml',
                'security/account_voucher_receipt_security.xml',
                'security/ir.model.access.csv',
                ],
    'demo': [],
    'depends': ['account_voucher'],
    'description': '''
TODO:
* Ver si en invoice, en las pestaña pagos, mostramos mas los vouchers que los apuntes
* Que solo se pueda confirmar un recibo si todos los voucher asociados están validados
* Agregar en otro modulo reporte de recibo y botones 
''',
    'installable': True,
    'name': 'Receipt',
    'test': [],
    'version': '1.243'}
