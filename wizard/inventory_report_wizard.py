from odoo import models, fields, api

class InventoryReportWizard(models.TransientModel):
    _name = 'cp.inventory.report.wizard'
    _description = 'Asistente para generar reporte de inventario'

    initial_date = fields.Date(string="Fecha inicio", required=True)
    final_date = fields.Date(string="Fecha fin", required=True)
    price_per_kg = fields.Float(string="Coste transporte €/kg", default=10.0, required=True)
    description = fields.Char(string="Descripción del reporte", required=True)

    def action_confirm_generate_report(self):
        """Genera el reporte y sus líneas basado en los parámetros del wizard."""
        self.ensure_one()
        cr = self.env.cr

        # Crear registro padre
        report = self.env['cp.inventory.report.header'].create({
            'name': self.description,
            'start_date': self.initial_date,
            'end_date': self.final_date,
            'price_per_kg': self.price_per_kg,
        })

        # Ejecutar la query adaptada a los parámetros del wizard
        cr.execute("""
                   WITH params AS (SELECT CAST(%s AS DATE) AS fecha_inicio,
                                          CAST(%s AS DATE) AS fecha_fin,
                                          %s               AS coste_por_kg),
                        movimientos AS (SELECT sm.product_id,
                                               SUM(
                                                       CASE
                                                           WHEN sm.date <= (SELECT fecha_inicio FROM params)
                                                               THEN sm.product_qty *
                                                                    (CASE WHEN sl_dest.usage = 'internal' THEN 1 ELSE -1 END)
                                                           ELSE 0 END
                                               ) AS qty_inicio,
                                               SUM(
                                                       CASE
                                                           WHEN sm.date <= (SELECT fecha_fin FROM params)
                                                               THEN sm.product_qty *
                                                                    (CASE WHEN sl_dest.usage = 'internal' THEN 1 ELSE -1 END)
                                                           ELSE 0 END
                                               ) AS qty_fin
                                        FROM stock_move sm
                                                 JOIN stock_location sl_src ON sm.location_id = sl_src.id
                                                 JOIN stock_location sl_dest ON sm.location_dest_id = sl_dest.id
                                        WHERE sm.state = 'done'
                                        GROUP BY sm.product_id),
                        latest_price_ini AS (SELECT DISTINCT ON (pph.product_id) pph.product_id,
                                                                                 pph.cost
                                             FROM product_price_history pph,
                                                  params p
                                             WHERE pph.datetime <= p.fecha_inicio
                                             ORDER BY pph.product_id, pph.datetime DESC),
                        latest_price_fin AS (SELECT DISTINCT ON (pph.product_id) pph.product_id,
                                                                                 pph.cost
                                             FROM product_price_history pph,
                                                  params p
                                             WHERE pph.datetime <= p.fecha_fin
                                             ORDER BY pph.product_id, pph.datetime DESC)
                   SELECT pp.default_code                                               AS referencia_interna,
                          pt.name ->> 'en_US'                                           AS nombre_producto,
                          COALESCE(m.qty_inicio, 0)                                     AS cantidad_01_01,
                          COALESCE(m.qty_inicio, 0) * COALESCE(lpi.cost, pt.list_price) AS valoracion_01_01,
                          COALESCE(m.qty_fin, 0)                                        AS cantidad_31_12,
                          COALESCE(m.qty_fin, 0) * COALESCE(lpf.cost, pt.list_price)    AS valoracion_31_12,
                          pt.list_price                                                 AS precio_venta,
                          COALESCE(lpf.cost, pt.list_price)                             AS precio_coste,
                          pt.weight                                                     AS peso,
                          pt.weight * (SELECT coste_por_kg FROM params)                 AS coste_transporte
                   FROM product_product pp
                            JOIN product_template pt ON pp.product_tmpl_id = pt.id
                            LEFT JOIN movimientos m ON m.product_id = pp.id
                            LEFT JOIN latest_price_ini lpi ON lpi.product_id = pp.id
                            LEFT JOIN latest_price_fin lpf ON lpf.product_id = pp.id
                   WHERE pt.type = 'product'
                   ORDER BY pt.default_code
                   """, (self.initial_date, self.final_date, self.price_per_kg))

        rows = cr.dictfetchall()

        # Crear líneas del reporte
        for row in rows:
            self.env['cp.inventory.report.line'].create({
                'report_id': report.id,
                'internal_reference': row['referencia_interna'],
                'product_name': row['nombre_producto'],
                'initial_amount': row['cantidad_01_01'],
                'initial_value': row['valoracion_01_01'],
                'final_amount': row['cantidad_31_12'],
                'final_value': row['valoracion_31_12'],
                'selling_price': row['precio_venta'],
                'cost_price': row['precio_coste'],
                'weight': row['peso'],
                'transport_cost': row['coste_transporte'],
            })

        # Abrir el reporte recién generado
        return {
            'type': 'ir.actions.act_window',
            'name': f"Reporte Inventario - {self.description}",
            'res_model': 'cp.inventory.report.header',
            'view_mode': 'form',
            'res_id': report.id,
        }