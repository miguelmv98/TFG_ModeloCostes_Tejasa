from odoo import models


class TimeRecord(models.Model):

    _inherit = 'costproduct.timerecord'

    def action_importar_tiempos(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Importar tiempos',
            'res_model' : 'costproduct.timerecordwizard',
            'target': 'new',
            'view_mode': ['form','tree'],
            'view_type': ['form','tree'],
            'context': {'default_user_id': self.id},}
