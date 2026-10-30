# Arnés B2B: captación y seguimiento (demo)

Repositorio: https://github.com/valrami-hue/arnes-b2b-avril
Demo en video: https://drive.google.com/file/d/18QAh-ysZTRn0IDpI0SyH6gPgJeBX3X0W/view?usp=sharing
Autor: Valeria Ramírez Olvera

Prototipo acotado y demostrable (no es un sistema de producción) para el ticket **C2 · Primer arnés B2B** de Avril Systems.
Empresa ficticia: **LimpioMax Oficinas** (limpieza de oficinas y locales). Todos los datos son sintéticos.

**Flujo:** solicitud → clasificación → datos faltantes → preguntas de seguimiento → borrador de respuesta (no se envía) → registro en CRM de prueba.

## Instalación
Requiere Python 3.9 o superior. Sin dependencias externas y sin llaves.
```
git clone https://github.com/valrami-hue/arnes-b2b-avril.git
cd arnes-b2b-avril
```

## Ejecución
```
python3 run.py                                      # reglas (por defecto)
python3 run.py --modo modelo                        # capa de modelo con cliente SIMULADO (sin llave)
python3 run.py --modo modelo --cliente anthropic    # modelo real (solo con llave autorizada)
python3 -m unittest discover -s tests -v            # 20 pruebas
```
En Windows puede ser `python` o `py` en lugar de `python3`.
Opciones: `--config`, `--solicitudes`, `--salida`, `--respuestas`. Para otro sector basta editar `config/sector.json`.

## Esquema del CRM de prueba
`crm/leads.json` (un objeto por solicitud) y `crm/leads.csv` (resumen). Campos principales:

| Campo | Contenido |
|---|---|
| `id`, `mensaje_original` | identificador y texto de la solicitud |
| `estado` | `listo_para_validar`, `faltan_datos`, `fuera_de_alcance` o `duplicado` |
| `categoria` | `servicio`, `fuera_de_alcance` o `sin_clasificar` |
| `datos` | nombre, empresa, contacto, email, teléfono, servicio, ubicación, metros, frecuencia |
| `faltantes`, `preguntas` | datos obligatorios que faltan y la pregunta de seguimiento de cada uno |
| `banderas` | `urgente`, `pide_precio` |
| `duplicado_de`, `notas` | solicitud original si es duplicada; avisos para un asesor |
| `modo`, `origen_campos`, `borrador_origen` | si se usó modelo o reglas, y si el borrador es del modelo o de plantilla |
| `borrador_respuesta`, `enviado` | borrador propuesto y siempre `false` |

## Entradas y salidas
- Entradas: `config/sector.json` y `data/solicitudes.json` (10 solicitudes: completas, incompletas, vaga, sin contacto, fuera de alcance, duplicada, parcialmente fuera de alcance, con petición de precio y urgentes).
- Salidas: `crm/` (modo reglas) o `crm_modelo/` (modo modelo).

## Capa con modelo (opcional)
El modelo **propone** y el arnés **valida**:
1. **Extracción:** el modelo devuelve JSON con servicio, ubicación, metros, frecuencia, urgencia y petición de precio. Cada campo se valida contra el catálogo del sector; lo inválido se descarta y lo rellenan las reglas.
2. **Borrador:** el modelo redacta usando solo datos ya validados (nunca ve el mensaje original). Se rechaza si menciona precios, descuentos o promesas, trae enlaces o correos, omite alguna pregunta pendiente, o no remite al asesor cuando el prospecto pidió precio.
3. **Respaldo:** ante cualquier falla (red, JSON inválido, respuesta vacía, borrador rechazado) se usan las reglas o la plantilla, y el motivo queda en `modo` / `borrador_origen`.
4. **Seguridad:** el mensaje del prospecto se trata como dato no confiable; la llave solo se lee de `ANTHROPIC_API_KEY` y no se guarda ni se imprime; solo se envían datos sintéticos; nada se envía a prospectos.

