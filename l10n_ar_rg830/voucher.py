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
import time
from openerp.osv import osv, fields
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class account_voucher_ret(osv.osv):
    _inherit = 'account.voucher'
    
    _columns = {
                'retencion_ids' : fields.many2many('account.retenciones',
                                'account_voucher_retenciones_rel',
                                'voucher_id',
                                'retencion_id',
                                'Associated Retenciones'), 
                'pago_neto' :fields.float('Pago Neto', digits_compute=dp.get_precision('Account')),
                'ret_type': fields.related('journal_id','ret_type',type='boolean', string='Retention Type', readonly=True,),
	}
    
    def pay_prev(self, cr, uid, ids, partner_id, date, context=None):
        
        
        partner_pool=self.pool.get('res.partner')

        ret_conf_pool=self.pool.get('conf.ret')
        voucher_rg830_pool=self.pool.get('voucher.rg830.rel')

        if partner_id :
            period_pool = self.pool.get('account.period')
            pids = period_pool.find(cr, uid, date)
            period_id = pids[0]
            pay_prev={}
            
            
            reg_partner = partner_pool.browse(cr, uid, partner_id, context=None)
            
            pay_prev = {
            'value': {'id_ret': [] ,'pay_prev': [] ,'ret_pay_prev':[],},
                }
                
            if reg_partner and reg_partner.reten_gan != 'exento':

                #Obtenemos lista de diarios de retencion (list_journal_ret_id)
                        
                ret_conf_id=ret_conf_pool.search(cr, uid,[], context=None)
                list_journal_ret_id=[]
                for rt in ret_conf_id:
                    data_ret=ret_conf_pool.browse(cr,uid,rt,context=None)
                    ws=data_ret.journal_id.id
                    if ws and ws not in list_journal_ret_id:
                        list_journal_ret_id.append(ws)                
                    pay_prev['value']['id_ret']=list_journal_ret_id
                list_inv=[]
                #Calculo de pagos hechos al poovedor:
                #Obtenemos lista de vouchers del periodo actual del proovedor
                
                pagos=voucher_rg830_pool.search(cr,uid,[('partner_id', '=', partner_id), ('periodo_id','=', period_id)],context=None)
                importe = 0.00
                    
                for pg in pagos:
                     dat_pg=voucher_rg830_pool.browse(cr,uid,pg,context=None)
                     if dat_pg['invoice_id']['id'] not in list_inv:
                         list_inv.append(dat_pg['invoice_id']['id'])
                for inv in list_inv:
                     combo=[] 
                     pag_invo=voucher_rg830_pool.search(cr,uid,[('invoice_id', '=', inv)],context=None)   
                     for fg in pag_invo:
                          dat_fg=voucher_rg830_pool.browse(cr,uid,fg,context=None)
   
                          cs={'id_ret':dat_fg['consept_rg830_id']['id'],'monto':dat_fg['neto'], 'voucher_id': dat_fg['voucher_id']['id'], 'receipt_id': dat_fg['receipt_id']['id'], 'resto': dat_fg['residual_consept']}
                          combo.append(cs)
                     ju={inv:combo}
                     pay_prev['value']['pay_prev'].append(ju)
                
                
            return pay_prev
               
    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        receipt_id=None
        keis=context.keys()
        if 'default_receipt_id'in keis:
            receipt_id = context['default_receipt_id']
        if amount > 0.00:
            result = super(account_voucher_ret,self).onchange_amount(cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context)
            partner_pool=self.pool.get('res.partner')
            ret_conf_pool=self.pool.get('conf.ret')
            
        if context.get('type','sale') in ('purchase', 'payment') and partner_id and amount > 0.00:
            period_pool = self.pool.get('account.period')
            pids = period_pool.find(cr, uid, date)
            period_id = pids[0]
            res = self.pay_prev(cr, uid, ids, partner_id, date, context=context)
            result['value']['pay_actual']=[]
            reg_partner=False
            partner_con='no inscripto'
            if partner_id:
                reg_partner = partner_pool.browse(cr, uid, partner_id, context=None)
                if reg_partner.reten_gan:
                    partner_con= reg_partner.reten_gan
            line_dr=result['value']['line_dr_ids']
            line_cr= result['value']['line_cr_ids']
            data_voucher=[]   
            list_id_ret=res['value']['id_ret']    
            lista_ret=ret_conf_pool.search(cr, uid, [], context=None)   
            
            if line_dr:
                for ze in line_dr:
                     data_voucher.append(ze)
            if line_cr :
                for za in line_cr:
                     data_voucher.append(za)
            context['data_voucher']=data_voucher
            calculo_830=self.calculo_rg830(cr,uid,ids,partner_id,data_voucher,context=context)
            for rest in res['value']['pay_prev']:
                calculo_830.append(rest)
            pay_actual=calculo_830
            
            #Calculo de los montos a retener        
            compute_retention=self.compute_retention(cr,uid,ids,partner_id,pay_actual,period_id,amount,context=context)
            mensaje= compute_retention['mensaje']            
            if  journal_id not in list_id_ret and partner_con != 'exento':                
                if mensaje:
                
                    result['warning']={'title': _('Aviso de Retención'),
                                 'message': _("El importe mensual exige lo siguiente: "
                                                 "\n %s ")% (mensaje) }
                
                return result        
                            
            if journal_id in list_id_ret:   
                result['value']['pago_neto']=0.0
                result['warning']={'title': _('Aviso de Retención'),
                                   'message': _("Esta a punto de ingrezar una retención ")}
                if compute_retention['numeros']:
                    result['numero']= compute_retention['numeros']                        
                return result
        else:
            return True

    def compute_retention(self,cr,uid,ids,partner_id,pay_actual,period_id,amount,context=None):
        reg_partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=None)
        if partner_id and reg_partner.reten_gan:
            respon = reg_partner.reten_gan 
        else: 
            respon = 'noinscripto'
        mensaje=""
        receipt_id = context['default_receipt_id']
        pagos_acumulados=[]
        ret_tot_gan=0.0
        for bh in pay_actual:
             inv_id=bh.keys()[0]
             for po in bh[inv_id] :
                 pagos_acumulados.append(po)
        list_ret= self.pool.get('conf.ret').search(cr,uid,[])
        pago_total=[]
        sub_l=[]
        numeros=[]
        
        totla_pagos=tuple(pagos_acumulados)
        for lista in list_ret:
   
            for pa in totla_pagos:
                id_ret=pa['id_ret']
                monto=pa['monto']
                
                if pa['id_ret']== lista:
                       
                    if lista not in sub_l:
                        hj={'id_ret':id_ret , 'monto':monto,}
                        pago_total.append(hj) 
                        sub_l.append(lista)
 
                    else:
                        for pl in pago_total:
                             
                             if pl['id_ret'] == lista:
                                 pl['monto'] +=monto

        for com_ret in pago_total:
             ret_paga=0.0
             ret_pagadas=self.pool.get('account.retenciones').search(cr,uid,[('partner_id','=', partner_id), ('periodo_id','=', period_id),('reten_gan', '=', com_ret['id_ret'])])
             for rp in ret_pagadas:
                 amount_ret=self.pool.get('account.retenciones').browse(cr, uid, rp)
                 ret_paga += amount_ret['amount']
             dat_ret= self.pool.get('conf.ret').browse(cr,uid,com_ret['id_ret'])
             impuesto=dat_ret['impuesto']
             consepto=dat_ret['name']
             pagos_tot = com_ret['monto']
             if respon == 'inscripto':
                 metodo=dat_ret.metodo
                 neto_imputable= dat_ret.neto
                 monto_min=dat_ret.importe_min
                 if dat_ret.metodo == 'porcentaje':  
                     alicuota=dat_ret.porcentaje/100
                 else:
                      alicuota=0.0
             if respon == 'noinscripto':
                 neto_imputable = 0.00
                 monto_min = dat_ret.importe_min_no_ins
                 alicuota=dat_ret.porcentaje_no_ins /100
                 metodo= 'porcentaje'   
             
             pagos_str=format(pagos_tot, '.2f')
             neto_str=format(neto_imputable, '.2f')

             if pagos_tot > neto_imputable:
                 if metodo == 'porcentaje':
                     monto_ret = (pagos_tot - neto_imputable) * alicuota
                 else:
                     data_tabla=self.pool.get('ret.escala').search(cr, uid,[('desde', '<', pagos_tot),('hasta', '>', pagos_tot)], context=None)
                     tabla_browse= self.pool.get('ret.escala').browse(cr, uid, data_tabla[0], context=None)
                     monto_ret=tabla_browse.monto + (((pagos_tot-neto_imputable) - tabla_browse.exedente_de)* (tabla_browse.porcen_mas/100))
                 ret_tot =monto_ret-ret_paga
                 ret_str=format(ret_tot, '.2f')
                 if ret_tot > monto_min:
                     ret_tot_gan += ret_tot
                     total_retencion=format(ret_tot_gan,'.2f')
                     cd={
                         'reten_gan':com_ret['id_ret'],
                         'amount': ret_tot,
                         'total_imput':pagos_tot,
                         'ret_prev':ret_paga,
                         }
                     numeros.append(cd)  
                     mensaje +=  "\n Retencion de: " + impuesto + "\n Consepto: " + consepto + "\n Importe a retener: $ " + ret_str + "\n Pagos totales (Neto):$ " + pagos_str + "\n Minimo imputable: $ " + neto_str + "\n"    
        amount_ajuste= amount - ret_tot_gan 
        amount_aj=format(amount_ajuste, '.2f')
        if mensaje: 
            mensaje += "\n Total retencion: " + total_retencion + "\n Ajuste de pago: " + amount_aj + "\n"
        result={'mensaje': mensaje, 'numeros': numeros}
        return result
 
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        
        
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
            if line.move_id.id:
                se_audit_cr=self.pool.get('account.voucher').search(cr,uid,[('move_id', '=', line.move_id.id)])
                
                if se_audit_cr:
                    audit_cr=self.pool.get('account.voucher').browse(cr,uid,se_audit_cr[0]).audit
                    return audit_cr
                se_audit_dr=self.pool.get('account.invoice').search(cr,uid,[('move_id', '=', line.move_id.id)])
                if se_audit_dr:
                    audit_dr=self.pool.get('account.invoice').browse(cr,uid,se_audit_dr[0]).pay
                    return audit_dr
            return False

        if context is None:
            context = {}
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.voucher.line')
        
        #set default values
        default = {
            'value': {'line_dr_ids': [] ,'line_cr_ids': [] ,'pre_line': False,},
        }
        #default['value']['line_dr_ids']['pay']=True
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

        total_credit = 0.0
        total_debit = 0.0
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
                if abs(line.amount_residual-price)<0.01:
                    #if the amount residual is equal the amount voucher, we assign it to that voucher
                    #line, whatever the other voucher lines
                    move_line_found = line.id
                    break
                #otherwise we will split the voucher amount on each line (by most old first)
                total_credit += line.credit or 0.0
                total_debit += line.debit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
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
            }
           
        
            #in case a corresponding move_line hasn't been found, we now try to assign the voucher amount
            #on existing invoices: we split voucher amount by most old first, but only for lines in the same currency
            if not move_line_found:
                if currency_id == line_currency_id:
                    if line.credit:
                        amount = min(amount_unreconciled, abs(total_debit))
                        rs['amount'] = amount
                        total_debit -= amount
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

    
       

