import sys
from flask import Flask, render_template, request
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

@app.route("/exercise")
def exercise():
    return render_template('exercise.html')


@app.after_request
def add_cache_control(response):
    response.headers['Cache-Control'] = 'public, max-age=1'
    return response

if __name__ == '__main__':
    app.run(debug=True)
