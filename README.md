# Gestión de Actas de Entrega - FR-GSI-30

Aplicación web local para diligenciar el Acta de Entrega de Equipos de Cómputo,
guardar el registro, generar PDF y dejar preparada la configuración de correo.

## Arquitectura inicial
- Backend: Python + FastAPI
- Base de datos: SQLite
- Frontend: HTML + CSS + JavaScript responsive para tablet
- PDF: ReportLab
- Firma: canvas táctil
- Acceso LAN: http://IP_DEL_SERVIDOR:8000

## 1. Requisitos
Python 3.11 o superior recomendado.

## 2. Instalación

Windows:
```bat
cd gestion_actas
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux:
```bash
cd gestion_actas
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Ejecutar
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

En el servidor:
http://127.0.0.1:8000

Desde otra PC/tablet de la misma red:
http://IP_DEL_SERVIDOR:8000

## 4. Windows Firewall
Si el servidor es Windows Server, permitir el puerto TCP 8000:
```powershell
New-NetFirewallRule -DisplayName "Gestion Actas 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

## 5. Correo
Copiar `.env.example` a `.env` y configurar el SMTP institucional.
La aplicación no guarda contraseñas de correo en el código.

## 6. Siguiente etapa
- Login y roles
- Inventario de activos
- Búsqueda por código/serial
- Consecutivo automático
- Consulta de actas
- Envío real por SMTP
- Copia de PDF en NAS
- Auditoría
- HTTPS
