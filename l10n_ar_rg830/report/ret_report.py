# -*- coding: utf-8 -*-

from openerp.report import report_sxw
import time
from openerp.osv import fields, osv

class ret_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(ret_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'voucher':self.voucher,
        })

    def voucher(self, cr, uid):
     	     name= 'juan'
     	     return name
	
	
	
report_sxw.report_sxw('report.account.retenciones', 'account.retenciones', 'addons/l10n_ar_retenciones/report/ret_report.rml',parser=ret_report, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
