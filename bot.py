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
        df["data"] = pd.to_datetime(df["data"], errors="coerce")  # Assicurati che la colonna "data" sia di tipo datetime
        df = df.sort_values("data")  # Ordina gli eventi per data
        return df
    except Exception as e:
        logger.error(f"Errore nella lettura del CSV: {e}")
        return pd.DataFrame(columns=["data", "event", "descrizione"])


# Comando /next per il prossimo evento
async def next_event(update: Update, context: CallbackContext):
    df = read_events()
    today = datetime.date.today()
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

# Configura il bot con i comandi
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("next", next_event))
    app.add_handler(CommandHandler("next5events", next_5_events))

    logger.info("Il bot è avviato e in ascolto dei comandi...")
    app.run_polling()

if __name__ == "__main__":
    main()
0 commit comments
Comments
0
