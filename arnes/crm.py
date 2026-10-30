"""CRM de prueba: JSON (completo) + CSV (resumen). Archivos locales, sin sistemas reales."""
import csv
import json
from pathlib import Path

COLUMNAS = ["id", "estado", "categoria", "servicio", "nombre", "empresa", "contacto",
            "ubicacion", "metros", "frecuencia", "faltantes", "urgente", "pide_precio",
            "modo", "borrador_origen", "enviado"]


def guardar(leads, carpeta):
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / "leads.json").write_text(json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(carpeta / "leads.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNAS)
        for l in leads:
            d = l["datos"]
            w.writerow([l["id"], l["estado"], l["categoria"], d["servicio"] or "", d["nombre"] or "",
                        d["empresa"] or "", d["contacto"] or "", d["ubicacion"] or "", d["metros"] or "",
                        d["frecuencia"] or "", ";".join(l["faltantes"]), l["banderas"]["urgente"],
                        l["banderas"]["pide_precio"], l["modo"], l["borrador_origen"], l["enviado"]])
