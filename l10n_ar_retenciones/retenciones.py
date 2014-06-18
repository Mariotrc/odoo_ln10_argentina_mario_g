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
import time

class retenciones_document (osv.osv):
	_name = "account.retenciones"
	_columns = {
                'name' : fields.char('Document ID',size=64, select=1, required=True,
                                     readonly=True, states={'draft':[('readonly',False)]}), 
                'partner_id' : fields.many2one('res.partner','Partner', required=True,
                                     readonly=True,states={'draft':[('readonly',False)]}, 
                                     help="Partner who made the pay with this document."),
                'invoice_id' : fields.many2one('account.invoice','Invoice', required=True,
                                     readonly=True,states={'draft':[('readonly',False)]}, 
                                     help="Factura Relacionada."),  
                'user_id' : fields.many2one('res.users','User', required=True,
                                     readonly=True,states={'draft':[('readonly',False)]}, 
                                     help="User who receive this document."), 
                'company_id': fields.many2one('res.company', 'Company', required=True,
                                     readonly=True, states={'draft':[('readonly',False)]}, 
                                     help="Company related to this treasury"),
		'amount': fields.float('Amount', digits=(16,2), required=True,
                                     readonly=True, states={'draft':[('readonly',False)]}, 
                                     help="Value of the Treasure"),
		'reception_date' : fields.date('Reception Date', required=True,
                                     readonly=True, states={'draft':[('readonly',False)]}),
		'emission_date' : fields.date('Emission Date', required=True,
                                     readonly=True, states={'draft':[('readonly',False)]}),

		'done_date' : fields.date('Solved Date', readonly=True),

		'type' : fields.selection([ ('re','retencion emitida'), ('rs','retencion sufrida'), ('pe','percepcion emitida'), ('ps','percepcion sufrida'), ], 'Document Type', required=True, select=1,
                                     readonly=True, states={'draft':[('readonly',False)]}),
		'state' : fields.selection([
                                ('draft','Open'),
                                ('valid','Valid'),
                                ('clearing','Clearing'),
                                ('paid','Paid'),
                                ('rejected','Rejected'),
                                ('cancel','Cancelled'),
                                ], 'State', required=True, readonly=True, select=1),
		'note' : fields.text('Notes'),
                'voucher_ids' : fields.many2many('account.voucher',
                                'account_voucher_retenciones_rel',
                                'retencion_id',
                                'voucher_id',
                                'Associated Vouchers'), 
		}
        _defaults = {
                'state': 'draft',
                'user_id': lambda self, cr, uid, context: uid,
                'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
                'reception_date': lambda *a: time.strftime('%Y-%m-%d'),
        }
        _order = "invoice_id"

        def button_validate(self, cr, user, ids, context=None):
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s '\
                   'WHERE id IN %s AND state=%s',
                   ('valid', tuple(ids), 'draft'))
                return True

        def button_clearing(self, cr, user, ids, context=None):
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s '\
                   'WHERE id IN %s AND state=%s',
                   ('clearing', tuple(ids), 'valid'))
                return True

        def button_paid(self, cr, user, ids, context=None):
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s, done_date=%s'\
                   'WHERE id IN %s AND state=%s',
                   ('paid', time.strftime('%Y-%m-%d'), tuple(ids), 'clearing'))
                return True

        def button_rejected(self, cr, user, ids, context=None):
                # TODO: Ejecutar el armado de nota de debito por cheque rechazado!
                # Ver si el cheque fue emitido por la empresa, si es asi deberia generar
                # una nota de credito al proveedor.
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s, done_date=%s'\
                   'WHERE id IN %s AND state=%s',
                   ('rejected', time.strftime('%Y-%m-%d'), tuple(ids), 'clearing'))
                return True

        def button_cancel(self, cr, user, ids, context=None):
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s '\
                   'WHERE id IN %s AND state IN %s',
                   ('cancel', tuple(ids), ('draft', 'valid')))
                return True

        def button_draft(self, cr, user, ids, context=None):
                cr.execute('UPDATE account_retenciones '\
                   'SET state=%s '\
                   'WHERE id IN %s AND state IN %s',
                   ('draft', tuple(ids), ('cancel')))
                return True

retenciones_document ()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
