# -*- coding: utf-8 -*-
from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

# Nombres válidos para el departamento de Ventas (sin importar mayúsculas/tildes)
_DEPT_VENTAS = {'ventas', 'sales', 'venta', 'ventas y distribucion', 'ventas y distribución'}
# Nombres válidos para el puesto Vendedor
_JOB_VENDEDOR = {'vendedor', 'vendedora', 'salesperson', 'seller', 'agente de ventas', 'ejecutivo de ventas'}


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ─────────────────────────────────────────────────────────────────────────
    # ORM Hooks
    # ─────────────────────────────────────────────────────────────────────────

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee in employees:
            employee._sync_vendedor_touch()
        return employees

    def write(self, vals):
        res = super().write(vals)
        # Solo re-evaluar si cambian los campos relevantes
        if any(f in vals for f in ('department_id', 'job_id', 'user_id')):
            for employee in self:
                employee._sync_vendedor_touch()
        return res

    # ─────────────────────────────────────────────────────────────────────────
    # Lógica de Sincronización
    # ─────────────────────────────────────────────────────────────────────────

    def _sync_vendedor_touch(self):
        """
        Activa o desactiva automáticamente el modo 'Vendedor Solo Cotizador Touch'
        en el usuario vinculado, basándose en el Departamento y Puesto del empleado.

        Regla:  Departamento = Ventas  AND  Puesto = Vendedor  →  Solo Cotizador Touch
        """
        self.ensure_one()

        if not self.user_id:
            return  # Empleado sin usuario en el sistema, nada que hacer

        dept_name = (self.department_id.name or '').strip().lower()
        job_name = (self.job_id.name or '').strip().lower()

        es_vendedor = dept_name in _DEPT_VENTAS and job_name in _JOB_VENDEDOR

        user = self.user_id.sudo()

        if es_vendedor and not user.x_is_vendedor_touch:
            _logger.info(
                "[KamaleonERP] AUTO: Activando modo Cotizador Touch para usuario '%s' "
                "(empleado: '%s', dept: '%s', puesto: '%s')",
                user.name, self.name, self.department_id.name, self.job_id.name,
            )
            user.write({'x_is_vendedor_touch': True})

        elif not es_vendedor and user.x_is_vendedor_touch:
            _logger.info(
                "[KamaleonERP] AUTO: Desactivando modo Cotizador Touch para usuario '%s' "
                "(empleado: '%s', dept: '%s', puesto: '%s')",
                user.name, self.name, self.department_id.name, self.job_id.name,
            )
            user.write({'x_is_vendedor_touch': False})
