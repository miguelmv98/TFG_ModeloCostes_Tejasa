# -*- coding: utf-8 -*-
from odoo import api, fields, models

class SoldProductsReport(models.Model):
    """ This model represents sold.products.report."""
    _name = 'cp.sold.products.report'
    _description = 'Reporte de los productos vendidos'
    _auto = False

    origin_document = fields.Char(string='Documento origen', readonly=True)
    delivery_notes = fields.Char(string='Albaranes relacionados', readonly=True)
    invoice_number = fields.Char(string='Numero factura', readonly=True)
    invoice_line_amount = fields.Integer(string='Cantidad', readonly=True)
    product_code = fields.Char(string='Código Producto', readonly=True)
    product_name = fields.Char(string='Nombre Producto', readonly=True)
    invoice_line_name = fields.Char(string='Líneas de la factura/Descripción', readonly=True)
    total_signed = fields.Float(string='Total', readonly=True)
    invoice_date = fields.Date(string='Fecha de la Factura', readonly=True)

    def init(self):
        self._cr.execute(f"""
            CREATE OR REPLACE VIEW cp_sold_products_report AS (
            WITH ranked AS (
                SELECT 
                    ai.origin AS origin_document,
                    sp.name AS delivery_notes,
                    ai.invoice_number AS invoice_number,
                    case when ai.invoice_number LIKE 'R%'
                        then - aml.quantity else aml.quantity 
                    END AS invoice_line_amount,
                    pp.default_code AS product_code,
                    pt.name->>'es_ES' AS product_name,
                    aml.name AS invoice_line_name,
                    ai.amount_total_signed AS total_signed,
                    ai.date_invoice AS invoice_date,
                    ROW_NUMBER() OVER (PARTITION BY ai.id, pp.default_code ORDER BY aml.id) AS rn
                FROM account_invoice ai
                    LEFT JOIN stock_picking sp ON sp.origin = ai.origin
                    LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id 
                    LEFT JOIN product_product pp ON pp.id = aml.product_id 
                    LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
                WHERE (ai.type = 'out_invoice' OR ai.type = 'out_refund')
                  AND pt.id IS NOT NULL
                  AND pp.default_code IS NOT NULL
            )
            SELECT 
                row_number() OVER () AS id,
                origin_document,
                delivery_notes,
                invoice_number,
                invoice_line_amount,
                product_code,
                product_name,
                invoice_line_name,
                total_signed,
                invoice_date
            FROM ranked
            WHERE rn = 1
            );
        """)