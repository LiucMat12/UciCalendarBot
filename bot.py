import os
import pandas as pd
import logging
from datetime import datetime, timedelta, time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import pytz  # Gestione dei fusi orari

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica il token dalle variabili d'ambiente
TOKEN = os.getenv("TOKEN_BOT")
CHAT_ID = os.getenv("CHAT_ID")

# Memorizza l'ultimo promemoria inviato
LAST_REMINDER = None

# Configura il fuso orario italiano
ITALY_TZ = pytz.timezone("Europe/Rome")

# Funzione per leggere il file CSV
def read_events():
    try:
        df = pd.read_csv("eventi.csv", parse_dates=["data"])  # Parsea le date
        df["data"] = pd.to_datetime(df["data"], errors="coerce")  # Assicurati che la colonna "data" sia datetime
        df = df.sort_values("data")  # Ordina gli eventi per data
        return df
    except Exception as e:
        logger.error(f"Errore nella lettura del CSV: {e}")
        return pd.DataFrame(columns=["data", "event", "descrizione"])

# Funzione per inviare il promemoria automatico
async def send_reminder(context: CallbackContext):
    global LAST_REMINDER
    df = read_events()
    today = datetime.now(ITALY_TZ).date()
    
    today_events = df[df["data"].dt.date == today]
    if not today_events.empty:
        event = today_events.iloc[0]
        message = f"🎯 *Gara di Oggi*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
    else:
        # Cerca l'evento di domani se oggi non c'è nulla
        tomorrow = today + timedelta(days=1)
        tomorrow_events = df[df["data"].dt.date == tomorrow]
        if not tomorrow_events.empty:
            event = tomorrow_events.iloc[0]
            message = f"📅 *Nessuna gara oggi. Prossima gara domani!*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
        else:
            message = "🚫 Nessuna gara oggi o domani."

    LAST_REMINDER = message  # Salva il messaggio come ultimo promemoria
    
    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# Comando per recuperare l'ultimo promemoria
async def last_reminder(update: Update, context: CallbackContext):
    if LAST_REMINDER:
        await update.message.reply_text(LAST_REMINDER, parse_mode="Markdown")
    else:
        await update.message.reply_text("🔔 Nessun promemoria inviato finora.")

# Comando /next per il prossimo evento
async def next_event(update: Update, context: CallbackContext):
    df = read_events()
    today = datetime.now(ITALY_TZ).date()
    future_events = df[df["data"].dt.date >= today]

    if not future_events.empty:
        next_event = future_events.iloc[0]
        message = f"🎯 *Prossimo Evento*\n📅 {next_event['data'].strftime('%d-%m-%Y')}\n📌 {next_event['event']}\n📝 {next_event['descrizione']}"
    else:
        message = "🚫 Nessun evento in programma."

    await update.message.reply_text(message, parse_mode="Markdown")

# Comando /next5events per i prossimi 5 eventi
async def next_5_events(update: Update, context: CallbackContext):
    df = read_events()
    today = datetime.now(ITALY_TZ).date()
    future_events = df[df["data"].dt.date >= today]

    if not future_events.empty:
        events_list = future_events.head(5)
        message = "📅 *Prossimi 5 Eventi:*\n"
        for _, event in events_list.iterrows():
            message += f"🔹 {event['data'].strftime('%d-%m-%Y')} - {event['event']}\n"
    else:
        message = "🚫 Nessun evento in programma."

    await update.message.reply_text(message, parse_mode="Markdown")

# Funzione per il riepilogo settimanale delle gare
async def send_weekly_summary(context: CallbackContext):
    df = read_events()
    today = datetime.now(ITALY_TZ).date()
    next_monday = today + timedelta(days=(7 - today.weekday()))  # Prossimo lunedì
    next_sunday = next_monday + timedelta(days=6)  # Fine settimana

    upcoming_events = df[(df["data"].dt.date >= next_monday) & (df["data"].dt.date <= next_sunday)]
    
    if not upcoming_events.empty:
        message = "📆 *Gare della prossima settimana:*\n"
        for _, event in upcoming_events.iterrows():
            message += f"🔹 {event['data'].strftime('%d-%m-%Y')} - {event['event']}\n"
    else:
        message = "🚫 Nessuna gara programmata per la prossima settimana."

    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# Configura il bot con i comandi e la JobQueue
def main():
    app = Application.builder().token(TOKEN).build()

    # Aggiungi i comandi
    app.add_handler(CommandHandler("next", next_event))
    app.add_handler(CommandHandler("next5events", next_5_events))
    app.add_handler(CommandHandler("lastreminder", last_reminder))  # Nuovo comando

    # Configura JobQueue per il promemoria automatico
    job_queue = app.job_queue
    job_queue.run_daily(send_reminder, time=time(hour=23, minute=1, tzinfo=pytz.UTC))  # 00:01 italiane

    # Pianifica il riepilogo settimanale ogni domenica alle 00:01 italiane
    job_queue.run_daily(send_weekly_summary, time=time(hour=23, minute=1, tzinfo=pytz.UTC), days=(6,))  # 6 = Domenica

    logger.info("Il bot è avviato e in ascolto dei comandi...")
    app.run_polling()

if __name__ == "__main__":
    main()
