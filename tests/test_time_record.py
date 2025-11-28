import datetime

from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestTimeRecord(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestTimeRecord, cls).setUpClass()

        cls.properties = cls.env['costproduct.timerecord'].create([
            {'empleado':'Test1','orden_fabricacion':'OMTestCase1','tiempo_inicio':datetime.datetime.now(), 'tiempo_final':datetime.datetime.now() + datetime.timedelta(hours=1) },
        ])

    def test_creation(self):
        self.assertRecordValues(self.properties, [
            {'empleado': 'Test1', 'orden_fabricacion': 'OMTestCase1','duracion_horas':1,'duracion_hms': '01:00:00'}
        ])

    def test_sql_constraint_uniqueness(self):

        tiempo_inicio = datetime.datetime.now()
        tiempo_final = datetime.datetime.now() + datetime.timedelta(hours=1)

        self.env['costproduct.timerecord'].create({
            'empleado':'Test3','orden_fabricacion':'OMTestCase3', 'tiempo_inicio': tiempo_inicio, 'tiempo_final': tiempo_final
        })
        with self.assertRaises(ValidationError):
            self.env['costproduct.timerecord'].create({'empleado':'Test3','orden_fabricacion':'OMTestCase3', 'tiempo_inicio': tiempo_inicio, 'tiempo_final': tiempo_final})

    @classmethod
    def tearDownClass(self):
        self.registry.reset_changes()
        super(TestTimeRecord, self).tearDownClass()