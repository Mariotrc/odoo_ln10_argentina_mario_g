# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (C) 2012 OpenERP - Team de Localización Argentina.
# https://launchpad.net/~openerp-l10n-ar-localization
#
# This program isfree software: you can redistribute it and/or modify
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
{
    'name' : 'Retenciones', 
    'version' : '2.1',
    'author':   'OpenERP - Team de Localización Argentina',
    'category': 'Localization/Argentina',
    'website':  'https://launchpad.net/~openerp-l10n-ar-localization',
    'license':  'AGPL-3',
    'description' : '''
Modulo de configuracion y aviso de retencion a proovedores
Al momento de realizar un pago, calcula el neto sin impuestos pagado en el periodo actual
y de ser necesario, alerta sobre la necesidad de emitir una retencion

    ''',
    'depends' : ['base','account','account_payment'],
    'init_xml' : [],
    'demo_xml' : [],
    'update_xml' : [
        'data/retenciones_view.xml',
        'data/vouchers_view.xml',
        'security/retenciones_security.xml',
        'data/conf_ret_view.xml',
        'data/partner_view.xml',
        
    ],
    'active': False 
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
