"""Vigía — triage de reportes de accidentes laborales.

Uso local:  python app.py   ->  http://127.0.0.1:7860
En Render:  el puerto llega en la variable PORT y se escucha en 0.0.0.0.
"""
import os
import sys
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent / "src"))
from modelo import UMBRAL, decidir  # noqa: E402

# ---------------------------------------------------------------- ejemplos
EJEMPLOS = [
    ("⚙️", "Prensa sin guarda",
     "An employee was cleaning the rollers of a printing press while it was still running. "
     "The machine guard had been removed. His right hand was caught between the rollers and he "
     "lost two fingers. He was taken to the hospital and admitted."),
    ("💧", "Resbalón en el comedor",
     "An employee slipped on a wet floor in the break room and fell, fracturing her wrist. "
     "She was treated at the hospital and admitted overnight for surgery."),
    ("🧪", "Fuga de ácido sulfúrico",
     "A worker was transferring sulfuric acid from a drum to a tank when the hose ruptured. "
     "Acid splashed on his face and arms causing chemical burns. He was hospitalized."),
    ("🌐", "Reporte en español",
     "El trabajador se cayó de una escalera y se fracturó la pierna."),
    ("🚫", "Texto vacío", ""),
]

# ---------------------------------------------------------------- estilo
LOGO = """
<svg viewBox="0 0 64 64" width="58" height="58" aria-hidden="true">
  <defs>
    <linearGradient id="vg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#60a5fa"/><stop offset="1" stop-color="#1d4ed8"/>
    </linearGradient>
  </defs>
  <path d="M32 4 L54 12 V30 C54 44 44 54 32 60 C20 54 10 44 10 30 V12 Z" fill="url(#vg)"/>
  <circle cx="29" cy="29" r="10" fill="none" stroke="#ffffff" stroke-width="4"/>
  <line x1="36.5" y1="36.5" x2="45" y2="45" stroke="#f97316" stroke-width="5" stroke-linecap="round"/>
</svg>
"""

ENCABEZADO = f"""
<div class="vg-header">
  {LOGO}
  <div>
    <div class="vg-nombre">Vig<span>ía</span></div>
    <div class="vg-sub">Triage inteligente de reportes de accidentes laborales</div>
  </div>
</div>
<div class="vg-pregunta">¿Este reporte amerita una inspección en sitio?</div>
<div class="vg-instr">Pega la narrativa de un accidente laboral grave <b>en inglés</b>. Vigía estima la
probabilidad de que el caso amerite inspección y la compara con el umbral elegido por costo.</div>
"""

CSS = """
:root, .dark {
  --vg-bg: #0b1220; --vg-card: #111a2e; --vg-borde: #1f2d4a;
  --vg-azul: #3b82f6; --vg-azul-claro: #60a5fa; --vg-naranja: #f97316; --vg-naranja-claro: #fb923c;
  --vg-texto: #e5e7eb; --vg-tenue: #94a3b8;
}
body, gradio-app, .gradio-container { background: var(--vg-bg) !important; }
.gradio-container { max-width: 1180px !important; margin: 0 auto !important; }
footer { display: none !important; }

.vg-header { display: flex; align-items: center; gap: 16px; margin: 8px 0 18px; }
.vg-nombre { font-size: 2.6rem !important; font-weight: 800; letter-spacing: -0.02em; line-height: 1;
  color: var(--vg-azul-claro) !important; }
.vg-nombre span { color: var(--vg-naranja) !important; }
.vg-sub { color: var(--vg-tenue); font-size: 0.95rem; margin-top: 4px; }
.vg-pregunta { color: var(--vg-texto); font-size: 1.35rem; font-weight: 700; margin-bottom: 4px; }
.vg-instr { color: var(--vg-tenue); font-size: 0.92rem; margin-bottom: 6px; }

.vg-card { background: var(--vg-card) !important; border: 1px solid var(--vg-borde) !important;
  border-radius: 14px !important; padding: 14px !important; }
.vg-lado-titulo { color: var(--vg-texto); font-weight: 700; margin: 2px 0 8px; }
.vg-ejemplo { justify-content: flex-start !important; text-align: left !important;
  background: #0f172a !important; border: 1px solid var(--vg-borde) !important; color: var(--vg-texto) !important; }
.vg-ejemplo:hover { border-color: var(--vg-azul) !important; }
.vg-nota { color: var(--vg-tenue); font-size: 0.8rem; line-height: 1.45; }

.vg-res { border-radius: 14px; padding: 18px; border: 1px solid var(--vg-borde); background: var(--vg-card); }
.vg-vacio { color: var(--vg-tenue); text-align: center; padding: 28px 10px; }
.vg-veredicto { font-size: 1.5rem; font-weight: 800; padding: 12px 16px; border-radius: 10px; text-align: center; }
.vg-si  { background: rgba(249,115,22,.15); color: var(--vg-naranja-claro); border: 1px solid rgba(249,115,22,.45); }
.vg-no  { background: rgba(59,130,246,.15); color: var(--vg-azul-claro); border: 1px solid rgba(59,130,246,.45); }
.vg-rej { background: rgba(148,163,184,.12); color: #cbd5e1; border: 1px dashed #64748b; }

.vg-gauge { position: relative; height: 16px; border-radius: 999px; background: #1e293b; margin: 26px 0 8px; }
.vg-fill { position: absolute; inset: 0 auto 0 0; border-radius: 999px;
  background: linear-gradient(90deg, var(--vg-azul), var(--vg-naranja)); }
.vg-thr { position: absolute; top: -8px; bottom: -8px; width: 3px; background: #fff; border-radius: 2px; }
.vg-thr span { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); white-space: nowrap;
  font-size: 0.72rem; color: #fff; }
.vg-nums { display: flex; justify-content: space-between; color: var(--vg-tenue); font-size: 0.85rem; }
.vg-nums b { color: var(--vg-texto); font-size: 1.15rem; }
.vg-det { color: var(--vg-tenue); font-size: 0.85rem; margin-top: 12px; line-height: 1.5; }
.vg-det b { color: var(--vg-texto); }
"""

