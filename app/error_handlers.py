from app import app

from flask import render_template, request

@app.errorhandler(404)
def not_found(e):
    return render_template("public/errorhandlers/404.html")

@app.errorhandler(415)
def server_error(e):
    return render_template("public/errorhandlers/415.html")

@app.errorhandler(416)
def no_username(e):
    return render_template("public/errorhandlers/416.html")

@app.errorhandler(417)
def no_file(e):
    return render_template("public/errorhandlers/417.html")