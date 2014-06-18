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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_voucher (osv.osv):
    _inherit = 'account.voucher'
    _columns = {
                'retencion_ids' : fields.many2many('account.retenciones',
                                'account_voucher_retenciones_rel',
                                'voucher_id',
                                'retencion_id',
                                'Associated Retenciones'), 
                'pago_neto' :fields.float('Pago Neto', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
	}
    _defaults = {'pago_neto':0.0}
    

               
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        
        result = super(account_voucher,self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None)
        partner_pool=self.pool.get('res.partner')
        if context.get('type', 'sale') in ('purchase', 'payment'):
            view_type = 'form'
            period_pool = self.pool.get('account.period')
            
            pids = period_pool.find(cr, uid, date)
            period_id = pids[0]
            if partner_id and amount > 0:
                reg_partner = partner_pool.browse(cr, uid, partner_id, context=None)
                neto_imputable = reg_partner.reten_gan.neto
                impuesto = reg_partner.reten_gan.impuesto
                alicuota=reg_partner.reten_gan.porcentaje/100
                monto_min=reg_partner.reten_gan.importe_min
                tipo_ret=reg_partner.reten_gan.name
                pago_neto = result['value']['pago_neto']
                state='posted'
                type='payment'
                
                cr.execute('select sum(pago_neto) from account_voucher where ' \
                        'period_id=%s and partner_id=%s and state = %s and type = %s ',(period_id, partner_id, state, type ))
                pagos=cr.fetchone()[0] or 0.0
                pagos_tot=pagos + pago_neto

                number='RG%'
                cr.execute('select sum(amount) from account_voucher where ' \
                        'period_id=%s and partner_id=%s and state = %s and type = %s and number like %s ',(period_id, partner_id, state, type, number ))
                ret_ganancias=cr.fetchone()[0] or 0.0
                if pagos_tot > neto_imputable:
                    monto_ret = (pagos_tot - neto_imputable) * alicuota
                    if monto_ret > monto_min:
                        result['warning']={'title': _('Aviso de Retención'),
                                   'message': _("El importe mensual exige lo siguiente: "
                                                " Pagos totales (Neto):$ %s "
                                                " Minimo imputable: $ %s "
                                                " Retencion de: %s "
                                                " Importe a retener: $ %s ")% (pagos_tot, neto_imputable, impuesto, monto_ret) }

        return result
        
       
    def chek_neto(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        result = super(account_voucher,self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None)
    
        if context.get('type', 'sale') in ('purchase', 'payment'):
            view_type = 'form'
            period_pool = self.pool.get('account.period')
            pids = period_pool.find(cr, uid, date)
            period_id = pids[0]
            if partner_id and amount > 0:
                state='posted'
                type='payment'
                number='R%'
                cr.execute('select sum(amount) from account_voucher where ' \
                        'period_id=%s and partner_id=%s and state = %s and type = %s and number not like %s ',(period_id, partner_id, state, type, number ))
                pagos=cr.fetchone()[0] or 0.0
                pagos_tot=pagos + amount

                number='RG%'
                cr.execute('select sum(amount) from account_voucher where ' \
                        'period_id=%s and partner_id=%s and state = %s and type = %s and number like %s ',(period_id, partner_id, state, type, number ))
                ret_ganancias=cr.fetchone()[0] or 0.0
                if pagos_tot >= 12000:
                    result['warning']={'title': _('Aviso de Retención'),
                                   'message': _('El importe mensual exige lo siguiente: Pagos totales: $ %s')% pagos_tot}

        return result

    def recompute_voucher_lines(self, cr, uid, ids,  partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency <= 0:
                        return True
                else:
                    if line.amount_residual <= 0:
                        return True
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})
        
        invoice_pool=self.pool.get('account.invoice')
        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')

        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default
        if 'pago_neto' in locals():
            pass
        else:
            pago_neto=0.0
        total_credit = 0.0
        total_debit = 0.0
        inv_untax=0.0
        account_type = 'receivable'
        if ttype == 'payment':
            account_type = 'payable'
            total_debit = price or 0.0
        else:
            total_credit = price or 0.0
            account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)], context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the voucher line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other voucher lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if abs (line.amount_residual - price)<0.01:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    ids = [move_line_found,]
                    account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
              
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if abs(line.amount_residual_currency - price)<0.01:
                    move_line_found = line.id
                    ids = [move_line_found,]
                    account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)
                    break
                total_credit += line.credit and line.amount_currency or 0.0
                total_debit += line.debit and line.amount_currency or 0.0

        #voucher line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id==line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or line.debit or 0.0)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual))
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            number=line.move_id.name#add
           
            if number.startswith("FC"):
                inv_id=self.pool.get('account.invoice').search(cr, uid, [('number','=',number)], context=context)#add
                invoice_data=self.pool.get('account.invoice').browse(cr, uid, inv_id[0], context=context)
                inv_untax=invoice_data['amount_untaxed']#add
            
            
            rs = {
                       'name':line.move_id.name,
                       'type': line.credit and 'dr' or 'cr',
                       'move_line_id':line.id,
                       'account_id':line.account_id.id,
                       'amount_original': amount_original,
                       'amount': (move_line_found == line.id) and min(abs(price), amount_unreconciled) or 0.0,
                       'date_original':line.date,
                       'date_due':line.date_maturity,
                       'amount_unreconciled': amount_unreconciled,
                       'currency_id': line_currency_id,
                       'inv_untax':inv_untax or 0.0,
                       'neto':pago_neto,
                       }
           
            
            
            
            
            if move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        pago_neto=(price/amount_original)*inv_untax
                        default['value']['pago_neto'] = pago_neto
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            else:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
                        
                        neto_pagado=(amount/amount_original)*inv_untax
                        rs['neto'] +=neto_pagado
                        pago_neto = rs['neto']
                        default['value']['pago_neto'] = pago_neto
                
                    else:
                        amount = min(amount_unreconciled, abs(total_credit))
                        rs['amount'] = amount
                        total_credit -= amount
           
                        
            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True

            if rs['type'] == 'cr':
                default['value']['line_cr_ids'].append(rs)
            else:
                default['value']['line_dr_ids'].append(rs)

            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
                default['value']['pre_line'] = 1
            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
                default['value']['pre_line'] = 1
            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price, ttype)
        return default
account_voucher()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
