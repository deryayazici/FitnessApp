import sys
from typing import Any
from flask import Flask, render_template, request, redirect, url_for, g, send_from_directory, flash
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


basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMAGE_UPLOADS"] = os.path.join(basedir, "uploads")

app.config["TESTING"] = True

app.config["RECAPTCHA_PUBLIC_KEY"] = "6Lct3hApAAAAAF3shHdCcXlLhzxvJiWbT2rH56XW"
app.config["RECAPTCHA_PRIVATE_KEY"] = "6Lct3hApAAAAALPoW_BXUgEtj5rKurAyFGb-6mp9"

class ItemForm(FlaskForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=3, max=20, message="Input must be between 3 and 20 characters long")])
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=500, message="Input must be between 3 and 90 characters long")])
    image       = FileField("Image", validators=[FileAllowed(app.config["ALLOWED_IMAGE_EXTENSIONS"], "Images only!")])
    
# class BelongsToOtherFieldOption:
#     def __init__(self, table, belongs_to, foreign_key=None, message=None):
#         if not table:
#             raise AttributeError("""
#             BelongsToOtherFieldOption validator needs the table parameter
#             """)
#         if not belongs_to:
#             raise AttributeError("""
#             BelongsToOtherFieldOption validator needs the belongs_to parameter
#             """)
#         self.table = table
#         self.belongs_to = belongs_to

#         if not foreign_key:
#             foreign_key = belongs_to + "_id"
#         if not message:
#             message = "Chosen option is not valid"
        
#         self.foreign_key = foreign_key
#         self.message = message

#     def __call__(self, form, field):
#         c = get_db().cursor()
#         try:
#             c.execute(""" SELECT COUNT(*) FROM {}
#                       WHERE id = ? AND {} = ?""".format(
#                            self.table,
#                            self.foreign_key 
#                       ),
#                       (field.data, getattr(form, self.belongs_to).data)
#                   )
#         except Exception as e:
#             raise AttributeError("""
#             Passed parameters are not correct.{}
#             """.format(e))
#         exists = c.fetchone()[0]
#         if not exists:
#             raise ValidationError(self.message)
        
class NewItemForm(ItemForm):
      recaptcha = RecaptchaField()
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

# ---- SINGLE ITEM VIEW ------
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
@app.route("/")
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



# def calculate_calories_burned(distance_miles, weight_pounds):

#     distance_km = distance_miles * 1.60934
#     weight_kg = weight_pounds * 0.453592
    
#     calories_burned_per_km = 0.75 * weight_kg 
#     total_calories_burned = calories_burned_per_km * distance_km
#     return int(total_calories_burned)

# @app.route("/running", methods=["GET", "POST"])
# def running():
#     if request.method == "POST":
#         distance = float(request.form.get("distance", 0.0)) 
#         weight = request.form.get("weight") 
        
#         if weight and weight.strip(): 
#             weight = float(weight)
#             calories_burned = calculate_calories_burned(distance, weight)
#             return render_template('running.html', calories_burned=calories_burned)
        
#         error_message = "Please enter a valid weight."
#         return render_template('running.html', error=error_message)
    
#     return render_template('running.html')
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

    #     if weight and weight.strip():
    #         weight = float(weight)
    #         calories_burned = calculate_calories_burned_walking(distance, weight)
    #         return render_template('walking.html', calories_burned=calories_burned)

    #     error_message = "Please enter a valid weight."
    #     return render_template('walking.html', error=error_message)

    # return render_template('walking.html')
  

# def calculate_calories_burned_walking(distance, weight):
#     distance_km = distance_miles * 1.60934
#     weight_kg = weight_pounds * 0.453592
    
#     calories_burned_per_km = 0.5 * weight_kg
#     total_calories_burned = calories_burned_per_km * distance_km
#     return int(total_calories_burned)

@app.route("/cycling", methods=["GET", "POST"])
def cycling():
    if request.method == "POST":
        distance = float(request.form.get("distance", 0.0))
        weight = float(request.form.get("weight", 0.0))  
     
        cycling_activity = Cycling(distance, weight)
        calories_burned = cycling_activity.calculate_calories_burned()
        return render_template('cycling.html', calories_burned=calories_burned)

    return render_template('cycling.html')



    #     if weight and weight.strip():
    #         weight = float(weight)
    #         calories_burned = calculate_calories_burned_cycling(distance, weight)
    #         return render_template('cycling.html', calories_burned=calories_burned)

    #     error_message = "Please enter a valid weight."
    #     return render_template('cycling.html', error=error_message)

    # return render_template('cycling.html')

# def calculate_calories_burned_cycling(distance_miles, weight_pounds):
#     distance_km = distance_miles * 1.60934
#     weight_kg = weight_pounds * 0.453592

#     average_speed_kmh = 15
#     calories_burned_per_hour_per_kg = 8.5
#     total_hours = distance_km / average_speed_kmh

#     total_calories_burned = calories_burned_per_hour_per_kg * weight_kg * total_hours

#     return int(total_calories_burned)



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
