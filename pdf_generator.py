"""
Generador de PDF para reportes técnicos.
Usa fpdf2 — sin dependencias de LaTeX ni binarios externos.
"""

import os
import tempfile
from fpdf import FPDF


LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo.png")

# ── Paleta ──────────────────────────────────────────────────────────────────
AZUL_OSCURO = (15, 40, 80)
AZUL_MEDIO = (30, 90, 160)
GRIS_CLARO = (245, 247, 250)
GRIS_LINEA = (210, 215, 225)
TEXTO_DARK = (25, 25, 35)
BLANCO = (255, 255, 255)
NARANJA = (230, 95, 30)


class ReportePDF(FPDF):
    def __init__(self, nombre_empresa: str = "Servicio Técnico"):
        super().__init__()
        self.nombre_empresa = nombre_empresa
        self.set_margins(14, 14, 14)
        self.set_auto_page_break(auto=True, margin=20)

    # ── Header ───────────────────────────────────────────────────────────────
    def header(self):
        # Franja azul superior
        self.set_fill_color(*AZUL_OSCURO)
        self.rect(0, 0, 210, 22, "F")

        # Logo (si existe)
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=8, y=3, h=16)
            self.set_x(55)
        else:
            self.set_x(8)

        # Nombre empresa
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(*BLANCO)
        self.set_y(6)
        self.cell(0, 8, self.nombre_empresa.upper(), ln=False)

        # Etiqueta "REPORTE TÉCNICO"
        self.set_font("Helvetica", "", 8)
        self.set_text_color(180, 200, 230)
        self.set_xy(8, 14)
        self.cell(0, 5, "REPORTE TÉCNICO DE SERVICIO")

        self.ln(14)

    # ── Footer ───────────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*GRIS_LINEA)
        self.line(14, self.get_y(), 196, self.get_y())
        self.ln(1)
        self.set_font("Helvetica", "", 7.5)
        self.set_text_color(140, 145, 155)
        self.cell(0, 5, f"Página {self.page_no()}", align="C")

    # ── Sección ──────────────────────────────────────────────────────────────
    def seccion_titulo(self, titulo: str):
        self.ln(3)
        self.set_fill_color(*AZUL_MEDIO)
        self.set_text_color(*BLANCO)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, f"  {titulo.upper()}", ln=True, fill=True)
        self.ln(2)
        self.set_text_color(*TEXTO_DARK)

    def fila_dato(self, etiqueta: str, valor: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*AZUL_MEDIO)
        self.cell(38, 6.5, etiqueta + ":", ln=False)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXTO_DARK)
        self.cell(0, 6.5, valor, ln=True)


# ── Función principal ─────────────────────────────────────────────────────────
def generar_pdf(data: dict) -> str:
    """
    data = {
        nombre, telefono, direccion, descripcion,
        fotos: [path, ...], fecha
    }
    Retorna la ruta al PDF temporal generado.
    """
    nombre_empresa = os.environ.get("NOMBRE_EMPRESA", "Servicio Técnico")
    pdf = ReportePDF(nombre_empresa=nombre_empresa)
    pdf.add_page()

    # ── Número y fecha del reporte ────────────────────────────────────────
    import datetime, hashlib
    folio = hashlib.md5(
        (data["nombre"] + data["fecha"]).encode()
    ).hexdigest()[:6].upper()

    pdf.set_fill_color(*GRIS_CLARO)
    pdf.set_draw_color(*GRIS_LINEA)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(90, 95, 110)
    pdf.cell(0, 6, f"  Folio: {folio}   |   Fecha: {data['fecha']}", ln=True, fill=True, border="B")
    pdf.ln(4)

    # ── Datos del cliente ────────────────────────────────────────────────
    pdf.seccion_titulo("Datos del Cliente")
    pdf.fila_dato("Cliente", data["nombre"])
    pdf.fila_dato("Teléfono", data["telefono"])
    pdf.fila_dato("Dirección", data["direccion"])

    # ── Descripción del trabajo ──────────────────────────────────────────
    pdf.ln(2)
    pdf.seccion_titulo("Trabajo Realizado")
    pdf.set_font("Helvetica", "", 9.5)
    pdf.set_text_color(*TEXTO_DARK)
    pdf.set_fill_color(*GRIS_CLARO)
    pdf.multi_cell(
        0,
        6,
        data.get("descripcion", "Sin descripción."),
        fill=True,
        border=0,
    )

    # ── Fotos ─────────────────────────────────────────────────────────────
    fotos = data.get("fotos", [])
    if fotos:
        pdf.ln(2)
        pdf.seccion_titulo(f"Registro Fotográfico  ({len(fotos)} foto{'s' if len(fotos) != 1 else ''})")

        cols = 2
        img_w = 84
        img_h = 60
        gap_x = 6
        start_x = 14

        for i, foto_path in enumerate(fotos):
            col = i % cols
            if col == 0:
                # Chequear espacio
                if pdf.get_y() + img_h + 16 > 277:
                    pdf.add_page()
                row_y = pdf.get_y()

            x = start_x + col * (img_w + gap_x)

            # Sombra / borde
            pdf.set_fill_color(*GRIS_LINEA)
            pdf.rect(x, row_y, img_w, img_h, "F")

            # Imagen
            try:
                pdf.image(foto_path, x=x, y=row_y, w=img_w, h=img_h)
            except Exception:
                pass

            # Etiqueta
            pdf.set_xy(x, row_y + img_h + 0.5)
            pdf.set_font("Helvetica", "I", 7.5)
            pdf.set_text_color(100, 110, 125)
            pdf.cell(img_w, 4, f"Foto {i + 1}", align="C")

            # Avanzar fila
            if col == cols - 1 or i == len(fotos) - 1:
                pdf.set_y(row_y + img_h + 7)

    # ── Firma / cierre ────────────────────────────────────────────────────
    pdf.ln(6)
    pdf.set_draw_color(*GRIS_LINEA)
    pdf.line(14, pdf.get_y(), 100, pdf.get_y())
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(130, 135, 145)
    pdf.cell(0, 4, "Firma del técnico", ln=True)

    # ── Guardar ───────────────────────────────────────────────────────────
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf.output(tmp.name)
    return tmp.name
