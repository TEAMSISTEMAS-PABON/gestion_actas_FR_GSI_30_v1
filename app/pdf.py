from pathlib import Path
import base64
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.units import mm


def signature_image(data, filename):
    if not data:
        return None
    try:
        raw = base64.b64decode(data.split(",", 1)[1])
        path = Path(filename)
        path.write_bytes(raw)
        return Image(str(path), width=55*mm, height=22*mm)
    except Exception:
        return None


def create_acta_pdf(data, output_path):
    output_path = Path(output_path)
    sig_dir = output_path.parent / "firmas"
    sig_dir.mkdir(exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title2", parent=styles["Title"], fontSize=14, leading=17, alignment=TA_CENTER)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=7.5, leading=9)
    normal = ParagraphStyle("Normal2", parent=styles["BodyText"], fontSize=8.5, leading=10)

    story = []
    story.append(Paragraph("GESTIÓN DE SISTEMAS DE INFORMACIÓN", title))
    story.append(Paragraph("ACTA DE ENTREGA DE EQUIPOS DE COMPUTO", title))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(f"<b>Código:</b> FR-GSI-30 &nbsp;&nbsp; <b>Versión:</b> 01 &nbsp;&nbsp; <b>Acta:</b> {data['consecutivo']}", small))
    story.append(Paragraph(f"<b>Fecha:</b> {data['fecha']}", small))
    story.append(Spacer(1, 4*mm))

    def section(title_text, rows):
        story.append(Paragraph(f"<b>{title_text}</b>", normal))
        table = Table(rows, colWidths=[42*mm, 49*mm, 42*mm, 49*mm])
        table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 7.5),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("TOPPADDING", (0,0), (-1,-1), 3),
        ]))
        story.append(table)
        story.append(Spacer(1, 3*mm))

    section("DATOS DEL TRABAJADOR", [
        ["Nombre", data["nombre_recibe"], "Cargo", data["cargo"]],
        ["Área / Servicio", data["area_servicio"], "Ubicación", data["ubicacion"]],
        ["Usuario de red / IP", data["ip_usuario"], "Fecha", data["fecha"]],
    ])

    section("HARDWARE", [
        ["Tipo", data["tipo"], "Marca", data["marca"]],
        ["Modelo", data["modelo"], "Serial", data["serial"]],
        ["Código / Activo fijo", data["codigo_activo"], "Procesador", data["procesador"]],
        ["Memoria RAM (GB)", data["ram"], "Disco duro (GB)", data["disco_gb"]],
        ["Tipo disco", data["tipo_disco"], "Monitor", data["monitor"]],
        ["Teclado", data["teclado"], "Mouse", data["mouse"]],
        ["Cargador", data["cargador"], "Copia de seguridad", data["copia_seguridad"]],
    ])

    section("SOFTWARE", [
        ["Software estándar corporativo", data["software_estandar"], "Software especial", data["software_especial"]],
        ["Otros software solicitado", data["otros_software"], "", ""],
    ])

    story.append(Paragraph("<b>OBSERVACIONES</b>", normal))
    obs = Table([[data["observaciones"] or ""]], colWidths=[182*mm], rowHeights=[18*mm])
    obs.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.black),("VALIGN",(0,0),(-1,-1),"TOP"),("FONTSIZE",(0,0),(-1,-1),8)]))
    story.append(obs)
    story.append(Spacer(1, 4*mm))

    texto = ("Certifico que los elementos detallados en el presente documento, me han sido entregados "
             "para mi cuidado y custodia con el propósito de cumplir con las tareas y asignaciones propias "
             "de mi cargo en la empresa, siendo estos de mi única y exclusiva responsabilidad. Me comprometo "
             "a usar correctamente los recursos y solo para los fines establecidos, y a no instalar ni permitir "
             "la instalación de software por personal ajeno al grupo interno de trabajo de soporte de sistemas "
             "de información. Con la firma de este documento el usuario final se responsabiliza por cualquier "
             "daño físico o lógico que se pudiera generar por un uso incorrecto.")
    story.append(Paragraph(texto, small))
    story.append(Spacer(1, 5*mm))

    rec = signature_image(data["firma_recibe"], sig_dir / f"{data['consecutivo']}_recibe.png")
    ent = signature_image(data["firma_entrega"], sig_dir / f"{data['consecutivo']}_entrega.png")
    rec_cell = [rec] if rec else ["Firma"]
    ent_cell = [ent] if ent else ["Firma"]

    table = Table([
        ["RECIBE", "ENTREGA"],
        [f"Nombre: {data['nombre_recibe']}", f"Nombre: {data['nombre_entrega']}"],
        [rec_cell, ent_cell],
    ], colWidths=[91*mm, 91*mm], rowHeights=[7*mm, 7*mm, 25*mm])
    table.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
    ]))
    story.append(table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("Fecha del formato: 17/05/2024 &nbsp;&nbsp; Página: 1 de 1", small))

    doc.build(story)
