# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountAmortisationTableLine(models.Model):
    """ This model represents account.amortisation.table.line."""
    _name = 'cp.account.amortisation.table.line'
    _description = 'Account Amortisation Table Line'

    report_id = fields.Many2one('cp.account.summary', string="Padre")
    name = fields.Char(string="Indicador")
    value = fields.Float(string="Valor")
    amortization = fields.Float(string="Amortización")
    net_value = fields.Float(string="Valor Neto")