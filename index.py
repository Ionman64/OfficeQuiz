import os
import smtplib
from email.message import EmailMessage
import mysql.connector

APP_NAME = "OfficeQuiz"
DATABASE_HOST = "localhost"
DATABASE_NAME = "quiz"
DATABASE_ROOT = "root"
DATABASE_PASSWORD = ""
EMAIL_SMTP_ADDRESS = "127.0.0.1"
EMAIL_SMTP_PORT = 1025
EMAIL_FROM_ADDR = "officequiz@mail.com"

def get_mysql_connection():
    return mysql.connector.connect(
      host=DATABASE_HOST,
      user=DATABASE_ROOT,
      passwd=DATABASE_PASSWORD
    )

def get_database_connection():
    return mysql.connector.connect(
      host=DATABASE_HOST,
      user=DATABASE_ROOT,
      passwd=DATABASE_PASSWORD,
      database=DATABASE_NAME
    )

class QuestionPool:
    def __init__(self):
        self.questions = []
    def add_question(self, question):
        self.questions.append(question)
    def get_questions(self):
        return self.questions
    def get_random_question(self):
        return self.questions[]

class Question:
    def __init__(self, text, answer, choices):
        self.id = None
        self.text = text
        self.choices = choices
        self.answer = answer
    def get_answer(self):
        return self.answer
    def get_choices(self):
        return self.choices
    def get_text(self):
        return self.text

class Group:
    def __init__(self, name):
        self.id = None
        self.players = []
        self.name = name
    def add_player(self, player):
        self.players.append(player)
    def get_players(self):
        return self.players

class Player:
    def __init__(self, name, email):
        self.id = None
        self.name = name
        self.email = email
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    def get_email(self):
        return self.email

def send_email(msg):
    msg = EmailMessage()
    msg["Subject"] = ("[%s] %s" % (APP_NAME, msg["Subject"]))
    msg['From'] = EMAIL_FROM_ADDR
    msg['To'] = "person@mail.com"
    msg.set_content("Hello World")
    with smtplib.SMTP(EMAIL_SMTP_ADDRESS, EMAIL_SMTP_PORT) as server:
        #Send the mail
        server.send_message(msg)

def get_new_question():
    db = get_database_connection()
    cursor = db.cursor()
    db.execute("SELECT * FROM questions LIMIT 1")
    myresult = cursor.fetchall()
    



if __name__ == "__main__":
    groups = []
    group = Group("Some Group")
    groups.append(group)
    print (groups)
    print (group.name)

    


    
