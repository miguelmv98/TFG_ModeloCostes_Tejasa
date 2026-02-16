from odoo import models, fields, api
import io
import base64
import xlsxwriter

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

    def action_export_lines_excel(self):
        self.ensure_one()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Modelo de Costes')

        sheet.write(0,12, "INGERSOS BRUTOS")
        sheet.write(1, 12, self.gross_revenue)

        sheet.write(0,13,"APROVISIONAMIENTO")
        sheet.write(1, 13, self.provisions)

        sheet.write(0, 16, "MARGEN BRUTO SOBRE MATERIALES")
        sheet.write(1, 16, self.material_gross_margin)

        sheet.write(0, 17, "TRANSPORTES")
        sheet.write(1, 17, self.transport)
        sheet.write(0, 18, "REPARACIONES")
        sheet.write(1, 18, self.repairs)
        sheet.write(0, 19, "SUPPLIES")
        sheet.write(1, 19, self.supplies)
        sheet.write(0, 20, "MARGEN DE CONTRIBUCIÓN")
        sheet.write(1, 20, self.contribution_margin)

        sheet.write(0, 21, "COSTE DE PERSONAL (Industrial)")
        sheet.write(1, 21, self.industrial_employee_cost)
        sheet.write(0, 22, "AMORTIZACIÓN DE PERSONAL (Industrial)")
        sheet.write(1, 22, self.industrial_amortization)
        sheet.write(0, 23, "COSTES DE FABRICACIÓN")
        sheet.write(1, 23, self.manufacturing_cost)
        sheet.write(0, 24, "MARGEN NETO INDUSTRIAL")
        sheet.write(1, 24, self.industrial_net_margin)

        sheet.write(0, 25, "COSTE DE PERSONAL (Oficina)")
        sheet.write(1, 25, self.office_employee_cost)
        sheet.write(0, 26, "SEGUROS")
        sheet.write(1, 26, self.insurances)
        sheet.write(0, 27, "AMORTIZACIÓN DE PERSONAL (Oficina)")
        sheet.write(1, 27, self.office_amortization)
        sheet.write(0, 28, "GASTOS GENERALES")
        sheet.write(1, 28, self.general_expenditures)

        sheet.write(0, 31, "MARGEN NETO")
        sheet.write(1, 31, self.global_net_margin)


        headers = [
            "Código Producto",
            "Descripción Producto",
            "Tipo de producto",

            "Existencias iniciales (unidades)",
            "Existencias iniciales (valor)",
            "Cantidad anual producida (unidades)",
            "Cantidad anual comprada (unidades)",
            "Cantidad anual vendida (unidades)",
            "Existencias finales (unidades)",
            "Existencias finales (valor)",
            "Variación (unidades)",
            "Variación (valor)",

            "Ingresos brutos",

            "Coste de materiales",
            "Coste de variaciones",
            "Trabajos de mecanizado (externos)",
            "Margen bruto sobre materiales",

            "Transporte y aranceles (compras)",
            "Reparaciones",
            "Suministros",
            "Margen de contribución",

            "Coste de personal industrial",
            "Amortización industrial",
            "Costes de fabricación",
            "Margen neto industrial",

            "Coste de personal oficina",
            "Seguros",
            "Amortización oficina",
            "Gastos generales",
            "Subactividad",
            "I + D",
            "Margen neto",

            "Tiempo estándar (h)",
            "Tiempo total (h)",
        ]
        for col,header in enumerate(headers):
            sheet.write(3, col, header)

        #Data
        row=4
        for line in self.line_ids:
            sheet.write(row, 0, line.code_product)
            sheet.write(row, 1, line.description_product)
            sheet.write(row, 2, line.product_type)

            sheet.write(row, 3, line.product_initial_amount)
            sheet.write(row, 4, line.product_initial_value)
            sheet.write(row, 5, line.amount_produced)
            sheet.write(row, 6, line.amount_bought)
            sheet.write(row, 7, line.amount_sold)
            sheet.write(row, 8, line.product_final_amount)
            sheet.write(row, 9, line.product_final_value)
            sheet.write(row, 10, line.amount_variation)
            sheet.write(row, 11, line.value_variation)

            sheet.write(row, 12, line.gross_revenue)

            sheet.write(row, 13, line.material_cost)
            sheet.write(row, 14, line.variation_cost)
            sheet.write(row, 15, line.external_work_cost)
            sheet.write(row, 16, line.material_gross_margin)

            sheet.write(row, 17, line.transport_cost)
            sheet.write(row, 18, line.repair_cost)
            sheet.write(row, 19, line.supplies_cost)
            sheet.write(row, 20, line.contribution_margin)

            sheet.write(row, 21, line.industrial_employee_cost)
            sheet.write(row, 22, line.industrial_amortization_cost)
            sheet.write(row, 23, line.manufacturing_cost)
            sheet.write(row, 24, line.industrial_net_margin)

            sheet.write(row, 25, line.office_employee_cost)
            sheet.write(row, 26, line.insurance_cost)
            sheet.write(row, 27, line.office_amortization_cost)
            sheet.write(row, 28, line.general_expenditures)
            sheet.write(row, 29, line.subactivity)
            sheet.write(row, 30, line.research_and_development)
            sheet.write(row, 31, line.global_net_margin)

            sheet.write(row, 32, line.reference_time)
            sheet.write(row, 33, line.total_time)

            row += 1

        workbook.close()
        output.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f'lineas_{self.name}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

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
    subactivity = fields.Float("Subactividad")
    research_and_development = fields.Float("I + D")
    global_net_margin = fields.Float("MARGEN NETO")

    reference_time = fields.Float("Tiempo Estandar (h)")
    total_time = fields.Float("Tiempo Total (h)")

