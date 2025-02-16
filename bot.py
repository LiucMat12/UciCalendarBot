import os
import pandas as pd
import logging
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Configura il logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica il token dalle variabili d'ambiente
TOKEN = os.getenv("TOKEN_BOT")
CHAT_ID = os.getenv("CHAT_ID")

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

# Funzione per ottenere l'evento di oggi o il prossimo disponibile
def get_daily_event():
    df = read_events()
    today = datetime.date.today()

    # Controlla se c'è un evento oggi
    events_today = df[df["data"].dt.date == today]
    if not events_today.empty:
        return events_today.iloc[0]

    # Se non ci sono eventi oggi, cerca il primo evento futuro
    future_events = df[df["data"].dt.date > today]
    if not future_events.empty:
        return future_events.iloc[0]

    return None  # Nessun evento disponibile

# Funzione per inviare il promemoria ogni giorno alle 9:00
async def send_reminder(context: CallbackContext):
    event = get_daily_event()
    if event is not None:
        message = f"🔔 *Promemoria Gara*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
    else:
        message = "🚫 Nessuna gara in programma per oggi o domani."

    await context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

# Comando /next per vedere il prossimo evento
async def next_event(update: Update, context: CallbackContext):
    event = get_daily_event()
    if event is not None:
        message = f"🎯 *Prossimo Evento*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
    else:
        message = "🚫 Nessun evento in programma."

    await update.message.reply_text(message, parse_mode="Markdown")

# Comando /next5events per vedere i prossimi 5 eventi
async def next_5_events(update: Update, context: CallbackContext):
    df = read_events()
    today = datetime.date.today()
    future_events = df[df["data"].dt.date >= today]

    if not future_events.empty:
        events_list = future_events.head(5)
        message = "📅 *Prossimi 5 Eventi:*\n"
        for _, event in events_list.iterrows():
            message += f"🔹 {event['data'].strftime('%d-%m-%Y')} - {event['event']}\n"
    else:
        message = "🚫 Nessun evento in programma."

    await update.message.reply_text(message, parse_mode="Markdown")

# Configura il bot con i comandi e il reminder automatico
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("next", next_event))
    app.add_handler(CommandHandler("next5events", next_5_events))

    # Aggiunge il job per il promemoria giornaliero alle 9:00
    app.job_queue.run_daily(send_reminder, time=datetime.time(hour=16, minute=35))

    logger.info("Il bot è avviato e in ascolto dei comandi...")
    app.run_polling()

if __name__ == "__main__":
    main()
