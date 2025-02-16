import os
import pandas as pd
import logging
import schedule
import time
import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram.ext import Application

# Imposta il logging per debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carica il token del bot dalle variabili d'ambiente
TOKEN = os.getenv("TOKEN_BOT")
CHAT_ID = os.getenv("CHAT_ID")  # Imposta il tuo Chat ID nelle variabili di ambiente

# Funzione per leggere il file CSV
def read_events():
    try:
        df = pd.read_csv("eventi.csv", parse_dates=["data"])
        df = df.sort_values("data")  # Ordina gli eventi per data
        return df
    except Exception as e:
        logger.error(f"Errore nella lettura del CSV: {e}")
        return pd.DataFrame(columns=["data", "event", "descrizione"])

# Funzione per inviare un promemoria
def send_reminder(context: CallbackContext):
    df = read_events()
    today = datetime.date.today()
    
    # Cerca eventi per oggi
    events_today = df[df["data"].dt.date == today]

    if not events_today.empty:
        # Se ci sono eventi per oggi, invia il promemoria per oggi
        for _, event in events_today.iterrows():
            message = f"🔔 *Promemoria Evento*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
            context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
    else:
        # Se non ci sono eventi per oggi, invia il promemoria per domani
        tomorrow = today + datetime.timedelta(days=1)
        events_tomorrow = df[df["data"].dt.date == tomorrow]

        if not events_tomorrow.empty:
            for _, event in events_tomorrow.iterrows():
                message = f"🔔 *Promemoria Evento*\n📅 {event['data'].strftime('%d-%m-%Y')}\n📌 {event['event']}\n📝 {event['descrizione']}"
                context.bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        else:
            # Se non ci sono eventi nemmeno per domani
            message = "🚫 Non ci sono eventi per i prossimi giorni."
            context.bot.send_message(chat_id=CHAT_ID, text=message)

# Comando /next per il prossimo evento
def next_event(update: Update, context: CallbackContext):
    df = read_events()
    today = datetime.date.today()
    future_events = df[df["data"].dt.date >= today]

    if not future_events.empty:
        next_event = future_events.iloc[0]
        message = f"🎯 *Prossimo Evento*\n📅 {next_event['data'].strftime('%d-%m-%Y')}\n📌 {next_event['event']}\n📝 {next_event['descrizione']}"
    else:
        message = "🚫 Nessun evento in programma."

    update.message.reply_text(message, parse_mode="Markdown")

# Comando /next5events per i prossimi 5 eventi
def next_5_events(update: Update, context: CallbackContext):
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

    update.message.reply_text(message, parse_mode="Markdown")

# Configura il bot con i comandi
def main():
    app = Application.builder().token(TOKEN).build()

    dp = app

    dp.add_handler(CommandHandler("next", next_event))
    dp.add_handler(CommandHandler("next5events", next_5_events))

    # Pianifica l'invio giornaliero del promemoria alle 9:00
    schedule.every().day.at("09:00").do(lambda: send_reminder(app))

    # Avvia il polling per il bot
    app.run_polling()

    # Loop per eseguire i job pianificati
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
