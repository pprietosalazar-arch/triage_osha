"""Lógica de decisión compartida por la app y los scripts de evaluación.

decidir(texto) -> dict con:
  estado        "ok" | "rechazado"
  clase         "INSPECCIONAR" | "NO INSPECCIONAR" | None
  probabilidad  probabilidad calibrada (Platt) de que OSHA abra inspección
  umbral        umbral elegido por costo (FN=5, FP=1)
  motivo        explicación corta
"""
from pathlib import Path
import time

import joblib
import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
_mlp = joblib.load(RAIZ / "modelos" / "mlp.joblib")
_dec = joblib.load(RAIZ / "modelos" / "decision.joblib")
_vec = _mlp.named_steps["tfidf"]
_analizador = _vec.build_analyzer()
_vocab = _vec.vocabulary_
_ood = joblib.load(RAIZ / "modelos" / "ood.joblib") if (RAIZ / "modelos" / "ood.joblib").exists() else {}

UMBRAL = float(_dec["umbral"])
MIN_CARACTERES = 20
MAX_CARACTERES = 5000
MIN_PALABRAS = 5


def cobertura(texto: str) -> tuple[float, int]:
    """Fracción de palabras del texto que el modelo conoce (vocabulario de entrenamiento)."""
    palabras = [t for t in _analizador(texto) if " " not in t]
    if not palabras:
        return 0.0, 0
    return float(np.mean([p in _vocab for p in palabras])), len(palabras)


def _calibrar(p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    z = np.log(p / (1 - p)).reshape(-1, 1)
    return _dec["calibrador_platt"].predict_proba(z)[:, 1]


def probabilidad(textos) -> np.ndarray:
    return _calibrar(_mlp.predict_proba(list(textos))[:, 1])


def decidir(texto) -> dict:
    t0 = time.perf_counter()
    base = {"estado": "rechazado", "clase": None, "probabilidad": None, "umbral": UMBRAL}
    texto = "" if texto is None else str(texto).strip()
    if len(texto) > MAX_CARACTERES:
        texto = texto[:MAX_CARACTERES]

    if len(texto) < MIN_CARACTERES:
        return base | {"motivo": "Texto vacío o demasiado corto para ser un reporte.", "ms": _ms(t0)}

    cob, n = cobertura(texto)
    if n < MIN_PALABRAS:
        return base | {"motivo": "El texto casi no tiene palabras.", "cobertura": cob, "ms": _ms(t0)}
    min_cob = _ood.get("min_cobertura", 0.0)
    if cob < min_cob:
        return base | {"motivo": f"Sólo {cob:.0%} de las palabras son conocidas (mínimo {min_cob:.0%}). "
                                 "No parece un reporte de accidente laboral en inglés.",
                       "cobertura": cob, "ms": _ms(t0)}

    p = float(probabilidad([texto])[0])
    clase = "INSPECCIONAR" if p >= UMBRAL else "NO INSPECCIONAR"
    return {"estado": "ok", "clase": clase, "probabilidad": p, "umbral": UMBRAL,
            "motivo": "Probabilidad mayor o igual al umbral." if p >= UMBRAL else "Probabilidad menor al umbral.",
            "cobertura": cob, "ms": _ms(t0)}


def _ms(t0):
    return (time.perf_counter() - t0) * 1000
