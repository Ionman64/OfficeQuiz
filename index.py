import os
import smtplib
from email.message import EmailMessage
import tornado.ioloop
import tornado.web
from tornado import template
import csv
import jsonpickle
import uuid
import time
import _thread
import time
import subprocess
import string
import random

APP_NAME = "Christmas Quiz"
EMAIL_SMTP_ADDRESS = "127.0.0.1"
EMAIL_SMTP_PORT = 1025
EMAIL_FROM_ADDR = "officequiz@mail.com"

EMAILS_FILE = "emails.csv"
QUESTIONS_FILE = "questions.csv"
ROOT = os.path.dirname(os.path.abspath(__file__))
PORT = 8888
HOST = "127.0.0.1"

CORRECT_ANSWER_POINTS = 2
INCORRECT_ANSWER_POINTS = -1
BONUS_POINTS = 4

PLAYERS = {}
QUESTIONS = {}
SENT_QUESTIONS = []

QUESTION_INTERVAL_MINUTES = 5
END_OF_QUIZ = False

loader = template.Loader("templates")

EMAIL_MJML = """<mjml version="3.3.3">
  <mj-body background-color="#F4F4F4" color="#55575d" font-family="Arial, sans-serif">
    <mj-section background-color="#C1272D" background-repeat="repeat" padding="20px 0" text-align="center" vertical-align="top">
      <mj-column>
            <mj-text align="center" color="#fff" font-family="Indie Flower, sans-serif" font-size="26px">
            <h1>
                Christmas Quiz:<br>Question #%s
            </h1>
            </mj-text>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff" background-repeat="repeat" padding="20px 0" text-align="center" vertical-align="top">
      <mj-column>
          {{bonus_question}}
        <mj-text align="center" color="#000" font-family="Indie Flower, sans-serif" font-size="26px">
            <label>%s</label>
        </mj-text>
      </mj-column>
    </mj-section>
    <mj-section background-color="#ffffff" background-repeat="repeat" padding="20px 0" text-align="center" vertical-align="top">
        <mj-column>
            {{answers_section}}
        </mj-column>
    </mj-section>
    <mj-section background-color="#C1272D" background-repeat="repeat" padding="20px 0" text-align="center" vertical-align="top">
      <mj-column>
        <mj-text align="center" color="#ffffff" font-family="Indie Flower, sans-serif" font-size="13px" line-height="22px" padding="10px 25px">Good Luck!</mj-text>
      </mj-column>
    </mj-section>
  </mj-body>
</mjml>
"""

ANSWER_BUTTON_MJML = """<mj-button font-family="Indie Flower, sans-serif" background-color="#C1272D" color="#fff" width="100%" font-size="24px" href="{{answer_url}}">
                            {{answer_text}}
                        </mj-button>"""

def prepare_email(question, player, question_num):
    code = EMAIL_MJML % (question_num, question.get_text())
    if question.is_bonus():
        code = code.replace("{{bonus_question}}", "<mj-image src=\"http://127.0.0.1:8888/static/img/bonus.png\" height=\"40px\" width=\"120px\" alt=\"Bonus Question\" />")
    else:
        code = code.replace("{{bonus_question}}", "")
    inner_question_code = ""
    for choice in question.get_choices():
        answers_section = ANSWER_BUTTON_MJML
        answers_section = answers_section.replace("{{answer_url}}", get_question_link(question, player, choice))
        answers_section = answers_section.replace("{{answer_text}}", choice)
        inner_question_code = inner_question_code + answers_section
    code = code.replace("{{answers_section}}", inner_question_code)
    guid = uuid.uuid4()
    with open("emails/%s.mjml" % guid, "w", encoding="utf-8") as file:
        file.write(code)
    return guid 

