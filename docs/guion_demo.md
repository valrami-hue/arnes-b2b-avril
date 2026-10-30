# Guion de demo (3–4 minutos)

**Antes de grabar o presentar:** abre la terminal en la carpeta del repo y ten `crm/` y `crm_modelo/` borrados o listos para regenerarse. No uses ninguna llave en la demo.

1. **Contexto (20 s).** "Es un prototipo para una empresa ficticia de limpieza de oficinas. Recibe una solicitud, la clasifica, detecta datos faltantes, prepara preguntas y un borrador, y lo registra en un CRM de prueba. No envía nada ni da precios."
2. **Modo reglas (40 s).** `python3 run.py`. Señala S03 (faltan datos), S05 (fuera de alcance), S07 (duplicado).
3. **Detalle (40 s).** Abre `crm/leads.json` en S03: datos extraídos, faltantes, preguntas, borrador con `"enviado": false`.
4. **Capa de modelo (60 s).** `python3 run.py --modo modelo`. Explica: "Este modo usa un cliente simulado con respuestas pregrabadas para que la demo funcione sin llaves; con una llave autorizada se usa `--cliente anthropic`." Señala las columnas EXTRACCION y BORRADOR: S10 cayó a reglas porque la respuesta fue inválida, y S09 usó plantilla porque el borrador mencionaba un precio.
5. **Pruebas (30 s).** `python3 -m unittest discover -s tests -v` (20 pruebas).
6. **Cierre (30 s).** Limitaciones y `docs/validar_con_cliente.md`.

## Preguntas probables y respuesta honesta
- **¿Esto usa IA?** Tiene dos modos: reglas (base) y capa de modelo. En la demo el modelo es simulado; el cliente real está implementado y probado con la API simulada (mock), pero no se ejecutó contra la API real porque no hay llave autorizada.
- **¿Qué pasa si el modelo se equivoca?** Sus respuestas se validan contra el catálogo del sector; lo inválido se descarta y se usa la regla. Un borrador con precios, promesas, enlaces o sin las preguntas pendientes se rechaza.
- **¿Y si el mensaje trae instrucciones maliciosas?** El texto se trata como dato no confiable, el modelo que redacta nunca ve el mensaje original, y hay una prueba con un intento de inyección.
- **¿Cuánto cuesta?** Reglas: $0. Con modelo real: unas 20 llamadas por corrida (10 de extracción y 10 de borrador); `run.py` imprime los tokens usados.
- **¿Cómo se adapta a otro sector?** Editando `config/sector.json`.
