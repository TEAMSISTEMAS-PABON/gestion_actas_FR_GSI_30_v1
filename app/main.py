from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from datetime import datetime
import sqlite3
import base64
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

from .pdf import create_acta_pdf

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdf"
DATA_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env")

DB = DATA_DIR / "actas.db"

app = FastAPI(title="Gestión de Actas FR-GSI-30")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS actas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        consecutivo TEXT UNIQUE,
        fecha TEXT,
        nombre_recibe TEXT,
        cargo TEXT,
        ubicacion TEXT,
        area_servicio TEXT,
        tipo TEXT,
        marca TEXT,
        modelo TEXT,
        serial TEXT,
        codigo_activo TEXT,
        procesador TEXT,
        ram TEXT,
        disco_gb TEXT,
        tipo_disco TEXT,
        monitor TEXT,
        teclado TEXT,
        mouse TEXT,
        cargador TEXT,
        ip_usuario TEXT,
        software_estandar TEXT,
        software_especial TEXT,
        otros_software TEXT,
        copia_seguridad TEXT,
        observaciones TEXT,
        nombre_entrega TEXT,
        firma_recibe TEXT,
        firma_entrega TEXT,
        correo TEXT,
        pdf_path TEXT,
        created_at TEXT
    )
    """)
    conn.commit()
    conn.close()


init_db()


def next_consecutivo():
    conn = db()
    row = conn.execute("SELECT id FROM actas ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    n = (row["id"] if row else 0) + 1
    return f"AE-{datetime.now().year}-{n:06d}"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    html = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


@app.post("/api/actas")
async def crear_acta(request: Request):
    form = await request.form()

    consecutivo = next_consecutivo()
    fecha = form.get("fecha") or datetime.now().strftime("%Y-%m-%d")
    firma_recibe = form.get("firma_recibe", "")
    firma_entrega = form.get("firma_entrega", "")

    def clean_signature(value):
        if not value or not value.startswith("data:image"):
            return ""
        return value

    data = {
        "consecutivo": consecutivo,
        "fecha": fecha,
        "nombre_recibe": form.get("nombre_recibe", ""),
        "cargo": form.get("cargo", ""),
        "ubicacion": form.get("ubicacion", ""),
        "area_servicio": form.get("area_servicio", ""),
        "tipo": form.get("tipo", ""),
        "marca": form.get("marca", ""),
        "modelo": form.get("modelo", ""),
        "serial": form.get("serial", ""),
        "codigo_activo": form.get("codigo_activo", ""),
        "procesador": form.get("procesador", ""),
        "ram": form.get("ram", ""),
        "disco_gb": form.get("disco_gb", ""),
        "tipo_disco": form.get("tipo_disco", ""),
        "monitor": form.get("monitor", ""),
        "teclado": form.get("teclado", ""),
        "mouse": form.get("mouse", ""),
        "cargador": form.get("cargador", ""),
        "ip_usuario": form.get("ip_usuario", ""),
        "software_estandar": form.get("software_estandar", ""),
        "software_especial": form.get("software_especial", ""),
        "otros_software": form.get("otros_software", ""),
        "copia_seguridad": form.get("copia_seguridad", ""),
        "observaciones": form.get("observaciones", ""),
        "nombre_entrega": form.get("nombre_entrega", ""),
        "firma_recibe": clean_signature(firma_recibe),
        "firma_entrega": clean_signature(firma_entrega),
        "correo": form.get("correo", ""),
    }

    pdf_path = PDF_DIR / f"{consecutivo}.pdf"
    create_acta_pdf(data, pdf_path)

    conn = db()
    conn.execute("""
    INSERT INTO actas (
        consecutivo,fecha,nombre_recibe,cargo,ubicacion,area_servicio,tipo,marca,modelo,
        serial,codigo_activo,procesador,ram,disco_gb,tipo_disco,monitor,teclado,mouse,
        cargador,ip_usuario,software_estandar,software_especial,otros_software,
        copia_seguridad,observaciones,nombre_entrega,firma_recibe,firma_entrega,
        correo,pdf_path,created_at
    ) VALUES (
        :consecutivo,:fecha,:nombre_recibe,:cargo,:ubicacion,:area_servicio,:tipo,:marca,:modelo,
        :serial,:codigo_activo,:procesador,:ram,:disco_gb,:tipo_disco,:monitor,:teclado,:mouse,
        :cargador,:ip_usuario,:software_estandar,:software_especial,:otros_software,
        :copia_seguridad,:observaciones,:nombre_entrega,:firma_recibe,:firma_entrega,
        :correo,:pdf_path,:created_at
    )
    """, {**data, "pdf_path": str(pdf_path), "created_at": datetime.now().isoformat(timespec="seconds")})
    conn.commit()
    conn.close()

    # Envío opcional por SMTP.
    if form.get("enviar_correo") == "1" and data["correo"]:
        try:
            send_email(data["correo"], consecutivo, pdf_path)
            email_status = "Correo enviado correctamente."
        except Exception as exc:
            email_status = f"No se pudo enviar el correo: {exc}"
    else:
        email_status = "PDF generado."

    return {
        "ok": True,
        "consecutivo": consecutivo,
        "pdf": f"/api/actas/{consecutivo}/pdf",
        "email_status": email_status
    }


def send_email(to_email: str, consecutivo: str, pdf_path: Path):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or user
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not host or not sender:
        raise RuntimeError("SMTP no configurado. Revise el archivo .env")

    msg = EmailMessage()
    msg["Subject"] = f"Acta de entrega de equipo de cómputo - {consecutivo}"
    msg["From"] = sender
    msg["To"] = to_email
    msg.set_content(f"Se adjunta el acta de entrega {consecutivo}.")
    msg.add_attachment(pdf_path.read_bytes(), maintype="application", subtype="pdf",
                       filename=pdf_path.name)

    with smtplib.SMTP(host, port, timeout=20) as server:
        if use_tls:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(msg)


@app.get("/api/actas/{consecutivo}/pdf")
def descargar_pdf(consecutivo: str):
    conn = db()
    row = conn.execute("SELECT pdf_path FROM actas WHERE consecutivo=?", (consecutivo,)).fetchone()
    conn.close()
    if not row or not Path(row["pdf_path"]).exists():
        return HTMLResponse("PDF no encontrado", status_code=404)
    return FileResponse(row["pdf_path"], media_type="application/pdf",
                        filename=f"{consecutivo}.pdf")


@app.get("/api/actas")
def listar_actas():
    conn = db()
    rows = conn.execute("""
        SELECT consecutivo, fecha, nombre_recibe, cargo, codigo_activo, serial
        FROM actas ORDER BY id DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
