import pandas as pd
import datetime
import time
import schedule
from telegram import Bot

TOKEN = 7981437591:AAGQqWOzccytWLRC6HDKPQtRgzJAaxaWAbI
CHAT_ID = "IL_TUO_CHAT_ID"
FILE_CSV = "eventi.csv"

bot = Bot(token=TOKEN)

def invia_promemoria():
    oggi = datetime.date.today()
    domani = oggi + datetime.timedelta(days=1)
    eventi = pd.read_csv(FILE_CSV)

    for _, row in eventi.iterrows():
        data_evento = datetime.datetime.strptime(row["data"], "%Y-%m-%d").date()
        if data_evento == domani:
            messaggio = f"🔔 *Promemoria Evento*\n\n📅 Data: {row['data']}\n🏷 *{row['titolo']}*\n📝 {row['descrizione']}"
            bot.send_message(chat_id=CHAT_ID, text=messaggio, parse_mode="Markdown")

schedule.every().day.at("09:00").do(invia_promemoria)

if __name__ == "__main__":
    while True:
        schedule.run_pending()
        time.sleep(60)

