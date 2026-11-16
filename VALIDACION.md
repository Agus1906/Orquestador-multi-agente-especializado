# Validación de la entrega

Fecha: 16 de noviembre de 2026. Python 3.12; dependencias exactas en `requirements-lock.txt`.

- **21 pruebas automatizadas aprobadas** con `python -m pytest -q`.
- `python -m ruff check .`: sin observaciones.
- `python -m pip check`: sin dependencias incompatibles.
- CLI offline ejecutada con consulta predeterminada: investigación → análisis → síntesis; 190 horas/mes simuladas, 74,03 % de reducción ponderada.
- Notebook generado y ejecutado de principio a fin mediante `scripts/build_demo.py`: delegación, estado, refinamiento y parada. Salidas guardadas en el `.ipynb`.
- Modo LLM probado con un transporte simulado que ejercita structured output y tool calling. **No se ejecutó una llamada real a OpenAI.**
- La inspección visual del notebook renderizado queda pendiente: la política del navegador de este entorno bloqueó abrir archivos locales. La ejecución y la validación del formato no reemplazan esa revisión visual. No hay gráficos ni contenido dependiente de servicios externos en la demo.

La evidencia es ficticia y local. Esta entrega valida la orquestación y los cálculos del prototipo; no constituye medición de un proceso productivo ni certifica datos externos.
