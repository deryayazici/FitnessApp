import sys
from flask import Flask, render_template, request, redirect, url_for, g 
import sqlite3
import pdb

print(sys.executable)


app = Flask(__name__)


@app.route("/")
def home():
        return render_template ('home.html')

@app.route("/running", methods=["GET","POST"])
def running():
     pdb.set_trace()
     return render_template('running.html')

@app.route("/exercise", methods=["GET", "POST"])
def exercise():
    conn = get_db()
    c = conn.cursor()
    if request.method == "POST":
         
         c.execute("""INSERT INTO fitness(id,title, description)
                    VALUES(?,?,?)""",
                    (
                        request.form.get("title"),
                        request.form.get("description")
                    )
        )
    conn.commit()
        #  print("Form data:")
        #  print("Title: {}, Description: {}".format(
        #        request.form.get("title"), request.form.get("description")
        #  ))
    return redirect(url_for("home"))
    return render_template('exercise.html')

def get_db():
     db = getattr(g, "_database", None)
     if db is None:
          db = g._database = sqlite3.connect("db/fitness.db")
     return db

def close_connection():
     db = getattr(g, "_database", None)
     if db is not None:
          db.close(Exception)

@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'public, max-age=1'
    return response

if __name__ == '__main__':
    app.run(debug=True)
