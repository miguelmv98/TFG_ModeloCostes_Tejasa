from odoo import fields, models, api


class TimeRecord(models.Model):
    _name = 'cp.time.record'
    _description = 'Registra el tiempo empleado a una orden de fabriacion'

    employee = fields.Char('Empleado', required=True)
    production_order = fields.Char('OM')
    start_date = fields.Datetime('Fecha Inicio')
    end_date = fields.Datetime('Fecha Fin')
    duration_hms = fields.Char("Duración (h:m:s)",compute="_compute_tiempo_calculado_hms")
    duration_hours = fields.Float("Duración en horas", compute="_compute_tiempo_calculado", store = True)

    _sql_constraints = [
        ('cp_AK_time_record_unique_record','UNIQUE(employee,production_order,start_date,end_date)','Registro ya existente')
    ]

    @api.depends("start_date", "end_date")
    def _compute_tiempo_calculado(self):
        for record in self:
                if record.start_date and record.end_date:
                    diferencia = record.end_date - record.start_date
                    segundos_totales = int(diferencia.total_seconds())

                    record.duration_hours  = segundos_totales / 3600
                else:
                    record.duration_hours = 0.0

    @api.depends("start_date", "end_date")
    def _compute_tiempo_calculado_hms(self):
        for record in self:
            if record.start_date and record.end_date:
                diferencia = record.end_date - record.start_date
                segundos_totales = int(diferencia.total_seconds())

                horas = segundos_totales // 3600
                minutos = (segundos_totales % 3600) // 60
                segundos = segundos_totales % 60
                record.duration_hms = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
            else:
                record.duration_hms = False

    def action_importar_tiempos(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Importar tiempos',
            'res_model': 'cp.time.record.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_user_id': self.id}, }

