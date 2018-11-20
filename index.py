import os
import smtplib
from email.message import EmailMessage
import mysql.connector

APP_NAME = "OfficeQuiz"

def setup_database():
    

def get_mysql_connection():
    return mysql.connector.connect(
      host=DATABASE_HOST,
      user=DATABASE_ROOT,
      passwd=DATABASE_PASSWORD
      database=DATABASE_NAME
    )

def get_database_connection():
    return mysql.connector.connect(
      host=DATABASE_HOST,
      user=DATABASE_ROOT,
      passwd=DATABASE_PASSWORD
      database=DATABASE_NAME
    )

class Question:
    id = None
    text = None
    choices = []
    answer = None

def send_email(msg):
    msg = EmailMessage()
    msg["Subject"] = ("[%s] %s" % (APP_NAME, msg["Subject"]))
    msg['From'] = EMAIL_FROM_ADDR
    msg['To'] = "person@mail.com"
    msg.set_content("Hello World")
    with smtplib.SMTP(EMAIL_SMTP_ADDRESS, EMAIL_SMTP_PORT) as server:
        #Send the mail
        server.send_message(msg)

def add_question(question):
    

def get_new_question():
    db = get_database_connection()
    cursor = db.cursor()
    db.execute("SELECT * FROM questions LIMIT 1")
    myresult = cursor.fetchall()
    



if __name__ == "__main__":
    DATABASE_HOST = "localhost"
    DATABASE_NAME = "quiz"
    DATABASE_ROOT = "root"
    DATABASE_PASSWORD = ""
    EMAIL_SMTP_ADDRESS = "127.0.0.1"
    EMAIL_SMTP_PORT = 1025
    EMAIL_FROM_ADDR = "officequiz@mail.com"

    


    