# Fuerza modo oscuro aunque el navegador esté en modo claro
JS = """
() => {
  const url = new URL(window.location);
  if (url.searchParams.get('__theme') !== 'dark') {
    url.searchParams.set('__theme', 'dark');
    window.location.replace(url.href);
  }
}
"""

TEMA = gr.themes.Base(
    primary_hue=gr.themes.colors.orange,
    secondary_hue=gr.themes.colors.blue,
    neutral_hue=gr.themes.colors.slate,
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"],
)

RESULTADO_INICIAL = ('<div class="vg-res"><div class="vg-vacio">🔎 Pega un reporte o elige un ejemplo '
                     'y presiona <b>Evaluar</b>.</div></div>')


# ---------------------------------------------------------------- lógica de la vista
def evaluar(texto):
    try:
        r = decidir(texto)
    except Exception as e:  # la app nunca se cae: cualquier error se muestra como rechazo
        r = {"estado": "rechazado", "probabilidad": None, "umbral": UMBRAL, "ms": 0,
             "motivo": f"Error inesperado al procesar la entrada ({type(e).__name__})."}

    u = r["umbral"]
    if r["estado"] != "ok":
        return (f'<div class="vg-res"><div class="vg-veredicto vg-rej">⚠️ ENTRADA RECHAZADA</div>'
                f'<div class="vg-det"><b>Motivo:</b> {r["motivo"]}<br>'
                f'Vigía no decide sobre esta entrada: debe revisarla una persona.<br>'
                f'Umbral vigente: <b>{u:.2f}</b> · tiempo: {r.get("ms", 0):.0f} ms</div></div>')

    p = r["probabilidad"]
    if r["clase"] == "INSPECCIONAR":
        ver = '<div class="vg-veredicto vg-si">🔎 INSPECCIONAR</div>'
    else:
        ver = '<div class="vg-veredicto vg-no">✅ NO INSPECCIONAR <span style="font-weight:500;font-size:.9rem">(investigación por escrito)</span></div>'
    return (f'<div class="vg-res">{ver}'
            f'<div class="vg-gauge"><div class="vg-fill" style="width:{p*100:.1f}%"></div>'
            f'<div class="vg-thr" style="left:calc({u*100:.1f}% - 1px)"><span>umbral {u:.2f}</span></div></div>'
            f'<div class="vg-nums"><span>Probabilidad de inspección: <b>{p:.1%}</b></span>'
            f'<span>Umbral: <b>{u:.0%}</b></span></div>'
            f'<div class="vg-det">Se inspecciona si la probabilidad ≥ umbral. El umbral minimiza el costo '
            f'esperado suponiendo que dejar pasar un caso grave cuesta <b>5 veces</b> más que una inspección '
            f'innecesaria.<br>Palabras conocidas por el modelo: {r["cobertura"]:.0%} · tiempo: {r["ms"]:.0f} ms</div></div>')


# ---------------------------------------------------------------- interfaz
with gr.Blocks(title="Vigía · Triage de reportes") as app:
    gr.HTML(ENCABEZADO)
    with gr.Row(equal_height=False):
        with gr.Column(scale=3):
            entrada = gr.Textbox(label="Narrativa del reporte (inglés)", lines=7,
                                 placeholder="An employee was operating a ... when ...")
            with gr.Row():
                boton = gr.Button("Evaluar", variant="primary", scale=2)
                limpiar = gr.Button("Limpiar", variant="secondary", scale=1)
            salida = gr.HTML(RESULTADO_INICIAL)
        with gr.Column(scale=1, min_width=240, elem_classes="vg-card"):
            gr.HTML('<div class="vg-lado-titulo">Casos de ejemplo</div>')
            for icono, titulo, texto in EJEMPLOS:
                b = gr.Button(f"{icono}  {titulo}", size="sm", elem_classes="vg-ejemplo")
                b.click(lambda t=texto: t, None, entrada)
            gr.HTML(
                '<div class="vg-nota" style="margin-top:10px"><b>Cuándo no usar Vigía:</b> reportes en otro '
                'idioma, accidentes fuera de EE. UU., casos con muertes o casi-accidentes sin lesión.<br><br>'
                'Modelo: TF-IDF + red densa entrenada desde cero con reportes OSHA 2015–2022, '
                'calibrada con Platt.</div>'
            )

    boton.click(evaluar, entrada, salida)
    entrada.submit(evaluar, entrada, salida)
    limpiar.click(lambda: ("", RESULTADO_INICIAL), None, [entrada, salida])

if __name__ == "__main__":
    en_render = "PORT" in os.environ
    app.launch(
        server_name="0.0.0.0" if en_render else "127.0.0.1",
        server_port=int(os.environ.get("PORT", 7860)),
        theme=TEMA, css=CSS, js=JS,
    )
