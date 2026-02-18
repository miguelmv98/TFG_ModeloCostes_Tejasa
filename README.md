# Modelo de Costes de Producción en Odoo

**Autor:** Miguel Monje Velarde  
**Tipo de proyecto:** Trabajo Fin de Grado (TFG)  
**Tecnología principal:** Odoo (Python)

## Descripción del proyecto

Este proyecto consiste en el desarrollo de un **modelo de costes de producción integrado en Odoo**, orientado a mejorar el cálculo, análisis y gestión de costes en entornos industriales o productivos.

El sistema se implementa como un **módulo personalizado de Odoo**, extendiendo funcionalidades estándar del ERP para permitir:

- Cálculo detallado de costes de producción
- Integración con hojas de cálculo para exportación y tratamiento de datos
- Automatización de procesos de análisis de costes

El objetivo principal es proporcionar una herramienta flexible y extensible que pueda integrarse en instalaciones reales de Odoo.

## Arquitectura

El proyecto está desarrollado como un **módulo instalable de Odoo**, siguiendo la arquitectura modular del framework:

- Backend en Python
- Integración con modelos ORM de Odoo
- Procesamiento de datos con librerías externas (Python)
- Generación de salidas compatibles con Excel

### Entorno de ejecución obligatorio

 **Importante:**  
> Este proyecto **NO es una aplicación standalone**.  
> El código debe ejecutarse **dentro de una instalación funcional de Odoo**.

Para probar el módulo correctamente:

1. Instalar Odoo en el sistema.
2. Copiar el proyecto dentro de la carpeta "extra-modules" dentro de la instalación de Odoo
