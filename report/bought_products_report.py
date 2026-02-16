# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BoughtProductsReport(models.Model):
    """ This model represents bought.products.report."""
    _name = 'cp.bought.products.report'
    _description = 'Reporte de los productos comprados'
    _auto = False

    amount = fields.Integer(string="Cantidad", readonly=True)
    origin_document = fields.Char(string="Documento de origen", readonly=True)
    product_code = fields.Char(string="Código del producto", readonly=True)
    product_name = fields.Char(string="Nombre del producto", readonly=True)
    invoice_line_name = fields.Char(string="Descripción línea de factura", readonly=True)
    invoice_date = fields.Date(string="Fecha de la factura", readonly=True)
    invoice_number = fields.Char(string="Número de factura", readonly=True)
    total_signed = fields.Float(string="Total", readonly=True)

    def init(self):
        self._cr.execute(f"""
        CREATE OR REPLACE VIEW cp_bought_products_report AS (
        WITH ranked AS (
            SELECT 
                case when ai.invoice_number LIKE 'R%'
                        then - aml.quantity else aml.quantity 
                END AS amount,
                ai.origin AS origin_document,
                pp.default_code AS product_code,
                pt.name->>'es_ES' AS product_name,
                aml.name AS invoice_line_name,
                ai.date_invoice AS invoice_date,
                ai.invoice_number AS invoice_number,
                CASE WHEN ROW_NUMBER() OVER (PARTITION BY ai.id, pp.default_code ORDER BY aml.id) = 1 
                     THEN ai.amount_total_signed 
                     ELSE NULL 
                END AS total_signed,
                ROW_NUMBER() OVER (PARTITION BY ai.id ORDER BY aml.id) AS rn,
                ROW_NUMBER() OVER (ORDER BY ai.date_invoice, ai.id, aml.id) AS id
            FROM account_invoice ai
                LEFT JOIN account_move_line aml ON aml.invoice_id = ai.id 
                LEFT JOIN product_product pp ON pp.id = aml.product_id 
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id 
            WHERE (ai.type = 'in_invoice' OR ai.type = 'in_refund')
              AND aml.quantity != 0
        )
        SELECT 
            id,
            amount,
            origin_document,
            product_code,
            product_name,
            invoice_line_name,
            invoice_date,
            invoice_number,
            total_signed
        FROM ranked
        ORDER BY invoice_date
        );
    """)