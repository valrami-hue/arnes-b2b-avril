"""Ejecuta el arnés.

  python3 run.py                                  # solo reglas (por defecto, sin llaves)
  python3 run.py --modo modelo                    # capa de modelo con cliente SIMULADO (sin llave)
  python3 run.py --modo modelo --cliente anthropic   # modelo real (requiere ANTHROPIC_API_KEY autorizada)
"""
import argparse
import sys
import time

from arnes import crm, modelo, pipeline


def _corto(texto, n):
    return texto if len(texto) <= n else texto[:n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/sector.json")
    ap.add_argument("--solicitudes", default="data/solicitudes.json")
    ap.add_argument("--salida", default=None)
    ap.add_argument("--modo", choices=["reglas", "modelo"], default="reglas")
    ap.add_argument("--cliente", choices=["simulado", "anthropic"], default="simulado")
    ap.add_argument("--respuestas", default="data/respuestas_simuladas.json")
    a = ap.parse_args()

    cliente = None
    if a.modo == "modelo":
        try:
            if a.cliente == "anthropic":
                cliente = modelo.ClienteAnthropic()
            else:
                cliente = modelo.ClienteSimulado(pipeline.cargar_json(a.respuestas))
        except modelo.ErrorModelo as e:
            print("No se pudo iniciar el cliente: %s.\nUsa --cliente simulado o define ANTHROPIC_API_KEY "
                  "(solo con una llave autorizada)." % e)
            return 2
    salida = a.salida or ("crm_modelo" if cliente else "crm")

    t0 = time.perf_counter()
    cfg = pipeline.cargar_json(a.config)
    leads = pipeline.procesar(pipeline.cargar_json(a.solicitudes), cfg, cliente)
    crm.guardar(leads, salida)
    dt = time.perf_counter() - t0

    print("Sector: %s" % cfg["sector"])
    print("Modo: %s\n" % ("reglas" if cliente is None else "modelo -> " + cliente.nombre))
    print("%-4s %-19s %-21s %-24s %s" % ("ID", "ESTADO", "SERVICIO", "EXTRACCION", "BORRADOR"))
    for l in leads:
        print("%-4s %-19s %-21s %-24s %s" % (l["id"], l["estado"], l["datos"]["servicio"] or "-",
                                             _corto(l["modo"], 24), _corto(l["borrador_origen"], 40)))
    print("\n%d solicitudes en %.3f s. CRM en %s/ (borradores NO enviados)." % (len(leads), dt, salida))
    if cliente is not None:
        print("Llamadas al cliente: %d | tokens entrada/salida: %d/%d"
              % (cliente.llamadas, cliente.tokens_entrada, cliente.tokens_salida))
    return 0


if __name__ == "__main__":
    sys.exit(main())
