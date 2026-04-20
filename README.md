# 🔧 Bot de Reportes Técnicos — Telegram

Bot de Telegram para generar PDF de reportes técnicos de mantenimiento/reparaciones.
**Costo: $0**

---

## ¿Qué hace?

El técnico escribe `/nuevo` en Telegram, responde 4 preguntas (cliente, teléfono, dirección, descripción), envía fotos, y recibe un **PDF profesional** con logo, datos del cliente y registro fotográfico numerado.

- ✅ Entrada por **voz o texto**
- ✅ Fotos en el PDF (2 por fila)
- ✅ Folio único por reporte
- ✅ Logo personalizable

---

## Setup paso a paso

### 1. Crear el bot en Telegram (2 minutos)

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Dale un nombre, ej: `Reportes Técnicos`
4. Dale un usuario, ej: `mi_reporte_tecnico_bot`
5. Copia el **token** que te da (parece: `123456:ABC-DEF...`)

### 2. Obtener API Key de Groq (transcripción de voz gratis)

1. Ve a **https://console.groq.com**
2. Crea cuenta gratuita
3. Ve a **API Keys → Create API Key**
4. Copia la key

### 3. Agregar tu logo (opcional)

Pon tu logo como `logo.png` en la carpeta del proyecto.
Tamaño recomendado: 200x80 px, fondo transparente o blanco.

### 4. Desplegar en Render.com (gratis)

#### 4a. Subir código a GitHub

```bash
git init
git add .
git commit -m "bot inicial"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/reporte-bot.git
git push -u origin main
```

#### 4b. Crear servicio en Render

1. Ve a **https://render.com** → New → **Background Worker**
2. Conecta tu repositorio de GitHub
3. Configura:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
4. En **Environment Variables** agrega:
   ```
   BOT_TOKEN=tu_token_de_botfather
   GROQ_API_KEY=tu_api_key_de_groq
   NOMBRE_EMPRESA=Nombre Tu Negocio
   ```
5. Clic en **Create Background Worker**

✅ En 2-3 minutos el bot estará activo 24/7.

---

## Uso del bot

| Comando | Acción |
|---------|--------|
| `/nuevo` o `/start` | Iniciar nuevo reporte |
| `/listo` | Terminar de enviar fotos y generar PDF |
| `/cancelar` | Cancelar el reporte actual |

### Flujo completo:

```
/nuevo
→ "¿Nombre del cliente?"          → Escribe el nombre
→ "¿Teléfono?"                    → Escribe el número
→ "¿Dirección?"                   → Escribe la dirección
→ "Describe el trabajo"           → Habla un audio 🎙 o escribe texto
→ "Envía las fotos"               → Envía 1, 2, 3... fotos
→ /listo
→ 📄 Bot envía el PDF
```

---

## Variables de entorno

| Variable | Descripción | Requerida |
|----------|-------------|-----------|
| `BOT_TOKEN` | Token de @BotFather | ✅ Sí |
| `GROQ_API_KEY` | Key de Groq para voz | ✅ Sí (para audio) |
| `NOMBRE_EMPRESA` | Nombre en el encabezado del PDF | No (default: "Servicio Técnico") |

---

## Correr localmente (para pruebas)

```bash
pip install -r requirements.txt

# En Windows:
set BOT_TOKEN=tu_token
set GROQ_API_KEY=tu_groq_key
set NOMBRE_EMPRESA=Tu Negocio

# En Mac/Linux:
export BOT_TOKEN=tu_token
export GROQ_API_KEY=tu_groq_key
export NOMBRE_EMPRESA="Tu Negocio"

python bot.py
```

---

## Estructura del proyecto

```
reporte-tecnico-bot/
├── bot.py              # Lógica del bot
├── pdf_generator.py    # Generación del PDF
├── requirements.txt    # Dependencias
├── logo.png            # Tu logo (opcional)
└── README.md
```

---

## Preguntas frecuentes

**¿Funciona sin internet el técnico?**
No, necesita datos móviles para enviar fotos y audios por Telegram.

**¿Puedo agregar más campos?**
Sí, en `bot.py` agrega un nuevo estado en el `ConversationHandler` y un campo en `data` en `pdf_generator.py`.

**¿Cuánto cuesta Groq?**
Tiene free tier generoso (~2 horas de audio/día). Para uso normal de un técnico, nunca lo superarás.

**¿Render.com puede apagar el bot?**
El plan gratuito de Background Workers no tiene sleep (a diferencia de Web Services). Tu bot corre 24/7.
