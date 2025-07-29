from odoo import fields, models, api


class TimeRecord(models.Model):
    _name = 'costproduct.timerecord'
    _description = 'Registra el tiempo empleado a una orden de fabriacion'

    empleado = fields.Char('Empleado', required=True)
    orden_fabricacion = fields.Char('OM')
    tiempo_inicio = fields.Date('Fecha Inicio')
    tiempo_final = fields.Date('Fecha Fin')
    #tiempoCalculado = fields.Time()

