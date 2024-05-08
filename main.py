import requests, pandas, os, smtplib, sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
from pretty_html_table import build_table
from email.message import EmailMessage
from email_body import header

#fetch required data from Korean-English Learners' Dictionary - word of the day
URL = "https://krdict.korean.go.kr/eng/mainAction"

response = requests.get(URL)
response.raise_for_status()

soup = BeautifulSoup(response.text,"html.parser")
today_word = soup.find(class_="today_word")
word_korean = today_word.find("strong").get_text()
speech_part = today_word.find(class_="manyLang6").get_text().strip()
word_english = today_word.find("dd", "manyLang6").get_text()
sound_link = today_word.find("a", class_="sound").get("href")[23:-2]
example = " translation: ".join([i.get_text() for i in today_word.find_all("dd")][1:3])

#create db
connection = sqlite3.connect("korean.db")
c = connection.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS KoreanWords
                  (Word TEXT, EnglishTranslation TEXT, PartOfSpeech TEXT, Example TEXT, Sound TEXT)''')

record = (word_korean, word_english, speech_part, example, sound_link)
c.execute("INSERT INTO KoreanWords VALUES (?, ?, ?, ?, ?)", record)
connection.commit()
def send_email(body):

    EMAIL = os.environ["EMAIL"]
    PASSWORD = os.environ["EMAIL_PASSWORD"]

    msg = EmailMessage()
    msg['Subject'] = '안녕하세요! KOREAN NEW WORDS OF THIS WEEK! 🇰🇷'
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg.set_content(header + body, subtype="html")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as connection:
        connection.login(EMAIL, PASSWORD)
        connection.send_message(msg)

c.execute("SELECT * FROM KoreanWords")
rows = c.fetchall()

#send email with words of the day from the last week if SUNDAY and clear data

today = datetime.today()

if today.weekday() == 6:
    # Read all entries from the database and convert into df, send email and clear data
    c.execute("SELECT * FROM KoreanWords")
    rows = c.fetchall()
    data = pandas.DataFrame(rows, columns=["Word","English Translation","Part of Speech","Example","Sound Link"])
    body = build_table(data, 'blue_light', font_size="12px", width="210px", text_align="center")
    send_email(body)
    c.execute("DELETE FROM KoreanWords")
    connection.commit()

c.close()
connection.close()
