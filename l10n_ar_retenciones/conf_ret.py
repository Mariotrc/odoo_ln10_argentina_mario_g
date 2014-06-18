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
from openerp.osv import fields, osv
import re
class conf_ret(osv.osv):
    _name='conf.ret'
    _description='Configuracion de retenciones'
    _columns={
        'name': fields.char('Nombre', size=32, required=True),
        'code': fields.char('Codigo', size=8, required=True),
        'neto': fields.float('Neto Minimo Imputable',  required=True),
        
        'porcentaje': fields.float('Porcentaje',  required=True),
        'importe_min' : fields.float('Importe Minimo',  required=True),
        'impuesto': fields.selection([('ganancias','Ganancias'),('iva','IVA'),('inrgbrutos','Ingresos Brutos'),('rg1784','Seg.Social RG1784')],string='Impuesto',required=True), 
    }
    _sql_constraints = [('name','unique(name)', 'Not repeat name!'),
                        ('code','unique(code)', 'Not repeat code!'),
                        ]
conf_ret()
	     

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
