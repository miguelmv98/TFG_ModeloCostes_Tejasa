# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountBalanceReport(models.Model):
    """ This model represents account.balance.report."""
    _name = 'cp.account.balance.report'
    _description = 'Reporte Balance de cuentas'
    _auto = False
    _rec_name = "account_name"

    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    fiscal_year = fields.Integer(string="Fiscal Year", readonly=True)

    base_account_code = fields.Char(string="Code", readonly=True)
    account_name = fields.Char(string="Name", readonly=True)

    starting_balance = fields.Float(string="Saldo Inicial", readonly=True)
    debit = fields.Float(string="Debe", readonly=True)
    earnings = fields.Float(string="Haber", readonly=True)
    interval_balance = fields.Float(string="Saldo Periodo", readonly=True)
    final_balance = fields.Float(string="Saldo Final", readonly=True)

    account_level_1_code = fields.Char(string="Código Nivel 1", readonly=True)
    account_level_1_name = fields.Char(string="Nombre Nivel 1", readonly=True)

    account_level_2_code = fields.Char(string="Código Nivel 2", readonly=True)
    account_level_2_name = fields.Char(string="Nombre Nivel 2", readonly=True)

    account_level_3_code = fields.Char(string="Código Nivel 3", readonly=True)
    account_level_3_name = fields.Char(string="Nombre Nivel 3", readonly=True)

    account_level_4_code = fields.Char(string="Código Nivel 4", readonly=True)
    account_level_4_name = fields.Char(string="Nombre Nivel 4", readonly=True)

    def init(self):
        """Hook to ensure the SQL view is created"""
        self.env.cr.execute("""
    CREATE OR REPLACE VIEW cp_account_balance_report AS
    (
        WITH movimientos AS (
            SELECT
                aml.account_id,
                aml.company_id,
                aml.debit,
                aml.credit,
                aml.date,
                EXTRACT(YEAR FROM aml.date)::int AS year
            FROM account_move_line aml
            JOIN account_move m ON m.id = aml.move_id
        ),
        years AS (
            SELECT DISTINCT EXTRACT(YEAR FROM date)::int AS year
            FROM movimientos
        ),
        saldo_inicial AS (
            SELECT
                aa.id AS account_id,
                rc.id AS company_id,
                y.year,
                CASE
                    WHEN aa.code LIKE '6%' OR aa.code LIKE '7%' THEN 0
                    ELSE COALESCE(SUM(m.debit - m.credit), 0)
                END AS saldo_inicial
            FROM account_account aa
            CROSS JOIN res_company rc
            CROSS JOIN years y
            LEFT JOIN movimientos m
                ON m.account_id = aa.id
               AND m.company_id = rc.id
               AND m.date < DATE (y.year || '-01-01')
            GROUP BY aa.id, rc.id, y.year, aa.code
        ),
        movimientos_periodo AS (
            SELECT
                m.account_id,
                m.company_id,
                m.year,
                COALESCE(SUM(m.debit), 0) AS debe,
                COALESCE(SUM(m.credit), 0) AS haber,
                COALESCE(SUM(m.debit - m.credit), 0) AS saldo_periodo
            FROM movimientos m
            GROUP BY m.account_id, m.company_id, m.year
        ),
        cuentas AS (
            SELECT
                ROW_NUMBER() OVER (PARTITION BY rc.id, y.year ORDER BY aa.code) AS id,
                rc.id AS company_id,
                y.year as fiscal_year,
                aa.code AS base_account_code,
                aa.name->>'en_US' AS account_name,
                COALESCE(si.saldo_inicial, 0.0) AS starting_balance,
                COALESCE(mp.debe, 0.0) AS debit,
                COALESCE(mp.haber, 0.0) AS earnings,
                COALESCE(mp.saldo_periodo, 0.0) AS interval_balance,
                COALESCE(si.saldo_inicial, 0.0) + COALESCE(mp.saldo_periodo, 0.0) AS final_balance
            FROM account_account aa
            CROSS JOIN res_company rc
            CROSS JOIN years y
            LEFT JOIN saldo_inicial si
                ON si.account_id = aa.id AND si.company_id = rc.id AND si.year = y.year
            LEFT JOIN movimientos_periodo mp
                ON mp.account_id = aa.id AND mp.company_id = rc.id AND mp.year = y.year
            WHERE COALESCE(si.saldo_inicial,0) <> 0
               OR COALESCE(mp.debe,0) <> 0
               OR COALESCE(mp.haber,0) <> 0
               OR COALESCE(mp.saldo_periodo,0) <> 0
        )
        SELECT
            c.*,
            g1.code_prefix_start AS account_level_1_code,
            COALESCE(g1.name->>'es_ES', g1.name->>'en_US', g1.name::text) AS account_level_1_name,
            g2.code_prefix_start AS account_level_2_code,
            COALESCE(g2.name->>'es_ES', g2.name->>'en_US', g2.name::text) AS account_level_2_name,
            g3.code_prefix_start AS account_level_3_code,
            COALESCE(g3.name->>'es_ES', g3.name->>'en_US', g3.name::text) AS account_level_3_name,
            g4.code_prefix_start AS account_level_4_code,
            COALESCE(g4.name->>'es_ES', g4.name->>'en_US', g4.name::text) AS account_level_4_name
        FROM cuentas c
        JOIN account_account aa ON aa.code = c.base_account_code
        LEFT JOIN LATERAL (
          SELECT ag.id, ag.code_prefix_start, ag.name
          FROM account_group ag
          WHERE ag.level = 0
            AND trim(ag.code_prefix_start) = trim(left(aa.code, 1))
          ORDER BY ag.id
          LIMIT 1
        ) g1 ON true
        LEFT JOIN LATERAL (
          SELECT ag.id, ag.code_prefix_start, ag.name
          FROM account_group ag
          WHERE ag.level = 1
            AND trim(ag.code_prefix_start) = trim(left(aa.code, 2))
          ORDER BY ag.id
          LIMIT 1
        ) g2 ON true
        LEFT JOIN LATERAL (
          SELECT ag.id, ag.code_prefix_start, ag.name
          FROM account_group ag
          WHERE ag.level = 2
            AND trim(ag.code_prefix_start) = trim(left(aa.code, 3))
          ORDER BY ag.id
          LIMIT 1
        ) g3 ON true
        LEFT JOIN LATERAL (
          SELECT ag.id, ag.code_prefix_start, ag.name
          FROM account_group ag
          WHERE ag.level = 3
            AND trim(ag.code_prefix_start) = trim(left(aa.code, 4))
          ORDER BY ag.id
          LIMIT 1
        ) g4 ON true
    )
                            """)
