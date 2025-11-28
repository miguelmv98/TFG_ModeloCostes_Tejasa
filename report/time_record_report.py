from odoo import models, fields

class TimeRecordReport(models.Model):
    _name = "cp.time.record.report"
    _description = "Reporte agregado (mensual y acumulado) de tiempos"
    _auto = False
    _order = "year desc, month asc, employee"

    employee = fields.Char("Empleado", readonly=True)
    year = fields.Integer("Año", readonly=True)
    month = fields.Integer("Mes", readonly=True)  # 1..12
    hours_month = fields.Float("Horas del mes", readonly=True)
    accumulated_hours = fields.Float("Horas acumuladas", readonly=True)

    def init(self):
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW cp_time_record_report AS (
                WITH base AS (
                    SELECT
                        employee,
                        EXTRACT(YEAR  FROM start_date)::int AS year,
                        EXTRACT(MONTH FROM end_date)::int AS month,
                        SUM(duration_hours) AS hours_month
                    FROM cp_time_record
                    WHERE start_date IS NOT NULL
                    GROUP BY employee, EXTRACT(YEAR FROM start_date), EXTRACT(MONTH FROM end_date)
                ),
                months AS (
                    SELECT
                        b.employee,
                        b.year,
                        gs.mes
                    FROM (SELECT DISTINCT employee, year FROM base) b
                    CROSS JOIN LATERAL generate_series(1, 12) AS gs(mes)
                ),
                combinado AS (
                    SELECT
                        m.employee,
                        m.year,
                        m.mes as month,
                        COALESCE(b.hours_month, 0.0) AS hours_month
                    FROM months m
                    LEFT JOIN base b
                      ON b.employee = m.employee AND b.year = m.year AND b.month = m.mes
                )
                SELECT
                    ROW_NUMBER() OVER(ORDER BY employee, year, month)::int AS id,
                    employee,
                    year,
                    month,
                    hours_month as hours_month,
                    SUM(hours_month) OVER (PARTITION BY employee, year ORDER BY month
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS accumulated_hours
                FROM combinado
            );
        """)
