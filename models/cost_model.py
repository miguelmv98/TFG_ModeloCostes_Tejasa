from odoo import models, fields, api

class CostModelHeader(models.Model):
    _name = "cp.cost.model.header"
    _description = "Registro del modelo de costes"

    name = fields.Char(string="Descripción", required=True)
    start_date = fields.Date(string="Fecha inicio", required=True)
    end_date = fields.Date(string="Fecha fin", required=True)
    reference_year = fields.Integer(string="Año de referencia", compute='_compute_year', store=True)
    line_ids = fields.One2many('cp.cost.model.line', 'cost_model_id', string="Líneas del modelo")
    create_date = fields.Datetime(string="Fecha de creación", readonly=True)

    gross_revenue = fields.Float("INGRESOS BRUTOS")
    provisions = fields.Float("APROVISIONAMIENTO")
    material_gross_margin = fields.Float("MARGEN BRUTO SOBRE MATERIALES")
    transport = fields.Float("TRANSPORTE")
    repairs = fields.Float("REPARACIONES")
    supplies = fields.Float("SUMINISTROS")
    contribution_margin = fields.Float("MARGEN DE CONTRIBUCIÓN")
    industrial_employee_cost = fields.Float("COSTE DE PERSONAL (Industrial)")
    industrial_amortization = fields.Float("AMORTIZACIÓN (Industrial)")
    manufacturing_cost = fields.Float("COSTES DE FABRICACIÓN")
    industrial_net_margin = fields.Float("MARGEN NETO INDUSTRIAL")
    office_employee_cost = fields.Float("COSTE DE PERSONAL (Oficina)")
    insurances = fields.Float("SEGUROS")
    office_amortization = fields.Float("AMORTIZACIÓN (Oficina)")
    general_expenditures = fields.Float("GASTOS GENERALES")
    global_net_margin = fields.Float("MARGEN NETO")


    @api.depends("end_date")
    def _compute_year(self):
        for model in self:
            model.reference_year = model.end_date.year

    def action_generate_cost_model(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generar Modelo de Costes',
            'res_model': 'cp.cost.model.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_user_id': self.id}, }


class CostModelLine(models.Model):
    _name = "cp.cost.model.line"
    _description = "Línea del modelo de costes"

    cost_model_id = fields.Many2one('cp.cost.model.header', string="Modelo de Costes", ondelete='cascade')
    code_product = fields.Char("Código Producto")
    description_product = fields.Char("Descripción Producto")
    product_type = fields.Char("Tipo de producto")
    product_initial_amount = fields.Integer("Existencias iniciales (unidades)")
    product_initial_value = fields.Float("Existencias iniciales (valor)")
    amount_produced = fields.Integer("Cantidad anual producidad (unidades)")
    amount_bought = fields.Integer("Cantidad anual comprada (unidades)")
    amount_sold = fields.Integer("Cantidad anual vendida (unidades)")
    product_final_amount = fields.Integer("Existencias finales (unidades)")
    product_final_value = fields.Float("Existencias finales (valor)")
    amount_variation = fields.Integer("Variacion (unidades")
    value_variation = fields.Float("Variacion (valor)")
    gross_revenue = fields.Float("INGRESOS BRUTOS")

    material_cost = fields.Float("Coste de materiales")
    variation_cost = fields.Float("Coste de variaciones")
    external_work_cost = fields.Float("Trabajos de mecanizado (externos)")
    material_gross_margin = fields.Float("MARGEN BRUTO SOBRE MATERIALES")

    transport_cost = fields.Float("Transporte y aranceles (compras)")
    repair_cost = fields.Float("Reparaciones")
    supplies_cost = fields.Float("Suministros")
    contribution_margin = fields.Float("MARGEN DE CONTRIBUCIÓN")

    industrial_employee_cost = fields.Float("Coste de personal industrial")
    industrial_amortization_cost = fields.Float("Amortización industrial")
    manufacturing_cost = fields.Float("COSTES DE FABRICACIÓN")
    industrial_net_margin = fields.Float("MARGEN NETO INDUSTRIAL")

    office_employee_cost = fields.Float("Coste de personal oficina")
    insurance_cost = fields.Float("Seguros")
    office_amortization_cost = fields.Float("Amortización oficina")
    general_expenditures = fields.Float("Gastos generales")
    research_and_development = fields.Float("I + D")
    global_net_margin = fields.Float("MARGEN NETO")

    reference_time = fields.Float("Tiempo Estandar (h)")
    total_time = fields.Float("Tiempo Total (h)")

