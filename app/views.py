from app import app
from flask import render_template, redirect, request, url_for, abort
from werkzeug.utils import secure_filename
from PyPDF2 import PdfFileReader
import os
import io
import uuid
import ntplib
from time import ctime
import psycopg2


class PostDatabase:
    def __init__(self, dbname, username, password, hostname, port):
        self.dbname = dbname
        self.username = username
        self.password = password
        self.hostname = hostname
        self.port = port

    def insert(self, job):
        conn = psycopg2.connect(database=self.dbname, user=self.username,
                                password=self.password, host=self.hostname, port=self.port)
        cur = conn.cursor()
        STATEMENT = '''INSERT INTO docs(uuid,confirmed,file,username,pages,state,createdat,filedata) VALUES('{}',false,'{}','{}','{}','NEW','{}',{});'''.format(
            job['uuid'],job['file'], job['username'], job['pages'], job['createdAt'],psycopg2.Binary(job['content']))
        cur.execute(STATEMENT)
        conn.commit()
        conn.close()

    def get_queue(self):
        conn = psycopg2.connect(database=self.dbname, user=self.username,
                                password=self.password, host=self.hostname, port=self.port)
        cur = conn.cursor()
        STATEMENT = '''SELECT * FROM docs;'''
        cur.execute(STATEMENT)
        response = cur.fetchall()
        result = []
        for res in response:
            newJob = {
                'username': res[3],
                'file': res[2],
                'pages': res[4],
                'createdAt': res[6].strftime('%m/%d/%Y'),
                'confirmed': res[1],
                'status': res[5]
            }
            result.append(newJob)
        conn.commit()
        conn.close()
        return result


@app.route("/")
def index():
    return render_template("public/index.html")

@app.route("/status")
def status():
    jobs = []
    db = PostDatabase(
        dbname='trial', 
        username='trial',
        password='@', 
        hostname='trial', 
        port=5432
    )
    jobs = db.get_queue()
    return render_template("public/status.html",jobs=jobs)


app.config["PDF_UPLOADS"] = "/Users/ankitsingh/Desktop/printer_app/app/static/pdf_uploads"


def check_if_pdf(filename):
    ALLOWED_EXTENSIONS = ["PDF"]
    if filename.split('.')[-1].upper() not in ALLOWED_EXTENSIONS:
        return False
    return True


def check_page(filename):
    response = {
        "filename": "samplefilename",
        "numPages": 0
    }
    with open(filename, "rb") as pdf_file:
        pdf_reader = PdfFileReader(pdf_file)
        response["filename"] = filename
        response["numPages"] = pdf_reader.numPages
        pdf_file.close()
    return response

def get_pdf_content(filename):
    response = {
        "filename": "samplefilename",
        "content": "random content"
    }
    with open(filename,'rb') as pdf_file:
        response['content'] = pdf_file.read()
        pdf_file.close()
    return response


def get_current_time():
    client = ntplib.NTPClient()
    response = client.request("in.pool.ntp.org", version=3)
    return response.tx_time

def updateDB(job):
    db = PostDatabase(
        dbname='trial', 
        username='trial',
        password='@', 
        hostname='trial', 
        port=5432
    )
    db.insert(job)
    return "Successfully inserted new data", 200

@app.route("/upload-file", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if request.files:
            pdf = request.files["pdf"]
            username = request.form["username"]

            if not check_if_pdf(pdf.filename):
                abort(415)

            if username == "":
                abort(416)

            filename = username + "_" + secure_filename(pdf.filename)
            savepath = os.path.join(app.config["PDF_UPLOADS"], filename)
            

            pdf.save(savepath)
            pages = check_page(savepath)
            content = get_pdf_content(savepath)['content']
            os.remove(savepath)

            newjob = {
                "uuid": str(uuid.uuid4()),
                "confirmed": False,
                "createdAt": ctime(get_current_time()),
                "file": filename,
                "username": username,
                "pages": pages["numPages"],
                "state": "NEW",
                "content": content
            }
            updateDB(newjob)
            return redirect(url_for('status'))
        else:
            abort(417)
    return render_template("public/index.html")
