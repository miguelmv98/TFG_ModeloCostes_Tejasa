
from odoo import models, fields, api
from odoo.exceptions import UserError


class CostModelWizard(models.Model):
    _name = 'cp.cost.model.wizard'
    _description = 'Asistente para generar el modelo de costes'

    star_date = fields.Date(string="Fecha inicio", required=True)
    end_date = fields.Date(string="Fecha fin", required=True)
    description = fields.Char(string="Descripción del reporte", required=True)

    account_report= fields.Many2one(
        'cp.account.summary',
        string="Informe de costes anual"
    )

    inventory_report = fields.Many2one(
        'cp.inventory.report.header',
        string="Reporte de inventario"
    )

    def action_confirm_generate_cost_model(self):
        """Aquí generarías el informe final combinando ambos"""
        self.ensure_one()
        cr = self.env.cr

        if not self.account_report or not self.inventory_report:
            raise UserError("Debes seleccionar ambos informes antes de generar el modelo.")

        query = """ 
        SELECT
    MAX(CASE WHEN code = 'INGRESOS_BRUTOS_MODELO' THEN total_value END) AS gross_revenue,
    MAX(CASE WHEN code = 'APROVISIONAMIENTO_MODELO' THEN total_value END) AS provisions,
    MAX(CASE WHEN code = 'MARGEN_BRUTO_MATERIALES_MODELO' THEN total_value END) AS material_gross_margin,
    MAX(CASE WHEN code = 'TRANSPORTES_MODELO' THEN total_value END) AS transport,
    MAX(CASE WHEN code = 'REPARACIONES_MODELO' THEN total_value END) AS repairs,
    MAX(CASE WHEN code = 'SUMINISTROS_MODELO' THEN total_value END) AS supplies,
    MAX(CASE WHEN code = 'MARGEN_CONTRIBUCION_MODELO' THEN total_value END) AS contribution_margin,
    MAX(CASE WHEN code = 'COSTES_PERSONAL_TALLER_MODELO' THEN total_value END) AS industrial_employee_cost,
    MAX(CASE WHEN code = 'AMORTIZACION_TALLER_MODELO' THEN total_value END) AS industrial_amortization,
    MAX(CASE WHEN code = 'COSTES_FABRICACION_MODELO' THEN total_value END) AS manufacturing_cost,
    MAX(CASE WHEN code = 'MARGEN_NETO_INDUSTRIAL_MODELO' THEN total_value END) AS industrial_net_margin,
    MAX(CASE WHEN code = 'COSTE_PERSONAL_OFICINA_MODELO' THEN total_value END) AS office_employee_cost,
    MAX(CASE WHEN code = 'SEGUROS_MODELO' THEN total_value END) AS insurances,
    MAX(CASE WHEN code = 'AMORTIZACION_OFICINA_MODELO' THEN total_value END) AS office_amortization,
    MAX(CASE WHEN code = 'GASTOS_GENERALES_MODELO' THEN total_value END) AS general_expenditures,
    MAX(CASE WHEN code = 'MARGEN_NETO_MODELO' THEN total_value END) AS global_net_margin
FROM cp_account_indicator
WHERE report_id = %(id_contabilidad)s;
        """
        self.env.cr.execute(query, {
            'id_contabilidad': self.account_report.id,
        })

        row = self.env.cr.dictfetchone()

        report = self.env['cp.cost.model.header'].create({
            'name': self.description,
            'start_date': self.star_date,
            'end_date': self.end_date,

            'gross_revenue': row['gross_revenue'],
            'provisions': row['provisions'],
            'material_gross_margin': row['material_gross_margin'],
            'transport': row['transport'],
            'repairs': row['repairs'],
            'supplies': row['supplies'],
            'contribution_margin': row['contribution_margin'],
            'industrial_employee_cost': row['industrial_employee_cost'],
            'industrial_amortization': row['industrial_amortization'],
            'manufacturing_cost': row['manufacturing_cost'],
            'industrial_net_margin': row['industrial_net_margin'],
            'office_employee_cost': row['office_employee_cost'],
            'insurances': row['insurances'],
            'office_amortization': row['office_amortization'],
            'general_expenditures': row['general_expenditures'],
            'global_net_margin': row['global_net_margin'],
        })

        query="""
        WITH unit_times AS (
    SELECT 
        pt.default_code,
        SUM(EXTRACT(EPOCH FROM (ct.end_date - ct.start_date)) / 3600.0) AS totalhoras,
        SUM(mp.product_qty) AS totalpiezas,
        (SUM(EXTRACT(EPOCH FROM (ct.end_date - ct.start_date)) / 3600.0)
            / NULLIF(SUM(mp.product_qty), 0)) AS horasunitarias
    FROM product_template pt
    INNER JOIN product_product pp ON pp.product_tmpl_id = pt.id
    INNER JOIN mrp_production mp ON mp.product_id = pp.id
    INNER JOIN cp_time_record ct 
        ON ct.production_order = REPLACE(mp.name, '/', '')
        AND ct.end_date BETWEEN %(fecha_inicio)s AND %(fecha_final)s
    where mp.state = 'done'
    GROUP BY pt.default_code
),

compras AS (
    SELECT 
        cbpr.product_code,
        SUM(cbpr.amount) AS amount_bought
    FROM cp_bought_products_report cbpr
    WHERE cbpr.invoice_date BETWEEN %(fecha_inicio)s AND %(fecha_final)s
    GROUP BY cbpr.product_code
),

ventas AS (
    SELECT 
        cspr.product_code,
        SUM(cspr.invoice_line_amount) AS amount_sold
    FROM cp_sold_products_report cspr
    WHERE cspr.invoice_date BETWEEN %(fecha_inicio)s AND %(fecha_final)s
    GROUP BY cspr.product_code
),
componentes AS (
    SELECT 
        ccr.product_code,
        SUM(ccr.line_product_cost) AS material_cost_unit
    FROM cp_components_report ccr
    GROUP BY ccr.product_code
),

inventario AS (
    SELECT 
        cirl.internal_reference,
        cirl.initial_amount,
        cirl.initial_value,
        cirl.final_amount,
        cirl.final_value,
        cirl.cost_price,
        cirl.selling_price
    FROM cp_inventory_report_line cirl
    INNER JOIN cp_inventory_report_header cirh ON cirh.id = cirl.report_id AND cirh.id = %(id_inventario)s
),

costes_indirectos AS (
    SELECT 
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'TRABAJOS_MECANIZADO' AND report_id=%(id_contabilidad)s) AS trabajos_mecanizado,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'TRANSPORTES' AND report_id=%(id_contabilidad)s) AS transportes,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'REPARACIONES' AND report_id=%(id_contabilidad)s) AS reparaciones,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'SUMINISTROS' AND report_id=%(id_contabilidad)s) AS suministros,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'PERSONAL_TALLER' AND report_id=%(id_contabilidad)s) AS personal_taller,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'AMORTIZACION_TALLER' AND report_id=%(id_contabilidad)s) AS amortizacion_taller,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'PERSONAL_OFICINA' AND report_id=%(id_contabilidad)s) AS personal_oficina,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'SEGUROS_MODELO' AND report_id=%(id_contabilidad)s) AS seguros,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'AMORTIZACION_OFICINA' AND report_id=%(id_contabilidad)s) AS amortizacion_oficina,
        (SELECT cost_hour_value FROM cp_account_indicator WHERE code = 'GASTOS_NO_FABRICACION' AND report_id=%(id_contabilidad)s) AS gastos_no_fabricacion,
        (SELECT SUM(total_value) FROM cp_account_indicator WHERE code IN ('AMORTIZACION_DESARROLLO','AMORTIZACION_INVESTIGACION','AMORTIZACION_PATENTES','AMORTIZACION_APP_INFORMATICAS') AND report_id=%(id_contabilidad)s) AS I_D,
        (SELECT SUM(total_value)*(100-(SELECT activity_level FROM cp_account_summary WHERE id=%(id_contabilidad)s))/100 FROM cp_account_indicator WHERE code IN ('PERSONAL_TALLER','AMORTIZACION_TALLER','PERSONAL_OFICINA','SEGUROS_MODELO','AMORTIZACION_OFICINA','AMORTIZACION_OFICINA','GASTOS_NO_FABRICACION')AND report_id=%(id_contabilidad)s) AS subactividad
),

base AS (
    SELECT 
        pt.default_code AS code_product,
        pt.name->>'es_ES' AS description_product,

        inv.initial_amount AS product_initial_amount,
        inv.initial_value AS product_initial_value,

        ut.totalpiezas as amount_produced,
        comp.amount_bought,
        vend.amount_sold,

        inv.final_amount AS product_final_amount,
        inv.final_value AS product_final_value,

        vend.amount_sold AS amount_variation,
        vend.amount_sold * inv.cost_price AS value_variation,
        vend.amount_sold * inv.selling_price AS gross_revenue,

        c.material_cost_unit * vend.amount_sold AS material_cost,

        inv.cost_price * ABS(vend.amount_sold) AS variation_cost,

        ut.horasunitarias * ci.trabajos_mecanizado * ut.totalpiezas AS external_work_cost,

        ut.horasunitarias * ci.transportes * ut.totalpiezas AS transport_cost,
        ut.horasunitarias * ci.reparaciones * ut.totalpiezas AS repair_cost,
        ut.horasunitarias * ci.suministros  * ut.totalpiezas AS supplies_cost,

        ut.horasunitarias * ci.personal_taller * ut.totalpiezas AS industrial_employee_cost,
        ut.horasunitarias * ci.amortizacion_taller * ut.totalpiezas AS industrial_amortization_cost,

        ut.horasunitarias * ci.personal_oficina * ut.totalpiezas AS office_employee_cost,
        ut.horasunitarias * ci.seguros * ut.totalpiezas  AS insurance_cost,
        ut.horasunitarias * ci.amortizacion_oficina * ut.totalpiezas AS office_amortization_cost,
        ut.horasunitarias * ci.gastos_no_fabricacion * ut.totalpiezas AS general_expenditures,
        (ci.subactividad / (SELECT SUM(totalhoras) FROM unit_times)) * ut.totalhoras AS subactivity,
        (ci.I_D / (SELECT SUM(totalhoras) FROM unit_times)) * ut.totalhoras AS research_and_development,
            
        
            
        0 AS reference_time,
        ut.totalhoras AS total_time

    FROM product_template pt
    LEFT JOIN inventario inv ON inv.internal_reference = pt.default_code
    LEFT JOIN compras comp ON comp.product_code = pt.default_code
    LEFT JOIN ventas vend ON vend.product_code = pt.default_code
    LEFT JOIN unit_times ut ON ut.default_code = pt.default_code
    CROSS JOIN costes_indirectos ci
    LEFT JOIN componentes c ON c.product_code = pt.default_code
    WHERE pt.type = 'product'
      AND pt.default_code IS NOT NULL
      AND pt.create_date < %(fecha_final)s
),

step1 AS (
    SELECT 
        base.*,
        COALESCE(base.gross_revenue,0) 
        + COALESCE(base.material_cost,0) 
        + COALESCE(base.variation_cost,0) 
        + COALESCE(base.external_work_cost,0) AS material_gross_margin
    FROM base
),
step1_5 AS (
    SELECT 
        *,
        COALESCE(material_gross_margin)
        + COALESCE(transport_cost,0) 
        + COALESCE(repair_cost,0) 
        + COALESCE(supplies_cost,0) AS contribution_margin
    FROM step1
),

step2 AS (
    SELECT 
        *,
        + COALESCE(material_cost,0) 
        + COALESCE(base.external_work_cost,0)
        + COALESCE(transport_cost,0) 
        + COALESCE(repair_cost,0) 
        + COALESCE(supplies_cost,0)
        + COALESCE(industrial_employee_cost,0) 
        + COALESCE(industrial_amortization_cost,0) AS manufacturing_cost,

         COALESCE(contribution_margin,0) 
        + COALESCE(industrial_employee_cost,0) 
        + COALESCE(industrial_amortization_cost,0) AS industrial_net_margin
    FROM step1_5
),

step3 AS (
    SELECT 
        *,
        COALESCE(industrial_net_margin,0) 
        + COALESCE(office_employee_cost,0) 
        + COALESCE(insurance_cost,0) 
        + COALESCE(office_amortization_cost,0) 
        + COALESCE(general_expenditures,0) 
        + COALESCE(subactivity,0) 
        + COALESCE(research_and_development,0)  AS global_net_margin
    FROM step2
)

SELECT 
   	code_product,
   	description_product,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM cp_components_report ccr2
            WHERE ccr2.line_product_code = step3.code_product
        ) 
        THEN 'COMPONENTE'
        ELSE 'PRODUCTO'
    END AS product_type,
    product_initial_amount,
    product_initial_value,
    amount_produced,
    amount_bought,
    amount_sold,
    product_final_amount,
    product_final_value,
    amount_variation,
    value_variation,
    gross_revenue,
    material_cost,
	variation_cost,
	external_work_cost,
	material_gross_margin,
	transport_cost,
    repair_cost,
    supplies_cost,
    contribution_margin,industrial_employee_cost,
    manufacturing_cost,
    industrial_net_margin,
    industrial_amortization_cost,
    office_employee_cost,
    insurance_cost,
    office_amortization_cost,
    general_expenditures,
    subactivity,
    research_and_development,
    global_net_margin,
    reference_time,
    total_time
FROM step3
        """

        self.env.cr.execute(query, {
            'fecha_inicio': self.star_date,
            'fecha_final': self.end_date,
            'id_contabilidad': self.account_report.id,
            'id_inventario': self.inventory_report.id,
        })

        rows = self.env.cr.dictfetchall()

        # Crear líneas del reporte
        for row in rows:
            self.env['cp.cost.model.line'].create({
                'cost_model_id': report.id,

                'code_product': row['code_product'],
                'description_product': row['description_product'],

                'product_initial_amount': row['product_initial_amount'],
                'product_initial_value': row['product_initial_value'],

                'amount_produced': row['amount_produced'],
                'amount_bought': row['amount_bought'],
                'amount_sold': row['amount_sold'],

                'product_final_amount': row['product_final_amount'],
                'product_final_value': row['product_final_value'],

                'amount_variation': row['amount_variation'],
                'value_variation': row['value_variation'],

                'gross_revenue': row['gross_revenue'],

                'material_cost': row['material_cost'],
                'variation_cost': row['variation_cost'],
                'external_work_cost': row['external_work_cost'],
                'material_gross_margin': row['material_gross_margin'],

                'transport_cost': row['transport_cost'],
                'repair_cost': row['repair_cost'],
                'supplies_cost': row['supplies_cost'],
                'contribution_margin': row['contribution_margin'],

                'industrial_employee_cost': row['industrial_employee_cost'],
                'industrial_amortization_cost': row['industrial_amortization_cost'],
                'manufacturing_cost': row['manufacturing_cost'],
                'industrial_net_margin': row['industrial_net_margin'],

                'office_employee_cost': row['office_employee_cost'],
                'insurance_cost': row['insurance_cost'],
                'office_amortization_cost': row['office_amortization_cost'],
                'general_expenditures': row['general_expenditures'],
                'research_and_development': row['research_and_development'],
                'subactivity': row['subactivity'],
                'global_net_margin': row['global_net_margin'],

                'reference_time': row['reference_time'],
                'total_time': row['total_time'],
                'product_type': row['product_type'],
            })

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Completada carga',
                'message': (
                    f"Se ha completado la carga del modelo de costes"
                ),
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        return action