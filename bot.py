import os
import logging
import tempfile
import datetime
import asyncio
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from pdf_generator import generar_pdf

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Estados de la conversación ──────────────────────────────────────────────
(
    NOMBRE_CLIENTE,
    TELEFONO_CLIENTE,
    DIRECCION_CLIENTE,
    DESCRIPCION_TRABAJO,
    FOTOS,
) = range(5)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")


# ── /start y /nuevo ──────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    context.user_data["fotos"] = []
    await update.message.reply_text(
        "🔧 *Nuevo Reporte Técnico*\n\n"
        "Vamos paso a paso.\n\n"
        "👤 ¿Nombre completo del cliente?",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove(),
    )
    return NOMBRE_CLIENTE


# ── Pasos del flujo ───────────────────────────────────────────────────────────
async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["nombre"] = update.message.text.strip()
    await update.message.reply_text("📱 ¿Número de teléfono del cliente?")
    return TELEFONO_CLIENTE


async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["telefono"] = update.message.text.strip()
    await update.message.reply_text("📍 ¿Dirección del servicio?")
    return DIRECCION_CLIENTE


async def recibir_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["direccion"] = update.message.text.strip()
    await update.message.reply_text(
        "🔧 Describe el trabajo realizado.\n\n"
        "Puedes enviar un 🎙 *audio* o escribir el texto directamente.",
        parse_mode="Markdown",
    )
    return DESCRIPCION_TRABAJO


async def recibir_descripcion_texto(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    context.user_data["descripcion"] = update.message.text.strip()
    await update.message.reply_text(
        "📷 Envía las fotos del trabajo (una por una).\n"
        "Cuando termines, escribe /listo\n\n"
        "_Si no tienes fotos, también escribe /listo_",
        parse_mode="Markdown",
    )
    return FOTOS


async def recibir_descripcion_voz(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Transcribe el audio con Groq Whisper (gratis)."""
    msg = await update.message.reply_text("🎙 Transcribiendo audio...")

    voice = update.message.voice
    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        await tg_file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        from groq import Groq
        import subprocess

        # Convertir ogg/opus → mp3 para compatibilidad con Groq
        mp3_path = tmp_path.replace(".ogg", ".mp3")
        subprocess.run(
            ["ffmpeg", "-y", "-i", tmp_path, "-ar", "16000", "-ac", "1", mp3_path],
            check=True,
            capture_output=True,
        )

        client = Groq(api_key=GROQ_API_KEY)
        with open(mp3_path, "rb") as audio_file:
            transcripcion = client.audio.transcriptions.create(
                file=("audio.mp3", audio_file, "audio/mpeg"),
                model="whisper-large-v3",
                language="es",
            )
        os.unlink(mp3_path)
        texto = transcripcion.text.strip()
        context.user_data["descripcion"] = texto
        await msg.edit_text(
            f"✅ *Transcripción:*\n\n_{texto}_\n\n"
            "📷 Envía las fotos del trabajo (una por una).\n"
            "Cuando termines, escribe /listo\n\n"
            "_Si no tienes fotos, también escribe /listo_",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.error(f"Error Groq: {e}")
        await msg.edit_text(
            "⚠️ No pude transcribir el audio. Escribe la descripción en texto por favor."
        )
        return DESCRIPCION_TRABAJO
    finally:
        os.unlink(tmp_path)

    return FOTOS


async def recibir_foto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    photo = update.message.photo[-1]  # mayor resolución
    context.user_data["fotos"].append(photo.file_id)
    n = len(context.user_data["fotos"])
    await update.message.reply_text(
        f"✅ Foto {n} guardada. Sigue enviando o escribe /listo"
    )
    return FOTOS


async def generar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Genera el PDF y lo envía."""
    msg = await update.message.reply_text("⏳ Generando reporte PDF...")

    # Descargar fotos
    fotos_paths = []
    for file_id in context.user_data.get("fotos", []):
        tg_file = await context.bot.get_file(file_id)
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        await tg_file.download_to_drive(tmp.name)
        fotos_paths.append(tmp.name)

    data = {
        "nombre": context.user_data.get("nombre", ""),
        "telefono": context.user_data.get("telefono", ""),
        "direccion": context.user_data.get("direccion", ""),
        "descripcion": context.user_data.get("descripcion", ""),
        "fotos": fotos_paths,
        "fecha": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
    }

    pdf_path = generar_pdf(data)

    nombre_archivo = f"Reporte_{data['nombre'].replace(' ', '_')}.pdf"
    with open(pdf_path, "rb") as f:
        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=f,
            filename=nombre_archivo,
            caption=(
                f"✅ *Reporte listo*\n"
                f"👤 {data['nombre']}\n"
                f"📅 {data['fecha']}"
            ),
            parse_mode="Markdown",
        )

    await msg.delete()

    # Limpieza
    os.unlink(pdf_path)
    for p in fotos_paths:
        os.unlink(p)

    context.user_data.clear()
    await update.message.reply_text(
        "🎉 ¡Listo! Escribe /nuevo para crear otro reporte."
    )
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Reporte cancelado. Escribe /nuevo para empezar de nuevo.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


# ── Main ──────────────────────────────────────────────────────────────────────
def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("nuevo", start),
        ],
        states={
            NOMBRE_CLIENTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)
            ],
            TELEFONO_CLIENTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)
            ],
            DIRECCION_CLIENTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_direccion)
            ],
            DESCRIPCION_TRABAJO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_descripcion_texto),
                MessageHandler(filters.VOICE, recibir_descripcion_voz),
            ],
            FOTOS: [
                MessageHandler(filters.PHOTO, recibir_foto),
                CommandHandler("listo", generar_reporte),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Bot iniciado ✅")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
