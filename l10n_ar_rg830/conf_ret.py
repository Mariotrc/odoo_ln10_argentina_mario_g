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
        'name': fields.char('Nombre', size=32),
        'descripcion': fields.char('Descripcion', size=64),
        'code': fields.char('Codigo', size=8, required=True),
        'neto': fields.float('Minimo Imputable Inscripto', required=True, help="Monto sin impuestos a partir del cual se aplica la retención" ),
        'journal_id' : fields.many2one('account.journal', 'Diario', required=False),
        'metodo':fields.selection([('porcentaje' , 'Porcentaje'),('tabla','Tabla')],string='Metodo de calculo ',size=16),
        'porcentaje': fields.float('Alicuota Inscripto',   help="ej. para 6% -> 6.00"),
        'porcentaje_no_ins': fields.float('Alicuota No Inscripto',required=True, help="ej. para 6% -> 6.00"),
        'escala' : fields.boolean('Por Escala',help="Si el monto se determina por la escala de valores"),
        'importe_min' : fields.float('Importe Minimo Inscripto',  required=True, help="Importe minimo de la retencion" ),
        'importe_min_no_ins' : fields.float('Importe Minimo No Inscripto',  required=True, help="Importe minimo de la retencion" ),
        'impuesto': fields.selection([('ganancias','Ganancias'),('iva','IVA'),('inrgbrutos','Ingresos Brutos'),('rg1784','Seg.Social RG1784')],string='Impuesto',required=True),
        'type':fields.selection([('emitida' , 'Emitida'),('sufrida','Sufrida')],string='Tipo'),
        'default': fields.boolean('Por defecto'),
    }

    _defaults = {
                'metodo': 'porcentaje',
                }
conf_ret()     

class ret_escala(osv.osv):
    _name='ret.escala'
    description='Escala de Rertenciones'
    _columns={
              'desde' : fields.float('Desde', required=True, ),
              'hasta' : fields.float('Hasta', required=True, ),
              'monto' : fields.float('Monto', required=True, ),
              'porcen_mas' : fields.float('Mas el %', required=True, ),
              'exedente_de' : fields.float('Sobre el exedente de:', required=True, ),
              }
    _defaults = {
                 'desde':0.0
                 }
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
