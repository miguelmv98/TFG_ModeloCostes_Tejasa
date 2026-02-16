# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountIndicatorManualAddition(models.Model):
    _name = 'cp.account.indicator.manual.addition'
    _description = 'Indicadores anuales del informe de costes'


    account_indicator_id = fields.Many2one(
        'cp.account.indicator',
        required=True,
        ondelete="cascade"
    )
    description = fields.Char(string="Description")
    value = fields.Float(string="Valor")