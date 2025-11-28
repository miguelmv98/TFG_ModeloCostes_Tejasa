import base64
import io
import pandas as pd
from odoo import models, fields, api
from odoo.exceptions import ValidationError


# -------------------------
# Base Strategy
# -------------------------
class ImportValidationStrategy:
    def validate(self, env, record, df, wizard):
        """
        Debe devolver (bool, str)
        - bool = True si pasa la validación, False si debe loguearse
        - str  = mensaje de error si no pasa
        """
        return True, None


# -------------------------
# Estrategias concretas
# -------------------------
class ParallelWorkValidation(ImportValidationStrategy):
    """Valida si el empleado tiene trabajos paralelos en diferentes OF."""

    def validate(self, env, record, df, wizard):
        empleado = record["empleado"]
        inicio = record["tiempo_inicio"]
        fin = record["tiempo_final"]

        # Reconstruir intervalos de todos los trabajos del mismo empleado
        trabajos = []
        i = 0
        df_emp = df[df["Empleado"] == empleado].sort_values(["OF", "Fecha/hora"]).reset_index(drop=True)

        while i < len(df_emp) - 1:
            fila_actual = df_emp.iloc[i]
            fila_siguiente = df_emp.iloc[i + 1]

            if fila_actual["Código"] == 1 and fila_siguiente["Código"] in [2, 3] \
               and fila_actual["OF"] == fila_siguiente["OF"]:
                trabajos.append({
                    "of": fila_actual["OF"],
                    "inicio": fila_actual["Fecha/hora"],
                    "fin": fila_siguiente["Fecha/hora"]
                })
                i += 2
            else:
                i += 1

        # Comprobar solapamientos con otras OF
        for t in trabajos:
            if t["of"] != record["production_order"]:
                if (t["inicio"] < fin) and (t["fin"] > inicio):
                    return False, f"Empleado {empleado} tiene solapamiento entre OF {record['production_order']} y {t['of']}"

        return True, None


class EmployeeExistValidation(ImportValidationStrategy):
    """Valida si el empleado existe en la BD de Odoo."""

    def validate(self, env, record, df, wizard):
        empleado = record["empleado"]
        exists = env['hr.employee'].search([('name', '=', empleado)], limit=1)
        if not exists:
            return False, f"Empleado {empleado} no existe en Odoo"
        return True, None


class CloseOrderValidation(ImportValidationStrategy):
    """Valida que cada orden tenga exactamente un cierre con código 3."""

    def validate(self, env, record, df, wizard):
        of = record["orden_fabricacion"]

        registros_of = df[df["OF"] == of]
        cierres = registros_of[registros_of["Código"] == 3]

        if len(cierres) > 1:
            return False, f"Orden {of} tiene múltiples cierres (código 3)"
        if len(cierres) == 0:
            return False, f"Orden {of} no tiene cierre en código 3"
        return True, None


