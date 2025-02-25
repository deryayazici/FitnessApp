import sys
import requests
from typing import Any
from flask import Flask, render_template, request, redirect, request_finished, session, url_for, g, send_from_directory, flash
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import InputRequired, DataRequired, Length, ValidationError
from werkzeug.utils import secure_filename, escape
from html import unescape
import sqlite3
import os
import datetime
from secrets import token_hex
from running import Running
from walking import Walking
from cycling import Cycling
from sign_in import create_user, init_db


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)

app.config["SECRET_KEY"] = "secretkey"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMAGE_UPLOADS"] = os.path.join(basedir, "uploads")

app.config["TESTING"] = True

# app.config["RECAPTCHA_PUBLIC_KEY"] = "6Lct3hApAAAAAF3shHdCcXlLhzxvJiWbT2rH56XW"
# app.config["RECAPTCHA_PRIVATE_KEY"] = "6Lct3hApAAAAALPoW_BXUgEtj5rKurAyFGb-6mp9"

RECAPTCHA_SITE_KEY = "6LeDd-EqAAAAACGxEoc3BSg4xv-cRw2k6vwipdTy"       
RECAPTCHA_SECRET_KEY = "6LeDd-EqAAAAADHpnkAH-VMTEJ_iEM0lz4YvSoeg"

class ItemForm(FlaskForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=3, max=20, message="Input must be between 3 and 20 characters long")])
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=500, message="Input must be between 3 and 90 characters long")])
    image       = FileField("Image", validators=[FileAllowed(app.config["ALLOWED_IMAGE_EXTENSIONS"], "Images only!")])
    
        
class NewItemForm(ItemForm):
    #   recaptcha = RecaptchaField()
      submit     = SubmitField("submit")

class EditItemForm(ItemForm):
      title = StringField('Title', validators=[DataRequired()])
      description = TextAreaField('Description', validators=[DataRequired()])
      image = FileField('Image') 
      submit     = SubmitField("Update item")

class DeleteItemForm(FlaskForm):
    submit = SubmitField("Delete item")

class FilterForm(FlaskForm):
    title  = StringField("Title")
    submit = SubmitField("Filter")

#-------SIGN-IN ROUTE--------
DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            username TEXT NOT NULL UNIQUE,
            email TEXT,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     # Determine which form to display based on query parameter.
#     form_type = request.args.get('form', 'login')
    
#     if request.method == 'POST':
#         action = request.form.get('action')
#         if action == 'login':
#             username = request.form['username']
#             password = request.form['password']
#             conn = get_db_connection()
#             user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
#             conn.close()
#             if user:
#                 if password == user['password']:
#                     session['user'] = username
#                     recaptcha = RecaptchaField()
#                     return redirect(url_for('home'))
#                 else:
#                     flash("Incorrect password. Please try again.")
#             else:
#                 flash("User not found. Please register.")
#             # Stay on login form if login fails.
#             form_type = 'login'
#         elif action == 'signup':
#             first_name = request.form['first_name']
#             last_name = request.form['last_name']
#             username = request.form['username']
#             email = request.form['email']
#             password = request.form['password']
#             conn = get_db_connection()
#             try:
#                 conn.execute(
#                     "INSERT INTO users (first_name, last_name, username, email, password) VALUES (?, ?, ?, ?, ?)",
#                     (first_name, last_name, username, email, password)
#                 )
#                 conn.commit()
#                 flash("Registration successful! Please log in.")
#                 # After successful registration, show the login form.
#                 form_type = 'login'
#             except sqlite3.IntegrityError:
#                 flash("Username already exists. Please choose another.")
#                 form_type = 'signup'
#             finally:
#                 conn.close()
#     return render_template('login.html', form_type=form_type)

