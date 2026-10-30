import re
import unittest
from pathlib import Path
from arnes import pipeline

RAIZ = Path(__file__).resolve().parent.parent


class TestArnes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cfg = pipeline.cargar_json(RAIZ / "config/sector.json")
        sols = pipeline.cargar_json(RAIZ / "data/solicitudes.json")
        cls.leads = {l["id"]: l for l in pipeline.procesar(sols, cfg)}

    def test_completa_queda_lista(self):
        self.assertEqual(self.leads["S01"]["estado"], "listo_para_validar")
        self.assertEqual(self.leads["S01"]["datos"]["metros"], 300)

    def test_incompleta_detecta_faltantes(self):  # caso incompleto 1
        l = self.leads["S03"]
        self.assertEqual(l["estado"], "faltan_datos")
        for campo in ("nombre", "empresa", "ubicacion", "metros", "frecuencia"):
            self.assertIn(campo, l["faltantes"])
        self.assertEqual(len(l["preguntas"]), len(l["faltantes"]))

    def test_sin_contacto(self):  # caso incompleto 2
        self.assertIn("contacto", self.leads["S06"]["faltantes"])

    def test_vaga_sin_clasificar(self):  # caso incompleto 3
        l = self.leads["S08"]
        self.assertEqual(l["categoria"], "sin_clasificar")
        self.assertIn("servicio", l["faltantes"])

    def test_fuera_de_alcance_y_duplicado(self):
        self.assertEqual(self.leads["S05"]["estado"], "fuera_de_alcance")
        self.assertEqual(self.leads["S07"]["estado"], "duplicado")
        self.assertEqual(self.leads["S07"]["duplicado_de"], "S01")
        self.assertEqual(self.leads["S07"]["faltantes"], [])  # no pide datos de nuevo
        self.assertEqual(self.leads["S05"]["faltantes"], [])

    def test_nunca_cotiza_ni_envia(self):
        for l in self.leads.values():
            self.assertFalse(l["enviado"])
            self.assertIsNone(re.search(r"\$|\bMXN\b|\bpesos\b", l["borrador_respuesta"]))
        self.assertIn("no compartimos precios", self.leads["S01"]["borrador_respuesta"])

    def test_parcial_fuera_de_alcance(self):
        self.assertTrue(self.leads["S10"]["notas"])


if __name__ == "__main__":
    unittest.main()
