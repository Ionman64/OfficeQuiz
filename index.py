import os
import smtplib
from email.message import EmailMessage
import mysql.connector
import tornado.ioloop
import tornado.web
import csv
import jsonpickle
import uuid

APP_NAME = "OfficeQuiz"
DATABASE_HOST = "localhost"
DATABASE_NAME = "quiz"
DATABASE_ROOT = "root"
DATABASE_PASSWORD = ""
EMAIL_SMTP_ADDRESS = "127.0.0.1"
EMAIL_SMTP_PORT = 1025
EMAIL_FROM_ADDR = "officequiz@mail.com"

EMAILS_FILE = "emails.csv"
QUESTIONS_FILE = "questions.csv"
ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8888

question_pool = None #Will be set later
sent_question_ids = []

class QuestionAPI(tornado.web.RequestHandler):
    def get(self):
        questionId=self.get_argument("questionId", None, True)
        question = question_pool.get_question(questionId)
        self.write(question.get_text())

class PlayerAPI(tornado.web.RequestHandler):
    def get(self):
        self.write(jsonpickle.encode(groups[0].get_players()))

class QuestionsView(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-type', 'text/html; charset=utf-8')
        self.write("<h4>Questions</h4>")
        self.write("<table>")
        self.write("<thead>")
        self.write("<th>Question Id</th>")
        self.write("<th>Question Text</th>")
        self.write("</thead>")
        self.write("<tbody>")
        for question in question_pool.get_questions():
            self.write("<tr>")
            self.write("<td>%s</td>" % question.get_id())
            self.write("<td>%s</td>" % question.get_text())
            self.write("</tr>")
        self.write("</tbody>")
        self.write("</table>")

class PlayersView(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-type', 'text/html; charset=utf-8')
        self.write("<h1>Player Score</h1>")
        for group in groups:
            self.write("<h4>%s</h4>" % group.get_name())
            self.write("<table>")
            self.write("<thead>")
            self.write("<th>Player Name</th>")
            self.write("<th>Player Score</th>")
            self.write("</thead>")
            self.write("<tbody>")
            for player in group.get_players():
                self.write("<tr>")
                self.write("<td>%s</td>" % player.get_name())
                self.write("<td>%s</td>" % player.get_score())
                self.write("</tr>")
            self.write("</tbody>")
            self.write("</table>")
                

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

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
        return self.questions
    def get_question(self, id):
        for question in self.questions:
            if question.get_id() == id:
                return question

class Question:
    def __init__(self, text, answer, choices):
        self.id = str(uuid.uuid4())
        self.text = text
        self.choices = choices
        self.answer = answer
    def get_id(self):
        return self.id
    def get_answer(self):
        return self.answer
    def get_choices(self):
        return self.choices
    def get_text(self):
        return self.text
    def get_id(self):
        return self.id

class Group:
    def __init__(self, name):
        self.id = None
        self.players = []
        self.name = name
    def add_player(self, player):
        player.set_group_id(self.id)
        self.players.append(player)
    def get_players(self):
        return self.players
    def get_name(self):
        return self.name

class Player:
    def __init__(self, name, email):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.score = 0
        self.group_id = None
    def set_group_id(self, id):
        self.group_id = id
    def get_id(self):
        return self.id
    def get_name(self):
        return self.name
    def get_email(self):
        return self.email
    def get_score(self):
        return self.score

class AuthStaticFileHandler(BaseHandler, tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Cache-control", "no-cache")
    def get(self, path):                
        if len(path) == 0:
            path="index"            
        super(AuthStaticFileHandler, self).get(path + ".html")

def send_email(msg):
    msg = EmailMessage()
    msg["Subject"] = ("[%s] %s" % (APP_NAME, msg["Subject"]))
    msg['From'] = EMAIL_FROM_ADDR
    msg['To'] = "person@mail.com"
    msg.set_content("Hello World")
    with smtplib.SMTP(EMAIL_SMTP_ADDRESS, EMAIL_SMTP_PORT) as server:
        #Send the mail
        server.send_message(msg)

def load_questions():
    with open(QUESTIONS_FILE, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            choices = []
            question_pool.add_question(Question(row[0], row[1], choices))

def get_new_question():
    for question in question_pool.get_questions():
        if question.id not in sent_question_ids:
            return question

def make_app():
    return tornado.web.Application(static_path=os.path.join(ROOT, "static"), 
        template_path=os.path.join(ROOT, "templates"), 
        compress_response=True,
        cookie_secret="asecretmessage",
        login_url="/login",
        handlers = [
            (r"/api/question", QuestionAPI),
            (r"/api/players", PlayerAPI),
            (r"/players", PlayersView),
            (r"/questions", QuestionsView),
            (r"/(.*)", AuthStaticFileHandler, {"path": os.path.join(ROOT, "static")}),
        ])

if __name__ == "__main__":
    question_pool = QuestionPool()
    load_questions()
    groups = []
    group = Group("Some Group")
    with open(EMAILS_FILE, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            group.add_player(Player(row[0], row[1]))
    groups.append(group)
    print (group.players[0].get_name())
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
