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
from openerp.tools.translate import _


class account_voucher_receipt (osv.osv):
       
    _name = "account.voucher.receipt" 
    _description = 'Account Voucher Receipt'

    def _get_has_vouchers(self, cr, uid, ids, name, args, context=None):
        res = {}
        for receipt in self.browse(cr, uid, ids, context=context):
            if receipt.voucher_ids:
                res[receipt.id] = True
            else:
                res[receipt.id] = False
        return res

    _columns = {
            'name':fields.char(string='Receipt Number', size=128, required=False, readonly=True, ),
            'manual_prefix': fields.related('receiptbook_id', 'manual_prefix', type='char', string='Prefix', readonly=True,),
            'manual_sufix': fields.char('Sufix', readonly=True, states={'draft':[('readonly',False)]}),
            'force_number': fields.char('Force Number', readonly=True, states={'draft':[('readonly',False)]}),
            'receiptbook_id': fields.many2one('account.voucher.receiptbook','ReceiptBook',readonly=True,required=True, states={'draft':[('readonly',False)]}),   
            'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
            'date': fields.date('Receipt Date', readonly=True, states={'draft':[('readonly',False)]}),
            'partner_id':fields.many2one('res.partner', string='Partner', readonly=True, required=True, states={'draft':[('readonly',False)]}),
            'voucher_ids':fields.one2many('account.voucher','receipt_id',string='Vouchers Lines', readonly=True, states={'draft':[('readonly',False)]}),
            'type': fields.selection([('receipt','Receipt'),
                                             ('payment','Payment')],'Type', required=True),
            'state': fields.selection([('draft','Draft'),('posted','Posted'),('cancel','Cancel')], string='State', readonly=True,),
            'next_receipt_number': fields.related('receiptbook_id', 'sequence_id', 'number_next', type='integer', string='Next Receipt Number', readonly=True),
            'receiptbook_sequence_type': fields.related('receiptbook_id', 'sequence_type', type='char', string='Receiptbook Sequence Type', readonly=True),
            'has_vouchers': fields.function(_get_has_vouchers, type='boolean', string='Has Vouchers?',),
            
                }
                
    _sql_constraints = [('name_uniq','unique(name,type)','The Receipt Number must be unique!')]

    _order = "date desc, id desc"

    def _get_receiptbook(self, cr, uid, context=None):
        if not context:
            context = {}
        print 'context', context
        receiptbook_ids = self.pool['account.voucher.receiptbook'].search(cr, uid, [('type','=',context.get('type',False))], context=context)
        return receiptbook_ids and receiptbook_ids[0] or False
    
    _defaults = {
        'receiptbook_id': _get_receiptbook, 
        'date': fields.date.context_today,
        'state': 'draft',
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.voucher.receipt',context=c),        
    }

    def unlink(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            if record.state == 'posted':
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a posted receipt.'))
            if record.voucher_ids:
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete a receipt that has vouchers.'))
        return super(account_voucher_receipt, self).unlink(cr, uid, ids, context) 

    def post_receipt(self, cr, uid, ids, context=None):
        obj_sequence = self.pool.get('ir.sequence')
        for receipt in self.browse(cr, uid, ids, context=context):
            if not receipt.voucher_ids:
                raise osv.except_osv(_('Invalid Action!'), _('Cannot post a receipt that has no voucher(s).'))
            for voucher in receipt.voucher_ids:
                if voucher.state != 'posted':
                    raise osv.except_osv(_('Invalid Action!'), _('Cannot post a receipt that has voucher(s) on draft or cancelled state.'))
            if receipt.force_number:
                self.write(cr, uid, [receipt.id], {'name':receipt.force_number}, context=context)                
            elif receipt.receiptbook_id.sequence_type == 'automatic':
                sequence = obj_sequence.next_by_id(cr, uid, receipt.receiptbook_id.sequence_id.id, context=context)
                self.write(cr, uid, [receipt.id], {'name':sequence}, context=context)                
            elif receipt.receiptbook_id.sequence_type == 'manual':
                self.write(cr, uid, [receipt.id], {'name':receipt.manual_prefix + receipt.manual_sufix}, context=context)
            self.write(cr, uid, [receipt.id], {'state': 'posted'}, context=context)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        
        res = {
            'state':'draft',
        }
        self.write(cr, uid, ids, res)
        return True

    def cancel_receipt(self, cr, uid, ids, context=None):
        res = {
            'state':'cancel',
        }
        self.write(cr, uid, ids, res)
        return True        

    def new_payment_normal(self, cr, uid, ids, context=None):
        # TODO add on context if dialog or normal and depending on this open on or other view. 
        # Better if only one veiw
        # TODO this function should be only called for one id
        if not ids: return []
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        receipt = self.browse(cr, uid, ids[0], context=context)
        new_context = context.copy()
        new_context = {
            'default_partner_id': receipt.partner_id.id,
            'default_receipt_id': receipt.id,
            'default_date': receipt.date,
            'default_receiptbook_id': receipt.receiptbook_id.id,
            'show_cancel_special': True,                    
            'show_cancel_special': True,      
            'from_receipt': True,
        }
        if context.get('type', False) == 'receipt':
            action_vendor = mod_obj.get_object_reference(cr, uid, 'account_voucher', 'action_vendor_receipt')
        elif context.get('type', False) == 'payment':
            action_vendor = mod_obj.get_object_reference(cr, uid, 'account_voucher', 'action_vendor_payment')
        action_vendor_id = action_vendor and action_vendor[1] or False
        action_vendor = act_obj.read(cr, uid, [action_vendor_id], context=context)[0]
        action_vendor['target'] = 'new'
        action_vendor['context'] = new_context
        action_vendor['views'] = [action_vendor['views'][1],action_vendor['views'][0]]
        return action_vendor        