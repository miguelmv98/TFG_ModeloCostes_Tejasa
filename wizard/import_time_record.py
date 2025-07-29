import base64
import io
import pandas as pd
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ImportTimeRecordWizard(models.TransientModel):
    _name = 'import.time.record.wizard'
    _description = 'Importar Tiempos desde Excel'

    archivo_excel = fields.Binary(string="Archivo Excel", required=True)
    nombre_archivo = fields.Char(string="Nombre del Archivo")

    def importar_tiempos(self):
        if not self.archivo_excel:
            raise ValidationError("Debes cargar un archivo Excel.")

        datos = base64.b64decode(self.archivo_excel)
        df = pd.read_excel(io.BytesIO(datos))

        # Validar columnas necesarias
        columnas_requeridas = ['Empleado', 'Fecha/hora', 'Código', 'OF']
        if not all(col in df.columns for col in columnas_requeridas):
            raise ValidationError(f"El archivo debe contener las columnas: {', '.join(columnas_requeridas)}")

        # Agrupar por orden y empleado
        df['OF'] = df['OF']
        agrupado = df.groupby(['OF', 'Empleado'])

        for (OF, Empleado), grupo in agrupado:
            fila_inicio = grupo[['codigo'] == 1]
            fila_fin = grupo[['codigo'] == 3 | 2]

            if fila_inicio.empty or fila_fin.empty:
                continue

            self.env['costproduct.timerecord'].create({
                'empleado': Empleado,
                'orden_fabricacion': OF,
                'tiempo_inicio': fila_inicio['fecha_hora'].values[0],
                'tiempo_final': fila_fin['fecha_hora'].values[0],
            })
