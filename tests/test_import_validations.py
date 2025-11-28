from odoo.tests.common import TransactionCase
import unittest
from datetime import datetime
import pandas as pd
from ..wizard.time_record_wizard import (
    ParallelWorkValidation,
    EmployeeExistValidation,
    CloseOrderValidation
)


class TestImportValidations(unittest.TestCase):

    def setUp(self):
        super().setUp()
        # Crear empleado de prueba en la BD
        self.employee = self.env['hr.employee'].create({'name': 'Juan Perez'})

        # DataFrame base para pruebas
        self.df = pd.DataFrame([
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 8, 0), "Código": 1, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 12, 0), "Código": 2, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 13, 0), "Código": 1, "OF": "OF002"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 16, 0), "Código": 2, "OF": "OF002"},
        ])

    # ------------------------
    # ParallelWorkValidation
    # ------------------------
    def test_parallel_work_no_overlap(self):

        validation = ParallelWorkValidation()
        record = {
            'empleado': "Juan Perez",
            'orden_fabricacion': "OF001",
            'tiempo_inicio': datetime(2023, 1, 1, 8, 0),
            'tiempo_final': datetime(2023, 1, 1, 12, 0)
        }
        ok, msg = validation.validate(self.env, record, self.df, None)
        self.assertTrue(ok)
        self.assertIsNone(msg)

    def test_parallel_work_with_overlap(self):

        validation = ParallelWorkValidation()
        record = {
            'empleado': "Juan Perez",
            'orden_fabricacion': "OF002",
            'tiempo_inicio': datetime(2023, 1, 1, 10, 0),
            'tiempo_final': datetime(2023, 1, 1, 14, 0)
        }
        ok, msg = validation.validate(self.env, record, self.df, None)
        self.assertFalse(ok)
        self.assertIn("solapamiento", msg)

    # ------------------------
    # EmployeeExistValidation
    # ------------------------
    def test_employee_exists(self):

        validation = EmployeeExistValidation()
        record = {'empleado': "Juan Perez"}
        ok, msg = validation.validate(self.env, record, self.df, None)
        self.assertTrue(ok)

    def test_employee_not_exists(self):

        validation = EmployeeExistValidation()
        record = {'empleado': "Empleado Fantasma"}
        ok, msg = validation.validate(self.env, record, self.df, None)
        self.assertFalse(ok)
        self.assertIn("no existe", msg)

    # ------------------------
    # CloseOrderValidation
    # ------------------------
    def test_close_order_with_one_closure(self):

        validation = CloseOrderValidation()
        record = {'orden_fabricacion': "OF001"}
        df = pd.DataFrame([
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 8, 0), "Código": 1, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 12, 0), "Código": 3, "OF": "OF001"},
        ])
        ok, msg = validation.validate(self.env, record, df, None)
        self.assertTrue(ok)

    def test_close_order_with_multiple_closures(self):

        validation = CloseOrderValidation()
        record = {'orden_fabricacion': "OF001"}
        df = pd.DataFrame([
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 8, 0), "Código": 1, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 12, 0), "Código": 3, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 13, 0), "Código": 3, "OF": "OF001"},
        ])
        ok, msg = validation.validate(self.env, record, df, None)
        self.assertFalse(ok)
        self.assertIn("múltiples cierres", msg)

    def test_close_order_without_closure(self):

        validation = CloseOrderValidation()
        record = {'orden_fabricacion': "OF001"}
        df = pd.DataFrame([
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 8, 0), "Código": 1, "OF": "OF001"},
            {"Empleado": "Juan Perez", "Fecha/hora": datetime(2023, 1, 1, 12, 0), "Código": 2, "OF": "OF001"},
        ])
        ok, msg = validation.validate(self.env, record, df, None)
        self.assertFalse(ok)
        self.assertIn("no tiene cierre", msg)
