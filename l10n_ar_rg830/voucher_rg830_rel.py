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
class voucher_rg830_rel(osv.osv):
    _name='voucher.rg830.rel'
    _description='Valores relacionados voucher-RG830'
    _columns={
        'voucher_id': fields.many2one('account.voucher', 'Voucher', required=True),
        'consept_rg830_id': fields.many2one('conf.ret', 'Consepto de retencion', required=True),
        'neto': fields.float('Neto sujeto a retencion', required=True),
        'journal_id' : fields.many2one('account.journal', 'Diario', required=False),
        'partner_id':fields.many2one('res.partner', 'Partner', required=True),
        'amount': fields.float('Amount' ),
        'importe': fields.float('Importe de la retencion',required=False),
        'periodo_id' : fields.many2one('account.period', 'Period', required=True),
        'receipt_id' : fields.many2one('account.voucher.receipt', 'Orgden de pago', required=False, ),
        'invoice_id':fields.many2one('account.invoice', 'Factura', required=False),
        'residual_consept': fields.float('Neto residual de consepto' ),
         }

voucher_rg830_rel()            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
