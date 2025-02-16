import pandas as pd
import datetime
import time
import schedule
from telegram import Bot
from datetime import datetime, timedelta
import os

# Ottieni il token del bot e chat ID dalle variabili d'ambiente
TOKEN_BOT = os.getenv('TOKEN_BOT')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TOKEN_BOT)

def invia_promemoria():
    # Percorso al file CSV
    file_csv= https://github.com/LiucMat12/UciCalendarBot/blob/main/eventi.csv  # Cambia con il percorso effettivo
    eventi = pd.read_csv(file_csv)

oggi = datetime.now()
    domani = oggi + timedelta(days=1)

    for _, row in eventi.iterrows():
        data_evento = datetime.datetime.strptime(row["data"], "%Y-%m-%d").date()
        if data_evento == domani:
            messaggio = f"🔔 *Promemoria Evento*\n\n📅 Data: {row['data']}\n🏷 *{row['titolo']}*\n📝 {row['descrizione']}"
            bot.send_message(chat_id=CHAT_ID, text=messaggio, parse_mode="Markdown")

# Pianifica l'esecuzione del promemoria una volta al giorno
schedule.every().day.at("09:00").do(invia_promemoria)  # Esegui ogni giorno alle 9:00 AM

schedule.every().day.at("12:00").do(invia_promemoria)  # Esegui ogni giorno alle 12:00 AM

if __name__ == "__main__":
    # Loop infinito per eseguire il controllo
while True:
    schedule.run_pending()
    time.sleep(60)  # Attendi un minuto prima di controllare di nuovo

