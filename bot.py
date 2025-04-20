import os
import pandas as pd
import logging
import json
from datetime import datetime, timedelta, time
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import pytz  # Gestione dei fusi orari

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica il token dalle variabili d'ambiente
TOKEN = os.getenv("TOKEN_BOT")

# Configura il fuso orario italiano
ITALY_TZ = pytz.timezone("Europe/Rome")

# File per salvare gli utenti
USER_FILE = "users.json"

# Funzione per caricare la lista di utenti registrati
def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Funzione per salvare gli utenti nel file
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# Comando /start per registrare l'utente
async def start(update: Update, context: CallbackContext):
    user_id = update.message.chat_id
    users = load_users()

    if user_id not in users:
        users.append(user_id)  # Salviamo l'ID dell'utente
        save_users(users)
        await update.message.reply_text("✅ Ti sei registrato per ricevere le notifiche sugli eventi!")
    else:
        await update.message.reply_text("ℹ️ Sei già registrato.")

# Funzione per leggere il file CSV
def read_events():
    try:
        df = pd.read_csv("eventi.csv", parse_dates=["data"])
        df["data"] = pd.to_datetime(df["data"], errors="coerce")
        df = df.sort_values("data")
        return df
    except Exception as e:
        logger.error(f"Errore nella lettura del CSV: {e}")
        return pd.DataFrame(columns=["data", "event", "descrizione"])

# Funzione per inviare il promemoria automatico
async def send_reminder(context: CallbackContext):
    df = read_events()
    today = datetime.now(ITALY_TZ).date()

    today_events = df[df["data"].dt.date == today]
    if not today_events.empty:
        event = today_events.iloc[0]
        message = f"🎯 *Gara di Oggi*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
    else:
        tomorrow = today + timedelta(days=1)
        tomorrow_events = df[df["data"].dt.date == tomorrow]
        if not tomorrow_events.empty:
            event = tomorrow_events.iloc[0]
            message = f"📅 *Nessuna gara oggi. Prossima gara domani!*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
        else:
            message = "🚫 Nessuna gara oggi o domani."

    users = load_users()
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Errore nell'invio a {user_id}: {e}")

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

    users = load_users()
    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Errore nell'invio del riepilogo settimanale a {user_id}: {e}")

# Configura il bot con i comandi e la JobQueue
def main():
    app = Application.builder().token(TOKEN).build()

    # Aggiungi i comandi
    app.add_handler(CommandHandler("start", start))  # REGISTRA GLI UTENTI
    app.add_handler(CommandHandler("next", next_event))
    app.add_handler(CommandHandler("next5events", next_5_events))

    # Configura JobQueue per il promemoria automatico

rome_tz = pytz.timezone('Europe/Rome')

job_queue = app.job_queue
job_queue.run_daily(send_reminder, time=time(hour=0, minute=1, tzinfo=rome_tz))  # 00:01 italiane
job_queue.run_daily(send_weekly_summary, time=time(hour=0, minute=1, tzinfo=rome_tz), days=(6,))  # Domenica


    logger.info("Il bot è avviato e in ascolto dei comandi...")
    app.run_polling()

if __name__ == "__main__":
    main()