def run_win_cmd(guid):
    result = []
    process = subprocess.Popen("npx mjml emails/%s.mjml -o emails/%s.html" % (guid, guid),shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for line in process.stdout:
        result.append(line)
    errcode = process.returncode
    #for line in result:
        #print (line)
    if errcode is not None:
        raise Exception('cmd %s failed, see above for details', cmd)

def read_email(guid):
    email_contents = ""
    with open("emails/%s.html" % guid, "r", encoding="utf-8") as file:
        for line in file:
            email_contents = email_contents + line
    return email_contents

class QuestionAPI(tornado.web.RequestHandler):
    def get(self):
        if END_OF_QUIZ:
            self.write(loader.load("message.html").generate(app_name=APP_NAME, message="Sorry, the quiz has ended. You'll have to wait until next year now!"))
            return
        playerId=self.get_argument("playerId", None, True)
        questionId=self.get_argument("questionId", None, True)
        answer=self.get_argument("answer", None, True)
        if (playerId == None) or (questionId == None) or (answer == None):
            self.write(loader.load("message.html").generate(app_name=APP_NAME, message="Hmm, looks like your request is missing a few parameters"))
            return
        if questionId not in QUESTIONS:
            self.write(loader.load("message.html").generate(app_name=APP_NAME, message="Hmm, could not find that question, perhaps the elves are still building it?"))
            return
        question = QUESTIONS[questionId]
        if playerId not in PLAYERS:
            self.write(loader.load("message.html").generate(app_name=APP_NAME, message="Hmm, could not find that player, maybe he is running late"))
            return
        player = PLAYERS[playerId]
        if questionId in player.get_answered_questions():
            self.write(loader.load("message.html").generate(app_name=APP_NAME, message="You already answered! You're on Santa's naughty list now!"))
            return
        if answer == question.get_answer():
            print ("%s (%s) has answered the question '%s' with the CORRECT answer '%s'" % (player.get_name(), player.get_email(), question.get_text(), answer))
            if question.is_bonus():
                player.increase_bonus(BONUS_POINTS)
            else:
                player.increase_score(CORRECT_ANSWER_POINTS)
        else:
            print ("%s (%s) has answered the question '%s' with the INCORRECT answer '%s' (Correct Answer: %s)" % (player.get_name(), player.get_email(), question.get_text(), answer, question.get_answer()))
            if not question.is_bonus():
                player.increase_score(INCORRECT_ANSWER_POINTS)
        player.answered_question(questionId)
        self.write(loader.load("message.html").generate(app_name=APP_NAME, message="Thanks, next question will be emailed soon!"))

class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.write(loader.load("message.html").generate(app_name=APP_NAME, message="404: Even Santa cannot find this page"))

class QuestionsView(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", 'text/html; charset="utf-8"')
    def get(self):
        self.write("<h4>Questions</h4>")
        self.write("<table>")
        self.write("<thead>")
        self.write("<th>Question Id</th>")
        self.write("<th>Question Text</th>")
        self.write("</thead>")
        self.write("<tbody>")
        for (key, question) in QUESTIONS.items():
            self.write("<tr>")
            self.write("<td>%s</td>" % question.get_id())
            self.write("<td>%s</td>" % question.get_text())
            self.write("</tr>")
        self.write("</tbody>")
        self.write("</table>")

class ScoreBoard(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", 'text/html; charset="utf-8"')
    def get(self):
        self.write(loader.load("scoreboard.html").generate(app_name=APP_NAME, groups=groups))
                

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

class Question:
    def __init__(self, text, answer, bonus_question, choices):
        self.id = str(uuid.uuid4())
        self.text = text
        self.choices = choices
        self.answer = answer
        self.bonus_question = (bonus_question == "1")
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
    def is_bonus(self):
        return self.bonus_question

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
    def get_team_score(self):
        team_score = 0
        for player in self.players:
            team_score = team_score + player.get_score()
        return team_score
        

class Player:
    def __init__(self, name, email):
        self.id = str(uuid.uuid4())
        self.name = name
        self.email = email
        self.score = 0
        self.group_id = None
        self.answered_questions = []
        self.bonus = 0
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
    def increase_score(self, addition):
        self.score = self.score + addition
    def increase_bonus(self, addition):
        self.bonus = self.bonus + addition
    def get_bonus(self):
        return self.bonus
    def get_answered_questions(self):
        return self.answered_questions
    def answered_question(self, questionId):
        self.answered_questions.append(questionId)
    def get_total_score(self):
        return self.get_score() + self.get_bonus()

def send_mails(messages, question_num):
    with smtplib.SMTP(EMAIL_SMTP_ADDRESS, EMAIL_SMTP_PORT) as server:
        for msg in messages:
            #Send the mail
            print("Sending question #%s to %s" % (question_num, msg["To"]))
            server.send_message(msg)
            print("Ok!")

def get_question_link(question, player, answer):
    return ("http://%s:%s/api/question?questionId=%s&playerId=%s&answer=%s" % (HOST, PORT, question.id, player.id, answer))

def run_quiz():
    question = get_new_question()
    question_num = 1
    while question is not None:
        messages = []
        for (key, player) in PLAYERS.items():
            msg = EmailMessage()
            msg["Subject"] = ("[%s] Question #%i!" % (APP_NAME, question_num))
            msg['From'] = EMAIL_FROM_ADDR
            msg['To'] = player.get_email()
            guid = prepare_email(question, player, question_num)
            run_win_cmd(guid)
            msg.set_content(read_email(guid), subtype='html')
            messages.append(msg)
        send_mails(messages, question_num)
        question_num = question_num + 1
        time.sleep(QUESTION_INTERVAL_MINUTES*60)
        question = get_new_question()
    END_OF_QUIZ = True
    messages = []
    for (key, player) in PLAYERS.items():
        msg = EmailMessage()
        msg["Subject"] = ("[%s] The quiz has ended!" % (APP_NAME))
        msg['From'] = EMAIL_FROM_ADDR
        msg['To'] = player.get_email()
        msg.set_content("Hej %s, it's the end of the quiz! Thanks for playing" % player.get_name())
        messages.append(msg)
    send_mails(messages, "EndOfQuiz")
        

def load_questions():
    with open(QUESTIONS_FILE, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            question = Question(row[0], row[1], row[2], row[3:])
            QUESTIONS[question.get_id()] = question

def get_new_question():
    for (key, question) in QUESTIONS.items():
        if question.id not in SENT_QUESTIONS:
            SENT_QUESTIONS.append(question.id)
            return question
    return None

def make_app():
    scoreboard_code = ''.join(random.choice(string.ascii_letters) for x in range(5))
    print ("ScoreBoard can be accessed at http://%s:%s/scoreboard/%s" % (HOST, PORT, scoreboard_code))
    return tornado.web.Application(static_path=os.path.join(ROOT, "static"), 
        template_path=os.path.join(ROOT, "templates"), 
        compress_response=True,
        cookie_secret="asecretmessage",
        login_url="/login",
        handlers = [
            (r"/api/question", QuestionAPI),
            (r"/scoreboard/" + scoreboard_code, ScoreBoard),
            (r"/questions", QuestionsView),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(ROOT, "static")}),
        ],
        default_handler_class=NotFoundHandler)

if __name__ == "__main__":
    load_questions()
    groups = {}
    with open(EMAILS_FILE, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            new_player = Player(row[1], row[2])
            PLAYERS[new_player.get_id()] = new_player
            group_name = row[0]
            group = None
            if group_name not in groups:
                group = Group(group_name)
                groups[group_name] = group
            else:
                group = groups[group_name]
            group.add_player(new_player)
    _thread.start_new_thread(run_quiz, ())
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

    


    
