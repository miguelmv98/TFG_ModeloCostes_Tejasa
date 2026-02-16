# -*- coding: utf-8 -*-
from odoo import models, fields, api


class IndicadorCoste(models.Model):
    _name = 'cp.account.indicator'
    _description = 'Indicadores anuales del informe de costes'


    report_id = fields.Many2one('cp.account.summary', string="Informe")
    general_indicator_id = fields.Many2one('cp.account.summary')
    model_indicator_id = fields.Many2one('cp.account.summary')
    hours_indicator_id = fields.Many2one('cp.account.summary')
    name = fields.Char(string="Nombre")
    code = fields.Char(string="Codigo")
    value = fields.Float(string="Valor base")
    total_value = fields.Float(string="Valor",compute= "_compute_total_value", store=True)
    amount_hours = fields.Float(string="Hours Amount")
    cost_hour_value = fields.Float(string="€/Hora",compute= "_compute_cost_hour_value", store=True)

    account_indicators_manual_ids = fields.One2many("cp.account.indicator.manual.addition", "account_indicator_id", string="Indicadores manuales")

    @api.depends("value","account_indicators_manual_ids")
    def _compute_total_value(self):
        for record in self:
            if record:
                manual_value = 0
                for indicator in record.account_indicators_manual_ids:
                    manual_value = manual_value + indicator.value
                record.total_value = manual_value + record.value
            else:
                record.total_value = 0

    @api.depends("amount_hours","total_value")
    def _compute_cost_hour_value(self):
        for record in self:
            if record.amount_hours:
                record.cost_hour_value = record.total_value/record.amount_hours
            else:
                record.cost_hour_value = False