**Clientes:** `simulado` (respuestas pregrabadas escritas a mano en `data/respuestas_simuladas.json`, **no es un modelo real**; incluye fallas a propósito: S10 con respuesta inválida y S09 con borrador que menciona un precio) y `anthropic` (API de mensajes de Anthropic con `urllib`, modelo configurable con `ARNES_MODELO`).

> **Estado de verificación:** el cliente `anthropic` se probó con una API simulada (mock) que verifica la forma de la petición, el conteo de tokens y el manejo de errores. **No se ejecutó contra la API real** porque el ticket prohíbe usar llaves reales sin permiso de Gerry/Sergio. Antes de usarlo, confirma el nombre del modelo disponible en tu cuenta.

## Pruebas (21 automáticas, todas pasan)
Casos incompletos: **S03** (faltan nombre, empresa, ubicación, metros y frecuencia), **S06** (sin contacto) y **S08** (mensaje vago, sin servicio).
También: caso completo, fuera de alcance, duplicado, que ningún borrador contenga precios, que nada se envíe y, de la capa de modelo: JSON con cercas de código, respuesta inválida, valores fuera de catálogo, borrador con precio, intento de inyección de instrucciones, cliente caído y cliente real con API simulada.

## Fallas encontradas
- **S07 (duplicado):** pedía de nuevo ubicación y metros aunque S01 ya los tenía.
- **S05 (fuera de alcance):** listaba faltantes que no tenía caso pedir.
- **S10:** menciona jardinería además de limpieza; queda `listo_para_validar` con nota para que un asesor decida.
- **Capa de modelo (ensayo con cliente simulado):** una respuesta no JSON (S10) y un borrador con precio (S09) se detectaron y se resolvieron con el respaldo.
- La clasificación por reglas depende de palabras clave (ver limitaciones).

## Cambios realizados
- S07 y S05 ya no generan lista de faltantes ni preguntas.
- Comparación de texto sin acentos ni mayúsculas, y "m²" se lee como "m2".
- El servicio se elige por mayor número de palabras clave acertadas, no por la primera coincidencia.
- Se agregó la capa de modelo con validación, respaldo a reglas y trazabilidad de qué decidió el modelo y qué las reglas.

## Limitaciones
- Las reglas usan palabras clave y no entienden sinónimos ni errores de ortografía.
- Las ubicaciones se detectan solo si están en `ubicaciones_conocidas` (el modelo puede devolver otras, pero no se valida que existan).
- El duplicado se detecta por mismo correo/teléfono y mismo servicio; no fusiona datos entre solicitudes.
- No conecta con ningún sistema real: el CRM son archivos locales y no se envían mensajes.
- Con modelo real los resultados pueden variar entre ejecuciones; por eso las salidas se validan.
- El modo `simulado` demuestra el flujo, no la calidad de un modelo real.

## Costo y tiempo aproximado de una ejecución
- Reglas: menos de 0.1 s para las 10 solicitudes, sin llamadas a modelos, costo de $0.
- Modelo simulado: igual de rápido y $0.
- Modelo real: 20 llamadas por corrida (10 de extracción y 10 de borrador). `run.py` imprime los tokens de entrada y salida; el costo en dinero depende de la tarifa vigente del modelo y no se calculó aquí. El tiempo dependerá de la red (normalmente algunos segundos por llamada).

## Cómo se desarrolló
Construido con apoyo de un asistente de IA (Claude) en una conversación y verificado ejecutando el código y las pruebas.

## Seguridad
Sin llaves, datos de clientes, producción, VPS ni repositorios protegidos. No se envían mensajes ni se publica contenido. No se prometen precios ni cotizaciones. Lo que habría que validar con un cliente antes de integrar está en `docs/validar_con_cliente.md`. Guion para la presentación: `docs/guion_demo.md`.
