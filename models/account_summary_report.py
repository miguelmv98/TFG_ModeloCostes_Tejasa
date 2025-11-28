# -*- coding: utf-8 -*-
import json
import os
import re
from odoo import models, fields, api, Command
import logging
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)


class InformeCostes(models.Model):
    _name = 'cp.account.summary'
    _description = 'Informe de costes anual'


    name = fields.Char(string="Descripción", required=True)
    fiscal_year = fields.Integer(string="Año Fiscal", required=True)
    industrial_employee = fields.Float(string="Trabajadores Taller", required=True)
    office_employee = fields.Float(string="Trabajadores Oficina", required=True)
    industrial_hours = fields.Float(string="Horas/año trabajador taller", required=True)
    office_hours = fields.Float(string="Horas/año trabajador oficina", required=True)
    effective_hours = fields.Float(string="Horas efectivas registradas", required=True)
    activity_level = fields.Float(string="Nivel de actividad", required=True)


    indicator_ids = fields.One2many('cp.account.indicator', 'report_id', string="Indicadores")
    table_line_ids = fields.One2many('cp.account.amortisation.table.line', 'report_id', string="Tabla de amortizaciones")

    general_indicator_ids = fields.One2many(
        'cp.account.indicator', 'general_indicator_id',
        compute='_compute_indicadores_generales',
        string="Indicadores Generales"
    )

    model_indicator_ids = fields.One2many(
        'cp.account.indicator','model_indicator_id',
        compute='_compute_indicadores_modelo',
        string="Indicadores Modelo"
    )

    hours_indicator_ids = fields.One2many(
        'cp.account.indicator','hours_indicator_id',
        compute='_compute_indicadores_horas',
        string="Indicadores Horas"
    )



    GENERAL_CODES = [
        'TRANSPORTES', 'REPARACIONES', 'ELECTRICIDAD', 'COMUNICACIONES', 'AGUA', 'BASURAS', 'EMBALAJE', 'SUMINISTROS',
        'PERSONAL_OFICINA', 'PERSONAL_TALLER', 'GASTOS_DIVERSOS', 'GASTOS_FINANCIEROS', 'ARRENDAMIENTOS', 'TRIBUTOS', 'GASTOS_NO_FABRICACION'
    ]
    HORAS_CODES = [
        'AMORTIZACION_TALLER', 'AMORTIZACION_OFICINA', 'HORAS_EFECTIVAS_TALLER', 'HORAS_EFECTIVAS_OFICINA',
        'HORAS_TOTAL_TALLER', 'HORAS_TOTAL_OFICINA', 'AMORTIZACION_HORA_TALLER', 'AMORTIZACION_HORA_OFICINA'
    ]

    def _compute_indicadores_generales(self):
        for record in self:
            record.general_indicator_ids = record.indicator_ids.filtered(lambda i: i.code in self.GENERAL_CODES)

    def _compute_indicadores_modelo(self):
        for record in self:
            record.model_indicator_ids = record.indicator_ids.filtered(lambda i: i.code.endswith('MODELO'))

    def _compute_indicadores_horas(self):
        for record in self:
            record.hours_indicator_ids = record.indicator_ids.filtered(lambda i: i.code in self.HORAS_CODES)


            
    def action_calcular_indicadores(self):
        """Botón para recalcular indicadores manualmente"""
        for rec in self:
            rec.indicator_ids.unlink()  # eliminar los anteriores
            rec._generar_indicadores()
            rec._generar_linea_tabla()


    def _generar_indicadores(self):
        self.ensure_one()
        fiscal_year = self.fiscal_year

        self.env.cr.execute("""
                            SELECT base_account_code, final_balance
                            FROM cp_account_balance_report
                            WHERE fiscal_year = %s
                            """, (fiscal_year,))
        vista_raw = self.env.cr.fetchall()

        vista_data = {}
        for codigo, valor in vista_raw:
            # Invertir signo si empieza por 6 o 7
            if str(codigo).startswith(('6', '7')):
                valor = -valor
            vista_data[str(codigo)] = valor

        indicadores_config = self._load_indicadores_config()

        indicadores_creados = {}

        # Crear indicadores de tipo standard (vienen de account_codes)
        for ind_config in [t for t in indicadores_config if t['type'] == 'standard']:
            valor = 0.0
            for acc in (ind_config['account_codes'] or '').split(','):
                acc = acc.strip()
                if acc:
                    valor += sum(v for c, v in vista_data.items() if str(c).startswith(str(acc)))

            ind = self.env['cp.account.indicator'].create({
                'report_id': self.id,
                'name': ind_config['name'],
                'code': ind_config['code'],
                'value': valor,
            })
            indicadores_creados[ind_config['code']] = ind

        #  Evaluar indicadores tipo 'function' (usan fórmulas bien formadas)
        for ind_config in [t for t in indicadores_config if t['type'] == 'function']:
            formula = ind_config['function']

            # Contexto con los valores de indicadores creados
            contexto = {code: indicadores_creados[code].value for code in indicadores_creados}

            # Reemplazar campos del padre {campo}
            def replace_field(match):
                field_name = match.group(1)
                return str(getattr(self, field_name, 0.0))

            formula_eval = re.sub(r'\{([\w_]+)\}', replace_field, formula)

            try:
                valor = eval(formula_eval, {"__builtins__": {}}, contexto)
            except Exception as e:
                _logger.warning(f"Error evaluando fórmula '{ind_config['code']}': {formula_eval} ({e})")
                valor = 0.0

            ind = self.env['cp.account.indicator'].create({
                'report_id': self.id,
                'name': ind_config['name'],
                'code': ind_config['code'],
                'value': valor,
            })
            indicadores_creados[ind_config['code']] = ind

        # Calcular valor por hora si aplica
        horas_taller_total = indicadores_creados["HORAS_TOTAL_TALLER"].value
        for ind_config in [t for t in indicadores_config if t['cost_hour'] == True]:
            ind = indicadores_creados[ind_config['code']]
            if horas_taller_total:  # Evita división por cero
                ind.write({'cost_hour_value': ind.value / horas_taller_total})
            else:
                ind.write({'cost_hour_value': 0.0})


        return True



    # ----------------------------------------------------------------------
    # CARGA DE CONFIGURACIÓN DESDE JSON
    # ----------------------------------------------------------------------
    def _load_indicadores_config(self):
        """Carga la configuración de indicadores desde un archivo JSON del módulo"""
        json_path = get_module_resource('cost_product', 'static', 'account_kpis_config.json')
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No se encontró el archivo JSON en {json_path}")
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _generar_linea_tabla(self):

        AMORTIZATION_CODES = [
            'DESARROLLO', 'AMORTIZACION_DESARROLLO', 'NETO_DESARROLLO',
            'INVESTIGACION', 'AMORTIZACION_INVESTIGACION', 'NETO_INVESTIGACION',
            'PATENTES', 'AMORTIZACION_PATENTES', 'NETO_PATENTES',
            'APP_INFORMATICAS', 'AMORTIZACION_APP_INFORMATICAS', 'NETO_APP_INFORMATICAS',
            'TERRENOS', 'AMORTIZACION_TERRENOS', 'NETO_TERRENOS',
            'CONSTRUCCIONES', 'AMORTIZACION_CONSTRUCCIONES', 'NETO_CONSTRUCCIONES',
            'MAQUINARIA', 'AMORTIZACION_MAQUINARIA', 'NETO_MAQUINARIA',
            'UTILLAJE', 'AMORTIZACION_UTILLAJE', 'NETO_UTILLAJE',
            'OTRAS_INSTALACIONES', 'AMORTIZACION_OTRAS_INSTALACIONES', 'NETO_OTRAS_INSTALACIONES',
            'MOBILIARIO', 'AMORTIZACION_MOBILIARIO', 'NETO_MOBILIARIO',
            'PROC_INFORMACION', 'AMORTIZACION_PROC_INFORMACION', 'NETO_PROC_INFORMACION',
            'ELEM_TRANSPORTE', 'AMORTIZACION_ELEM_TRANSPORTE', 'NETO_ELEM_TRANSPORTE',
            'OTRO_INMOVILIZADO_MATERIAL', 'AMORTIZACION_OTRO_INMOVILIZADO_MATERIAL', 'NETO_OTRO_INMOVILIZADO_MATERIAL'
        ]
        for record in self:
            record.table_line_ids.unlink()  # borrar las anteriores

            indicadores = record.indicator_ids.filtered(lambda i: i.code in AMORTIZATION_CODES)
            ind_dict = {ind.code: ind.value for ind in indicadores if ind.code}

            lines = []
            for ind in indicadores:
                code = ind.code or ""
                if code.startswith("AMORTIZACION_") or code.startswith("NETO_"):
                    continue

                base = code
                nombre = ind.name or base.replace("_", " ").title()
                valor = ind_dict.get(base, 0.0)
                amortizacion = ind_dict.get(f"AMORTIZACION_{base}", 0.0)
                valor_neto = ind_dict.get(f"NETO_{base}", valor + amortizacion)

                if any([valor, amortizacion, valor_neto]):
                    lines.append({
                        'report_id': record.id,
                        'name': nombre,
                        'value': valor,
                        'amortization': amortizacion,
                        'net_value': valor_neto,
                    })

            if lines:
                self.env['cp.account.amortisation.table.line'].create(lines)