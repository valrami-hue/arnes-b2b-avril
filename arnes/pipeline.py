"""Flujo: solicitud -> clasificación -> datos faltantes -> preguntas -> borrador.
Solo biblioteca estándar. No envía nada: los borradores solo se guardan."""
import json
import re
import unicodedata
from pathlib import Path

from . import modelo


def norm(texto):
    """Minúsculas, sin acentos y con ² -> 2, para comparar palabras clave."""
    t = unicodedata.normalize("NFKD", (texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cargar_json(ruta):
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def _contiene(texto_norm, palabras):
    return [p for p in palabras if norm(p) in texto_norm]


def _frecuencia(t):
    if re.search(r"diari|todos los dias", t): return "diaria"
    if re.search(r"semanal|por semana|cada semana", t): return "semanal"
    if re.search(r"quincenal", t): return "quincenal"
    if re.search(r"mensual|cada mes|al mes", t): return "mensual"
    if re.search(r"una vez|una sola vez|unica vez", t): return "unica"
    return None


def _metros(t):
    m = re.search(r"(\d[\d,\.]*)\s*(?:m2|mts2|mts|metros cuadrados|metros)", t)
    if not m:
        return None
    try:
        return int(float(m.group(1).replace(",", "")))
    except ValueError:
        return None


def clasificar(sol, cfg):
    """Devuelve datos extraídos, categoría, banderas y notas."""
    t = norm(sol["mensaje"])
    r = sol.get("remitente", {})
    notas = []

    # servicio: gana el que más palabras clave acierte
    puntajes = {sid: len(_contiene(t, s["palabras"])) for sid, s in cfg["servicios"].items()}
    mejor = max(puntajes, key=puntajes.get)
    servicio = mejor if puntajes[mejor] > 0 else None

    fuera = _contiene(t, cfg["fuera_de_alcance"])
    if servicio is None and fuera:
        categoria = "fuera_de_alcance"
    elif servicio is None:
        categoria = "sin_clasificar"
    else:
        categoria = "servicio"
        if fuera:
            notas.append("Parte de la solicitud (%s) está fuera de alcance." % ", ".join(fuera))

    ubic = next((u for u in cfg["ubicaciones_conocidas"] if norm(u) in t), None)
    email, tel = (r.get("email") or "").strip(), (r.get("telefono") or "").strip()
    datos = {
        "nombre": (r.get("nombre") or "").strip() or None,
        "empresa": (r.get("empresa") or "").strip() or None,
        "contacto": email or tel or None,
        "email": email or None,
        "telefono": tel or None,
        "servicio": servicio,
        "ubicacion": ubic,
        "metros": _metros(t),
        "frecuencia": _frecuencia(t),
    }
    banderas = {
        "urgente": bool(_contiene(t, cfg["palabras_urgencia"])),
        "pide_precio": bool(_contiene(t, cfg["palabras_precio"])),
    }
    return datos, categoria, banderas, notas


def faltantes(datos, cfg):
    return [c for c in cfg["campos_obligatorios"] if not datos.get(c)]


def preguntas(falt, cfg):
    return [cfg["preguntas"][c] for c in falt]


def borrador(lead, cfg):
    emp = cfg["empresa_ficticia"]
    nombre = lead["datos"]["nombre"]
    saludo = "Hola %s," % nombre.split()[0] if nombre else "Hola,"
    est = lead["estado"]
    if est == "fuera_de_alcance":
        cuerpo = ("Gracias por escribir a %s. Por ahora nos especializamos en %s, "
                  "así que no podemos atender esta solicitud. Agradecemos su interés."
                  % (emp, cfg["sector"].split(" (")[0]))
        return "%s\n\n%s" % (saludo, cuerpo)
    if est == "duplicado":
        cuerpo = ("Gracias por escribir de nuevo a %s. Ya tenemos registrada su solicitud (%s) "
                  "y un asesor le dará seguimiento." % (emp, lead["duplicado_de"]))
        return "%s\n\n%s" % (saludo, cuerpo)
    partes = ["Gracias por escribir a %s." % emp]
    if lead["datos"]["servicio"]:
        partes.append("Recibimos su solicitud de: %s." % cfg["servicios"][lead["datos"]["servicio"]]["nombre"].lower())
    if lead["banderas"]["pide_precio"]:
        partes.append("Por este medio no compartimos precios ni cotizaciones; un asesor le dará seguimiento "
                      "una vez que confirmemos los detalles.")
    if lead["banderas"]["urgente"]:
        partes.append("Notamos que es urgente y lo marcamos como prioritario.")
    if lead["preguntas"]:
        partes.append("Para canalizarla con un asesor, ¿nos ayuda a confirmar lo siguiente?")
        partes.append("\n".join("- " + q for q in lead["preguntas"]))
    else:
        partes.append("Tenemos la información necesaria; un asesor se pondrá en contacto para validar los detalles.")
    return "%s\n\n%s" % (saludo, "\n".join(partes))


def procesar(solicitudes, cfg, cliente=None):
    """Sin cliente: solo reglas. Con cliente (modelo): el modelo propone y las reglas respaldan."""
    leads, vistos = [], {}
    for sol in solicitudes:
        datos, categoria, banderas, notas = clasificar(sol, cfg)
        origen = {c: "reglas" for c in ("servicio", "ubicacion", "metros", "frecuencia")}
        modo = "reglas"
        if cliente is not None:
            try:
                ext = modelo.extraer(sol, cfg, cliente)
                datos, categoria, banderas, notas, origen = modelo.fusionar(ext, datos, categoria, banderas, notas)
                modo = "modelo"
            except modelo.ErrorModelo as e:
                modo = "reglas (fallback: %s)" % e
        falt = faltantes(datos, cfg)
        dup = None
        if datos["contacto"] and datos["servicio"]:
            clave = ((datos["email"] or datos["telefono"]).lower(), datos["servicio"])
            dup = vistos.get(clave)
            vistos.setdefault(clave, sol["id"])
        if categoria == "fuera_de_alcance":
            estado = "fuera_de_alcance"
        elif dup:
            estado = "duplicado"
        elif falt:
            estado = "faltan_datos"
        else:
            estado = "listo_para_validar"
        sin_pendientes = estado in ("fuera_de_alcance", "duplicado")
        lead = {
            "id": sol["id"], "mensaje_original": sol["mensaje"], "categoria": categoria,
            "estado": estado, "datos": datos,
            "faltantes": [] if sin_pendientes else falt,
            "preguntas": [] if sin_pendientes else preguntas(falt, cfg),
            "banderas": banderas, "duplicado_de": dup, "notas": notas,
            "modo": modo, "origen_campos": origen,
        }
        lead["borrador_respuesta"] = borrador(lead, cfg)
        lead["borrador_origen"] = "plantilla"
        if cliente is not None:
            try:
                lead["borrador_respuesta"] = modelo.redactar(lead, cfg, cliente)
                lead["borrador_origen"] = "modelo"
            except modelo.ErrorModelo as e:
                lead["borrador_origen"] = "plantilla (fallback: %s)" % e
        lead["enviado"] = False  # nunca se envía nada
        leads.append(lead)
    return leads
