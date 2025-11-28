# -*- coding: utf-8 -*-
from odoo import models, fields


class IndicadorCoste(models.Model):
    _name = 'cp.account.indicator'
    _description = 'Indicadores anuales del informe de costes'


    report_id = fields.Many2one('cp.account.summary', string="Informe")
    general_indicator_id = fields.Many2one('cp.account.summary')
    model_indicator_id = fields.Many2one('cp.account.summary')
    hours_indicator_id = fields.Many2one('cp.account.summary')
    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    value = fields.Float(string="Valor")
    cost_hour_value = fields.Float(string="€/Hora")

