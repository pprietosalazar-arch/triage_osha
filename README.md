---
title: Triage de reportes OSHA
emoji: 🔎
colorFrom: yellow
colorTo: red
sdk: gradio
sdk_version: 6.32.0
python_version: "3.12"
app_file: app.py
pinned: false
---

# Vigía — triage de reportes de accidentes laborales

¿Este reporte amerita una inspección en sitio?

Pega la narrativa de un reporte de accidente laboral grave (en inglés). La app devuelve:

- **Clase:** INSPECCIONAR / NO INSPECCIONAR, o ENTRADA RECHAZADA si el texto no parece un reporte.
- **Probabilidad** calibrada de que el caso amerite inspección.
- **Umbral aplicado (0.17)**, elegido para minimizar el costo esperado con un falso negativo 5 veces más caro que un falso positivo.

Modelo: TF-IDF + red densa (64 neuronas), entrenada desde cero con OSHA Severe Injury Reports 2015–2022, calibrada con Platt. No usa ningún modelo de lenguaje preentrenado.

**No usar** para reportes en otro idioma, accidentes fuera de EE. UU., casos con muertes o casi-accidentes sin lesión.
