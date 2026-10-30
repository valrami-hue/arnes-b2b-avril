---
name: captacion-b2b
description: Procesa solicitudes ficticias de prospectos (clasifica, detecta datos faltantes, prepara preguntas y borradores sin enviar) y las registra en un CRM de prueba JSON/CSV, con capa opcional de modelo.
---

# Captación y seguimiento B2B (demo)

Úsalo cuando se pida procesar solicitudes sintéticas de prospectos con el arnés de este repo.

## Cómo ejecutarlo
1. `python3 run.py` -> solo reglas, sin llaves (usa `config/sector.json` y `data/solicitudes.json`).
2. `python3 run.py --modo modelo` -> capa de modelo con cliente SIMULADO (respuestas pregrabadas, sin llave).
3. `python3 run.py --modo modelo --cliente anthropic` -> modelo real. Solo con una llave autorizada por Gerry/Sergio,
   definida en `ANTHROPIC_API_KEY`. Nunca escribas la llave en archivos.
4. Revisa `crm/` o `crm_modelo/`: `leads.json` (detalle) y `leads.csv` (resumen).
5. Otro sector: cambia solo `config/sector.json`.

## Reglas
- Solo datos sintéticos. Nunca usar datos de clientes reales, VPS ni sistemas externos.
- Nunca enviar mensajes: los borradores quedan con `enviado: false`.
- Nunca prometer precios ni cotizaciones (el arnés rechaza borradores que los mencionen).
- Si el modelo falla o devuelve algo inválido, se usan las reglas.