account_voucher_ret()

class account_voucher(osv.osv):
    _inherit = "account.voucher"
    
    def proforma_voucher(self, cr, uid, ids, context=None):
        super(account_voucher,self).proforma_voucher(cr, uid, ids, context=context)
        for vouch in self.browse(cr,uid,ids,context=context):
            amount_vou=vouch['amount']
            partner_id=vouch['partner_id'].id
            voucher=ids[0]
            receipt_id=vouch['receipt_id'].id
            data_voucher=[]
            journal_id=vouch['journal_id'].id
            periodo_id=vouch['period_id'].id
            payment_rate_currency_id=vouch['payment_rate_currency_id'].id
            ttype=vouch['type']
            currency_id=vouch.company_id.currency_id.id
            date=vouch['date']
            company_id=vouch['company_id'].id
            rate=vouch['payment_rate']
        context={'type': ttype,'default_receipt_id':receipt_id,}    
        voucher_line=self.calculo_rg830(cr, uid, ids,partner_id,data_voucher, context)
        voucher_rg_rel_pool=self.pool.get('voucher.rg830.rel')
        if voucher_line:
            for line_c in voucher_line:
                invoice_id=line_c.keys()[0]
                for line_v in line_c[invoice_id]:  
                     vals={'voucher_id':voucher, 'periodo_id': periodo_id, 'partner_id':partner_id, 'journal_id': journal_id, 'consept_rg830_id': line_v['id_ret'], 'neto':line_v['monto'], 'amount': amount_vou, 'receipt_id': receipt_id,'invoice_id': invoice_id,'residual_consept': line_v['resto']}
                     data_in=voucher_rg_rel_pool.create(cr,uid,vals,context)
        ret_conf_pool=self.pool.get('conf.ret')
        ret_conf_id=ret_conf_pool.search(cr, uid,[], context=None)
        list_journal_ret_id=[]
        for rt in ret_conf_id:
            data_ret=ret_conf_pool.browse(cr,uid,rt,context=None)
            ws=data_ret.journal_id.id
            if ws and ws not in list_journal_ret_id:
                list_journal_ret_id.append(ws) 
                
        

        return True
       
    def cancel_voucher(self, cr, uid, ids, context=None):
        super(account_voucher,self).cancel_voucher(cr, uid, ids, context)
        voucher_rg_rel_pool=self.pool.get('voucher.rg830.rel')
        vouch_search=voucher_rg_rel_pool.search(cr, uid,[('voucher_id','=',ids[0])], context=None)
        for cut in vouch_search:
            out=voucher_rg_rel_pool.unlink(cr,uid,cut,context=None)
        return True
    
    def calculo_rg830(self, cr,uid,ids,partner_id,data_voucher,context=None):
        receipt_id=None
        if context:
            receipt_id = context['default_receipt_id']
        ids_ret=self.pool.get('conf.ret').search(cr,uid,[],context=None)
        pool_escala=self.pool.get('ret.escala')
        calculo={'product_ret':[]}
        date=  time.strftime('%Y-%m-%d'),
        period_pool = self.pool.get('account.period')
        pids = period_pool.find(cr, uid, date)
        period_id = pids[0]
        lista_ret=[]
        lista_rete=[]
        calculate_tot=[]
        res = self.pay_prev(cr, uid, ids, partner_id, date, context=context)
        pay_prev= res['value']['pay_prev']
        if data_voucher:
            datos_vou= data_voucher
        
        else:    
            if ids:
                datos_vou= self.pool.get('account.voucher.line').search(cr,uid,[('voucher_id', '=', ids[0])],context=None)
        for line in datos_vou: 
            
            importe=0.0
            resp_partner='no inscripto'
            partner_res=self.pool.get('res.partner').browse(cr,uid,partner_id)['reten_gan']
            if partner_res: resp_partner=partner_res
            if data_voucher:
                  line_voucher = line
                  move_id = self.pool.get('account.move.line').browse(cr,uid,line_voucher['move_line_id'],context=None).move_id.id
            
            else:
                 if ids:   
                     line_voucher=self.pool.get('account.voucher.line').browse(cr,uid,line)
                     move_id = line_voucher.move_line_id.move_id.id
            sen=1
            if line_voucher['type'] == 'cr':
                sen=-1
            lista_rete=[]
            ty={}
            invoice=self.pool.get('account.invoice').search(cr,uid,[('move_id', '=', move_id)], context=None)
            invoice_dat=self.pool.get('account.invoice').browse(cr,uid,invoice[0])
            amount_tot=invoice_dat['amount_total']
            
            amount_untax_line_voucher=(line_voucher['amount']/invoice_dat['amount_total']) * invoice_dat['amount_untaxed']
            calculate=[]
            for inv_line in self.pool.get('account.invoice.line').search(cr,uid,[('invoice_id','=',invoice[0])]):
                lines=self.pool.get('account.invoice.line').browse(cr,uid,inv_line)
                id_ret=lines.product_id.reten_gan.id
                if not id_ret:
                    id_ret=self.pool.get('conf.ret').search(cr,uid,[('default', '=', True)])[0]
                
                price_sub=lines.price_subtotal
                pay_ant=self.pool.get('voucher.rg830.rel').search(cr,uid,[('partner_id', '=', partner_id), ('periodo_id','<>', period_id),('invoice_id','=',invoice[0]),('consept_rg830_id','=',id_ret)],context=None)
                resto_ant=[]
                pay_previo=self.pool.get('voucher.rg830.rel').search(cr,uid,[('partner_id', '=', partner_id), ('periodo_id','=', period_id),('invoice_id','=',invoice[0]),('consept_rg830_id','=',id_ret)],context=None)
                resto_previo=[]
                if pay_ant:
                    for pa in pay_ant:
                         anteriores=self.pool.get('voucher.rg830.rel').browse(cr,uid,pa)
                         resto_ant.append(anteriores['residual_consept'])
                    resto_men=min(resto_ant)
                    if price_sub>resto_men:
                        price_sub = resto_men
                if pay_previo:
                    for pp in pay_previo:
                         previos=self.pool.get('voucher.rg830.rel').browse(cr,uid,pp)
                         resto_previo.append(previos['residual_consept'])
                    resto_men=min(resto_previo)
                    if price_sub>resto_men:
                        price_sub = resto_men
                """
                if pay_prev:
                    for prev in pay_prev:
                        
                        if prev.keys()[0]== invoice[0]:
                           
                            for tr in prev[prev.keys()[0]]:
                                if tr['id_ret']== id_ret:
                                   if price_sub > tr['resto']:
                                       price_sub=tr['resto']
               """
   
                
                
                if amount_untax_line_voucher - price_sub >= -0.001:
                    monto=price_sub * sen
                    resto= 0.00
                    amount_untax_line_voucher -= price_sub 
                    if amount_untax_line_voucher  < 0  : amount_untax_line_voucher=0.00
                else:
                    monto=amount_untax_line_voucher * sen
                    resto=price_sub - monto
                    amount_untax_line_voucher=0.0
                
                dic={
                     'resto': resto,
                     'id_ret':id_ret,
                     'monto':monto,
                     'receipt_id': receipt_id,
                     }
                if not calculate:
                   calculate.append(dic)
                   lista_rete.append(id_ret)
                else:
                   for tr in calculate:
                       if id_ret not in lista_rete:
                           lista_rete.append(id_ret) 
                           calculate.append(dic)
                           break
                       else:
                           if id_ret==tr['id_ret']:
                              tr['monto'] += monto
                           else: continue
                """
                if not calculo['product_ret']:
                   calculo['product_ret'].append(dic)
                   lista_ret.append(id_ret)
                else:
                   for li in calculo['product_ret']:
                       if id_ret  not in lista_ret:
                           lista_ret.append(id_ret)
                           calculo['product_ret'].append(dic)
                           break
                       else:
                           if id_ret == li['id_ret']:
                               li['monto'] += monto
                           else:continue """
            
            ty={invoice[0]:calculate}
            
            calculate_tot.append(ty)
        return calculate_tot
        
    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):        

        reten = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)
        if not reten:
            reten = {}
        reten['value']['ret_type'] = False
        ret_ids=self.pool.get('conf.ret').search(cr,uid,[('journal_id','=', journal_id),])
        if ret_ids:
            reten['value']['ret_type'] = True
        return reten
account_voucher()

class account_voucher_line(osv.osv):
    
    _inherit ='account.voucher.line'
    
    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
        vals = {}
        if amount:
            vals['reconcile'] = (0.001>(amount - amount_unreconciled)>-0.001 )
        return {'value': vals}
account_voucher_line() 

class account_invoice(osv.osv):
     _inherit = 'account.invoice'
    
    
     _columns={
            'pay': fields.boolean('No pagar'),
           }
      
account_invoice()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
