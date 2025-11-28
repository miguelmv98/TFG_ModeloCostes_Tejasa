from odoo import fields, models, api


class ModelName(models.Model):
    _name = 'cp.time.record.wizard.log'
    _description = 'Log con los herrores registrados al cargar datos de tiempos'

    file_name = fields.Char('Nombre del fichero')
    employee = fields.Char('Empleado')
    production_order = fields.Char('Orden Montaje')
    start_date = fields.Datetime('Fecha Inicio')
    error = fields.Char('Error')
    reviewed = fields.Boolean('Revisado',default=False)