# -------------------------
# Wizard principal
# -------------------------
class ImportTimeRecordWizard(models.TransientModel):
    _name = 'cp.time.record.wizard'
    _description = 'Time Record Wizard'

    excel_file = fields.Binary(string="Archivo Excel")
    file_name = fields.Char(string="Nombre del Archivo")

    start_date = fields.Date(string="Fecha Inicio")
    end_date = fields.Date(string="Fecha Fin")

    check_parallel_work = fields.Boolean(string="Avisar por trabajos paralelos")
    check_existing_employee = fields.Boolean(string="Avisar si el empleado no existe")
    check_closed_order = fields.Boolean(string="Avisar por cierres incorrectos en código 3")

    def _get_validations(self):
        strategies = []
        if self.check_parallel_work:
            strategies.append(ParallelWorkValidation())
        if self.check_existing_employee:
            strategies.append(EmployeeExistValidation())
        if self.check_closed_order:
            strategies.append(CloseOrderValidation())
        return strategies

    def importar_tiempos(self):
        if not self.excel_file:
            raise ValidationError("Debes cargar un archivo Excel.")

        datos = base64.b64decode(self.excel_file)
        hojas = pd.read_excel(io.BytesIO(datos), sheet_name=None, header=None)

        contador_creados = 0
        contador_fallos = 0
        contador_duplicados_bd = 0
        duplicados_locales = set()

        validations = self._get_validations()

        for nombre_hoja, df_original in hojas.items():
            if df_original.empty:
                continue

            # Buscar fila donde está el encabezado real ("Empleado")
            fila_header = None
            for i, fila in df_original.iterrows():
                if fila.astype(str).str.contains("Empleado", case=False, na=False).any():
                    fila_header = i
                    break
            if fila_header is None:
                continue

            # Leer con encabezado real
            df = pd.read_excel(io.BytesIO(datos), sheet_name=nombre_hoja, header=fila_header, usecols="A:D")

            columnas_esperadas = ["Empleado", "Fecha/hora", "Código", "OF"]
            if list(df.columns[:4]) != columnas_esperadas:
                continue

            df["Fecha/hora"] = pd.to_datetime(df["Fecha/hora"], errors="coerce")
            df = df.dropna(subset=["Fecha/hora"])

            # Filtrar por fechas
            if self.start_date:
                df = df[df["Fecha/hora"] >= pd.to_datetime(self.start_date)]
            if self.end_date:
                df = df[df["Fecha/hora"] <= pd.to_datetime(self.end_date)]

            # Ordenar
            df = df.sort_values(by=["Empleado", "OF", "Fecha/hora"]).reset_index(drop=True)

            i = 0
            while i < len(df) - 1:
                fila_actual = df.iloc[i]
                fila_siguiente = df.iloc[i + 1]

                if fila_actual["Código"] == 1 and fila_siguiente["Código"] in [2, 3]:
                    if (
                        fila_actual["Empleado"] == fila_siguiente["Empleado"]
                        and fila_actual["OF"] == fila_siguiente["OF"]
                    ):
                        record = {
                            'employee': fila_actual["Empleado"],
                            'production_order': fila_actual["OF"],
                            'start_date': fila_actual["Fecha/hora"],
                            'end_date': fila_siguiente["Fecha/hora"]
                        }

                        # Validaciones opcionales
                        valido = True
                        for v in validations:
                            ok, msg = v.validate(self.env, record, df, self)
                            if not ok:
                                self.env['cp.time.record.wizard.log'].create({
                                    'file_name': self.file_name,
                                    'employee': record['employee'],
                                    'production_order': record['production_order'],
                                    'start_date': record['start_date'],
                                    'error': msg,
                                })
                                contador_fallos += 1
                                valido = False
                                break

                        if valido:
                            clave = (record['employee'], record['production_order'],
                                     record['start_date'], record['end_date'])

                            if clave in duplicados_locales:
                                # Duplicado en el mismo Excel
                                self.env['cp.time.record.wizard.log'].create({
                                    'file_name': self.file_name,
                                    'employee': record['employee'],
                                    'production_order': record['production_order'],
                                    'start_date': record['start_date'],
                                    'error': 'Duplicado en el mismo archivo'
                                })
                                contador_fallos += 1
                            else:
                                try:
                                    with self.env.cr.savepoint():
                                        self.env['cp.time.record'].create(record)
                                        duplicados_locales.add(clave)
                                        contador_creados += 1
                                except Exception:
                                    # Duplicado ya en BD
                                    contador_duplicados_bd += 1
                        i += 2
                    else:
                        i += 2
                        self.env['cp.time.record.wizard.log'].create({
                            'file_name': self.file_name,
                            'employee': fila_actual["Empleado"],
                            'production_order': fila_actual["OF"],
                            'start_date': fila_actual["Fecha/hora"],
                            'error': 'El empleado o la orden de montaje no coinciden'
                        })
                        contador_fallos += 1
                else:
                    i += 1

        action = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Completada carga',
                'message': (
                    f"Se han creado {contador_creados} registros, "
                    f"se han encontrado {contador_fallos} fallos y "
                    f"{contador_duplicados_bd} registros guardados previamente."
                ),
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
        return action
