from odoo import models, fields, api

class InventoryReportHeader(models.Model):
    _name = "cp.inventory.report.header"
    _description = "Cabecera del reporte de inventario"

    name = fields.Char(string="Descripción", required=True)
    start_date = fields.Date(string="Fecha inicio", required=True)
    end_date = fields.Date(string="Fecha fin", required=True)
    price_per_kg = fields.Float(string="Coste transporte €/kg", required=True)
    line_ids = fields.One2many('cp.inventory.report.line', 'report_id', string="Líneas del reporte")
    create_date = fields.Datetime(string="Fecha de creación", readonly=True)

    def action_generate_inventory_report(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar inventario',
            'res_model': 'cp.inventory.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_user_id': self.id}, }


class InventoryReportLine(models.Model):
    _name = "cp.inventory.report.line"
    _description = "Línea del reporte de inventario"

    report_id = fields.Many2one('cp.inventory.report.header', string="Reporte padre", ondelete='cascade')
    internal_reference = fields.Char("Referencia Interna")
    product_name = fields.Char("Nombre Producto")
    initial_amount = fields.Float("Cantidad 01/01")
    initial_value = fields.Float("Valoración 01/01")
    final_amount = fields.Float("Cantidad 31/12")
    final_value = fields.Float("Valoración 31/12")
    selling_price = fields.Float("Precio Venta")
    cost_price = fields.Float("Precio Coste")
    weight = fields.Float("Peso")
    transport_cost = fields.Float("Coste Transporte")