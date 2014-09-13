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
from openerp import netsvc
import time
import openerp.addons.decimal_precision as dp
from voucher import account_voucher_ret
from openerp.tools.translate import _

class retenciones_document (osv.osv):
    
    _name = "account.retenciones"
    _columns = {
                
         'partner_id' : fields.many2one('res.partner','Partner', required=True,
                                     readonly=True,states={'draft':[('readonly',False)]}, 
                                     help="Partner who made the pay with this document."),
                  
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
        'periodo_id' : fields.many2one('account.period', 'Period', required=True),
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
        'receipt_id' : fields.many2one('account.voucher.receipt', 'Orgden de pago', required=False, select=True),
        'reten_gan' : fields.many2one('conf.ret', 'Retencion Ganancias', required=True, select=True),
        'name' : fields.char(string='Nombre', size=20,required=False,readonly=True,),
        'actual_pay' :fields.float('Pago sujeto a retencion', digits=(16,2),help="Value of the Treasure"),
        'pay_prev' :fields.float('Pagos acumulados en el mes', digits=(16,2),help="Value of the Treasure"),
        'total_imput' :fields.float('Neto total imputado',digits=(16,2),help="Value of the Treasure"),
        'ret_prev' :fields.float('Retenciones realizadas', digits=(16,2),help="Value of the Treasure"),
        'import_calculo' :fields.float('Monto para calculo', digits=(16,2),help="Value of the Treasure"),
        'no_imputable' :fields.float('Neto no imputable', digits=(16,2),help="Value of the Treasure"),
        }
    _defaults = {
                'state': 'draft',
                'user_id': lambda self, cr, uid, context: uid,
                'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
                'reception_date': lambda *a: time.strftime('%Y-%m-%d'),
                'emission_date': lambda *a: time.strftime('%Y-%m-%d'),
               
                
        }
    _order = "name"
    
    def onchange_type(self,cr,uid, ids,type, partner_id, context=None): 
        result={}
        if type:
           if 'domain' not in result: result['domain'] = {}
           if type in ['re', 'ps']:
              result['domain'].update({'partner_id': [('supplier','=', True)],})
           if type in ['rs', 'pe']:
              result['domain'].update({'partner_id': [('customer','=', True)],})
        return result
    def onchange_partner(self, cr, uid, ids, partner_id,  reten_gan, type, emission_date,company_id,context=None):
        date=emission_date
        amount=0.0
        int(reten_gan)
        context={'default_receipt_id': None}
        result = {
                   'value': {'pay_prev': 0.0 ,'actual_pay' : 0.0, 'no_imputable':0.0},
                  }
        if type == False:
            result['warning']={'title': _('Error!!'),
                                 'message': _("Seleccione primero el tipo de Retencion...    " ) }
            return result
        else:


            res=self.pool.get('account.voucher').pay_prev( cr, uid, ids, partner_id,date,context)
            period_pool = self.pool.get('account.period')
            period_id = period_pool.find(cr, uid, date)[0]
            
            if partner_id and res['value']['pay_prev']:
                list_id_ret=[]
                pay_actual= res['value']['pay_prev']
                datos_ret=self.pool.get('account.voucher').compute_retention(cr,uid,ids,partner_id,pay_actual,period_id,amount,context=context)['numeros']
                for li in datos_ret:
                     if li['reten_gan'] not in list_id_ret:
                         list_id_ret.append(li['reten_gan'])
                if 'domain' not in result: result['domain'] = {}
                if 'value' not in result: result['value'] = {}
                if list_id_ret:
                    result['domain'].update({'reten_gan': [('id','in', list_id_ret)],})
                    
                    result['value'].update({'reten_gan': list_id_ret[0],})
                else:
                    result['domain'].update({'reten_gan': [('id','in',[])],})
                    
                    result['value'].update({'reten_gan': False, })
                    
                return result


       
    def onchange_reten_gan(self, cr, uid, ids,reten_gan, partner_id,  amount, type, emission_date,company_id,context=None):
        date=emission_date
        pagos_previos=0.0
        amount=0.0
        pagos_tot=0.00
        period_pool = self.pool.get('account.period')
        pids = period_pool.find(cr, uid, date)
        period_id = pids[0]
        result = {
                        'value': {'actual_pay': 0.0 ,'amount' : 0.0, },
                        }
        context={'default_receipt_id': None}
        res=self.pool.get('account.voucher').pay_prev( cr, uid, ids, partner_id, date,context)
        pay_actual= res['value']['pay_prev']
        if partner_id:
            condi=self.pool.get('res.partner').browse(cr,uid,partner_id)['reten_gan']
            retencion=self.pool.get('conf.ret').browse(cr,uid,reten_gan)
            no_imputable=0.0
            if condi == 'inscripto':
               no_imputable= retencion['neto']
            datos_ret=self.pool.get('account.voucher').compute_retention(cr,uid,ids,partner_id,pay_actual,period_id,amount,context=context)['numeros']
            if not self.browse(cr,uid,ids[0])['receipt_id']:
                data_receipt=self.pool.get('account.voucher.receipt').search(cr, uid,[('partner_id', '=', partner_id),  ('state', '=', 'draft')])
                receipt_id= data_receipt[0]
            else: receipt_id= self.browse(cr,uid,ids[0])['receipt_id']['id']      
            pagos_prev=self.pool.get('voucher.rg830.rel').search(cr,uid,[('partner_id','=', partner_id), ('periodo_id', '=', period_id), ('consept_rg830_id','=',reten_gan),('receipt_id','!=',receipt_id)])        
            for pp in pagos_prev:
                dato_pago=self.pool.get('voucher.rg830.rel').browse(cr,uid,pp)
                neto=dato_pago['neto']
                pagos_previos += neto
            for pa in datos_ret:
                if pa['reten_gan']==reten_gan:
                    ret_prev=pa['ret_prev']
                    amount= pa['amount']
                    pagos_tot= pa['total_imput']
                    reten_gan= pa['reten_gan']
                    pay_actual= pagos_tot - pagos_previos     
                    result['value'].update({'total_imput': pagos_tot,})
                    result['value'].update({'amount': amount,})
                    result['value'].update({'pay_prev': pagos_previos,})
                    result['value'].update({'actual_pay': pay_actual,})
                    result['value'].update({'receipt_id': receipt_id,})
                    result['value'].update({'periodo_id': period_id,})
                    result['value'].update({'ret_prev': ret_prev,})
                    result['value'].update({'no_imputable': no_imputable,})
        return result
       
       
       
    def button_validate(self, cr, user, ids, context=None):
                
                name=self.pool.get('ir.sequence').get(cr, user, 'retencion-ganacias')
                for reten in self.browse(cr, user, ids, context=context):
                     if not reten.name:
                         self.write(cr, user, [reten.id], {'name':name}, context=context)
                self.write(cr, user, ids, { 'state' : 'valid' })
             
                return  True

    def button_clearing(self, cr, user, ids, context=None):
                self.write(cr, user, ids, { 'state' : 'clearing' })
                
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
                self.write(cr, user, ids, { 'state' : 'cancel' })
                
                return True

    def button_draft(self, cr, user, ids, context=None):
                wf_service = netsvc.LocalService("workflow")
                for voucher_id in ids:
                     wf_service.trg_create(user, 'account.voucher', voucher_id, cr)
                self.write(cr, user, ids, {'state':'draft'})   
            

                return True
    def retencion_print(self, cr, user, ids, context=None):
              
              assert len(ids) == 1, 'This option should only be used for a single id at a time.'
              self.write(cr, user, ids, {'sent': True}, context=context)
              name=self.browse(cr,user,ids[0])['name']
              datas = {
                       'ids': ids,
                       'model': 'account.retenciones',
                       'form': self.read(cr, user, ids[0], context=context)
                     }
              return {
                     'type': 'ir.actions.report.xml',
                     'report_name': 'account.retenciones',
                     'datas': datas,
                     'nodestroy' : True,
                     'name': 'Retencion Ganancias '+ name ,
                   }
retenciones_document ()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
