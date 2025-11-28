# -*- coding: utf-8 -*-
from odoo import fields, models

class ComponentsReport(models.Model):
        _name = "cp.components.report"
        _description = "Reporte de la lista de componentes por producto"
        _auto = False

        product_code = fields.Char("Producto Ref. Interna", readonly=True)
        product_name = fields.Char("Producto Nombre", readonly=True)
        line_amount = fields.Float("Cantidad", readonly=True)
        line_product_code = fields.Char("Línea Producto Ref. Interna", readonly=True)
        line_product_name = fields.Char("Línea Producto Nombre", readonly=True)
        line_product_cost = fields.Float("Precio", readonly=True)
        line_product_weight = fields.Float("Peso", readonly=True)

        def init(self):
            self._cr.execute("""
                CREATE OR REPLACE VIEW cp_components_report AS (
                WITH latest_price AS (
                    SELECT DISTINCT ON (product_id)
                        product_id,
                        cost,
                        datetime
                    FROM product_price_history
                    ORDER BY product_id, datetime DESC
                )
                SELECT
                    row_number() OVER () AS id,
                    prod_final.default_code AS product_code,
                    CONCAT('[', prod_final.default_code, '] ', tmpl_final.name->>'en_US') AS product_name,
                    bl.product_qty::numeric AS line_amount,
                    prod_line.default_code AS line_product_code,
                    CONCAT('[', prod_line.default_code, '] ' , tmpl_line.name->>'en_US') AS line_product_name,
                    lp.cost AS line_product_cost,
                    COALESCE(prod_line.weight,0) AS line_product_weight
                FROM mrp_bom b
                LEFT JOIN product_template tmpl_final
                  ON b.product_tmpl_id = tmpl_final.id
                LEFT JOIN product_product prod_final
                  ON prod_final.product_tmpl_id  = tmpl_final.id
                LEFT JOIN mrp_bom_line bl
                  ON bl.bom_id = b.id
                LEFT JOIN product_product prod_line
                  ON prod_line.id = bl.product_id
                LEFT JOIN product_template tmpl_line
                  ON prod_line.product_tmpl_id = tmpl_line.id
                LEFT JOIN latest_price lp
                  ON lp.product_id = prod_line.id
                ORDER BY b.id, bl.id
                );
            """)