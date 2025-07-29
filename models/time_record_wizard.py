from odoo import fields, models, api


class TimeRecordWizard(models.TransientModel):
    _name = 'costproduct.timerecordwizard'
    _description = 'Time Record Wizard'

    archivo_excel = fields.Binary(required=True, string='nombre_archivo')
