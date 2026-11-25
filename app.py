"""App: ¿Amerita inspección este reporte de accidente?

Uso:  python app.py   ->  abre http://127.0.0.1:7860
Pega la narrativa de un reporte de accidente grave (en inglés) y presiona "Evaluar".
"""
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent / "src"))
from modelo import UMBRAL, decidir  # noqa: E402

EJEMPLOS = [
    "An employee was cleaning the rollers of a printing press while it was still running. "
    "The machine guard had been removed. His right hand was caught between the rollers and he "
    "lost two fingers. He was taken to the hospital and admitted.",
    "An employee slipped on a wet floor in the break room and fell, fracturing her wrist. "
    "She was treated at the hospital and admitted overnight for surgery.",
    "A worker was transferring sulfuric acid from a drum to a tank when the hose ruptured. "
    "Acid splashed on his face and arms causing chemical burns. He was hospitalized.",
    "El trabajador se cayó de una escalera y se fracturó la pierna.",
    "",
]

CSS = """
.veredicto {font-size: 1.6rem; font-weight: 700; padding: 14px 18px; border-radius: 10px; text-align:center}
.si  {background:#fde2e1; color:#9b1c1c}
.no  {background:#def7ec; color:#03543f}
.rej {background:#fdf6b2; color:#723b13}
"""


def evaluar(texto):
    try:
        r = decidir(texto)
    except Exception as e:  # la app nunca se cae: cualquier error se muestra como rechazo
        r = {"estado": "rechazado", "clase": None, "probabilidad": None, "umbral": UMBRAL,
             "motivo": f"Error inesperado al procesar la entrada ({type(e).__name__}).", "ms": 0}

    if r["estado"] != "ok":
        html = '<div class="veredicto rej">⚠️ ENTRADA RECHAZADA</div>'
        detalle = (f"**Motivo:** {r['motivo']}\n\n"
                   f"La aplicación no decide sobre esta entrada. Un analista humano debe revisarla.\n\n"
                   f"Umbral vigente: **{r['umbral']:.2f}** · tiempo: {r.get('ms', 0):.0f} ms")
        return html, None, detalle

    p, u = r["probabilidad"], r["umbral"]
    if r["clase"] == "INSPECCIONAR":
        html = '<div class="veredicto si">🔎 INSPECCIONAR</div>'
    else:
        html = '<div class="veredicto no">✅ NO INSPECCIONAR (investigación por escrito)</div>'
    detalle = (f"**Probabilidad de inspección:** {p:.1%}\n\n"
               f"**Umbral aplicado:** {u:.2f} — se inspecciona si la probabilidad ≥ {u:.0%}\n\n"
               f"El umbral minimiza el costo esperado con un falso negativo 5 veces más caro "
               f"que un falso positivo.\n\n"
               f"Palabras conocidas por el modelo: {r['cobertura']:.0%} · tiempo: {r['ms']:.0f} ms")
    return html, {"Inspeccionar": p, "No inspeccionar": 1 - p}, detalle


with gr.Blocks(title="Triage de reportes OSHA") as app:
    gr.Markdown(
        "# ¿Amerita inspección este reporte?\n"
        "Pega la narrativa de un reporte de accidente laboral grave **(en inglés)**. "
        "El modelo estima la probabilidad de que el caso amerite una inspección en sitio "
        "y la compara con el umbral elegido por costo."
    )
    with gr.Row():
        with gr.Column(scale=3):
            entrada = gr.Textbox(label="Narrativa del reporte", lines=8,
                                 placeholder="An employee was operating a ... when ...")
            with gr.Row():
                boton = gr.Button("Evaluar", variant="primary")
                gr.ClearButton(entrada, value="Limpiar")
        with gr.Column(scale=2):
            veredicto = gr.HTML()
            barras = gr.Label(label="Probabilidad", num_top_classes=2)
            detalle = gr.Markdown()
    gr.Examples(EJEMPLOS, inputs=entrada, label="Ejemplos (escritos a mano, no vienen del dataset)")
    gr.Markdown(
        "<small>Modelo: TF-IDF + red densa entrenada con reportes OSHA 2015–2022, calibrada con Platt. "
        "No usar para reportes en otro idioma, accidentes fuera de EE. UU. o casos con muertes "
        "(no están en los datos de entrenamiento).</small>"
    )
    boton.click(evaluar, entrada, [veredicto, barras, detalle])
    entrada.submit(evaluar, entrada, [veredicto, barras, detalle])

if __name__ == "__main__":
    import os
    # En Render el puerto llega en la variable PORT y hay que escuchar en 0.0.0.0
    app.launch(server_name="0.0.0.0", server_port=int(os.environ.get("PORT", 7860)), css=CSS)