#     return redirect(url_for('/home'))

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles both login and sign-up in two stages.
    Stage 1: Validate credentials (login/sign-up) without reCAPTCHA.
    Stage 2: If credentials are valid, store username in session as 'pending_user'
             and re-render the page to show the reCAPTCHA widget.
    When the reCAPTCHA response is submitted, verify it and then log the user in.
    """
    form_type = request.args.get('form', 'login')  # 'login' or 'signup'
    
    # Stage 2: reCAPTCHA verification step
    if request.method == 'POST' and 'g-recaptcha-response' in request.form:
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            flash("Please complete the reCAPTCHA.")
            return redirect(url_for('index', form=form_type))
        payload = {
            'secret': RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=payload)
        result = r.json()
        if result.get("success"):
            # reCAPTCHA verified; finalize login/registration
            pending_user = session.pop('pending_user', None)
            if pending_user:
                session['user'] = pending_user
                return redirect(url_for('home'))
            else:
                flash("Session expired. Please try logging in again.")
                return redirect(url_for('index', form=form_type))
        else:
            flash("reCAPTCHA verification failed. Please try again.")
            return redirect(url_for('index', form=form_type))
    
    # Stage 1: Process credentials if reCAPTCHA is not yet present
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'login':
            username = request.form['username']
            password = request.form['password']
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            conn.close()
            if user and password == user['password']:
                # Credentials valid; store pending user and ask for reCAPTCHA
                session['pending_user'] = username
                flash("Credentials verified. Please complete the reCAPTCHA to continue.")
                return redirect(url_for('index', form='login'))
            else:
                flash("Invalid username or password.")
        elif action == 'signup':
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            try:
                conn = get_db_connection()
                conn.execute(
                    "INSERT INTO users (first_name, last_name, username, email, password) VALUES (?, ?, ?, ?, ?)",
                    (first_name, last_name, username, email, password)
                )
                conn.commit()
                conn.close()
                session['pending_user'] = username
                flash("Registration successful! Please complete the reCAPTCHA to finalize login.")
                return redirect(url_for('index', form='signup'))
            except sqlite3.IntegrityError:
                flash("Username already exists. Please choose another.")
    
    return render_template('login.html', form_type=form_type, recaptcha_site_key=RECAPTCHA_SITE_KEY)


def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

with app.app_context():
    init_db()

#  SINGLE ITEM VIEW 
@app.route("/item/<int:item_id>")
def item(item_id):
    c = get_db().cursor()
    item_from_db = c.execute("""SELECT
                    i.id, i.title, i.description, i.image
                    FROM
                    fitness AS i
                    WHERE i.id = ?""",
                    (item_id,)
    )
    row = c.fetchone()

    try:
        item = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "image": row[3]
        }
    except:
        item = {}

    if item:
        deleteItemForm = DeleteItemForm()
        return render_template("item.html", item = item, deleteItemForm = deleteItemForm, item_id=item_id)
    return redirect(url_for("home")) 

# ----------- DISPLAY ALL ITEMS -----------
@app.route("/home")
def home():
    conn = get_db()
    c = conn.cursor()

    form = ItemForm(request.args, meta={"csrf": False})

    items_from_db = c.execute("""SELECT i.id, i.title, i.description, i.image
                                 FROM fitness AS i
                                 ORDER BY i.id DESC
    """)

    fitness = []
    for row in items_from_db:
        item = {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "image": row[3]
        }
        fitness.append(item)
    return render_template ('home.html', fitness = fitness, form=form)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["IMAGE_UPLOADS"], filename)


# --- ADD NEW ITEM ------

@app.route("/exercise", methods=["GET", "POST"])
def exercise():
    if request.method == "POST":
        conn = get_db()
        c = conn.cursor()
        form = NewItemForm()
    
        c.execute("SELECT MAX(id) FROM fitness")
        max_id = c.fetchone()[0] 

        if max_id is None:
            new_id = 1
        else:
            new_id = max_id + 1
        
        if form.validate_on_submit() and form.image.validate(form, extra_validators=(FileRequired(),)):
                
            filename = save_image_upload(form.image)
            
            c.execute("""INSERT INTO fitness(id,title, description, image)
                        VALUES(?,?,?,?)""",
                        (   new_id,
                            escape(form.title.data),
                            escape(form.description.data),
                            filename
                        )
                        )

            conn.commit()
            flash("Item {} has been successfully submitted.".format(form.title.data), "success")

            return redirect(url_for("home"))
        # flash("Form validation failed.", "danger")
        conn.close()
    return render_template('exercise.html', form=NewItemForm())

def save_image_upload(image):
    format = "%Y%m%dT%H%M%S"
    now = datetime.datetime.utcnow().strftime(format)
    random_string = token_hex(2)
    filename = random_string + "_" + now + "_" + image.data.filename
    filename = secure_filename(filename)
    image.data.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
    return filename



@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename)

# -----DELETE ITEM ------
@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    print("Delete item route called!")
    conn = get_db()
    c = conn.cursor()

    item_from_db = c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
    row = c.fetchone()

    if row:
        item = {
            "id": row[0],
            "title": row[1]
        }

        c.execute("DELETE FROM fitness WHERE id = ?", (item_id,))
        conn.commit()

        flash(f"Item {item['title']} has been successfully deleted.", "success")
    else:
        flash("This item does not exist", "danger")

    return redirect(url_for("home"))

# -----EDIT ITEM ---------

@app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    with get_db() as conn:
        c = conn.cursor()
        form = EditItemForm()

        if request.method == "POST":
            if form.validate_on_submit():
                c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
                item = c.fetchone()

                if not item:
                    flash("Item not found", "error")
                    return redirect(url_for("home"))

                existing_image_filename = item[3]

                if form.image.data:
                    new_image_filename = save_image_upload(form.image)
                    # form.image.save(os.path.join(app.config["IMAGE_UPLOADS"], new_image_filename))
            
                else:
                    new_image_filename = existing_image_filename

                c.execute(
                    """
                    UPDATE fitness
                    SET title=?, description=?, image=?
                    WHERE id=?
                    """,
                    (
                        escape(form.title.data),
                        escape(form.description.data),
                        new_image_filename,
                        item_id,
                    ),
                )
                conn.commit()
                flash("Item {} has been successfully updated.".format(form.title.data), "success")
                return redirect(url_for("home"))

        c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
        item = c.fetchone()
        if not item:
            # flash("Item not found", "error")
            return redirect(url_for("home"))

        form.title.data = item[1]
        form.description.data = unescape(item[2])
        # form.image.data = item[3]

    return render_template("edit_item.html", form=form, item_id=item_id, item=item)


@app.route("/running", methods=["GET", "POST"])
def running():
    if request.method == "POST":
        distance = float(request.form.get("distance", 0.0))
        weight = float(request.form.get("weight", 0.0))
        running_activity = Running(distance, weight)
        calories_burned = running_activity.calculate_calories_burned()
        return render_template('running.html', calories_burned=calories_burned)

    return render_template('running.html')


@app.route("/walking", methods=["GET", "POST"])
def walking():
    if request.method == "POST":
        distance = float(request.form.get("distance", 0.0))
        weight = float(request.form.get("weight", 0.0))

        walking_activity = Walking(distance, weight)
        calories_burned = walking_activity.calculate_calories_burned()
        return render_template('walking.html', calories_burned=calories_burned)

    return render_template('walking.html')

@app.route("/cycling", methods=["GET", "POST"])
def cycling():
    if request.method == "POST":
        distance = float(request.form.get("distance", 0.0))
        weight = float(request.form.get("weight", 0.0))  
     
        cycling_activity = Cycling(distance, weight)
        calories_burned = cycling_activity.calculate_calories_burned()
        return render_template('cycling.html', calories_burned=calories_burned)

    return render_template('cycling.html')

def get_db():
     db = getattr(g, "_database", None)
     if db is None:
          db = g._database = sqlite3.connect("fitness.db") 
     return db

@app.teardown_appcontext
def close_connection(exception):
     db = getattr(g, "_database", None)
     if db is not None:
        db.close()
     
@app.after_request  
def add_cache_control(response):
    response.headers['Cache-Control'] = 'public, max-age=1'
    return response


if __name__ == '__main__':
    app.run(debug=True)
