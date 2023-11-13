import sys
from flask import Flask, render_template, request, redirect, url_for, g, send_from_directory, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import InputRequired, DataRequired, Length
from werkzeug.utils import secure_filename
import sqlite3
import os
import datetime
from secrets import token_hex

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["jpeg", "jpg", "png"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["IMAGE_UPLOADS"] = os.path.join(basedir, "uploads")

class ItemForm(FlaskForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=3, max=20, message="Input must be between 3 and 20 characters long")])
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=500, message="Input must be between 3 and 90 characters long")])
    image       = FileField("Image", validators=[FileRequired(), FileAllowed(app.config["ALLOWED_IMAGE_EXTENSIONS"], "Images only!")])
   

class NewItemForm(ItemForm):
      submit     = SubmitField("submit")

class EditItemForm(ItemForm):
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

    # form = FilterForm(request.args, meta={"csrf": False})

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
    return render_template ('home.html', fitness = fitness)

@app.route("/uploads/<filename>")
def uploads(filename):
    return send_from_directory(app.config["IMAGE_UPLOADS"], filename)


# --- ADD NEW ITEM ------

# def generate_unique_filename(original_filename):
#     format = "%Y%m%dT%H%M%S"
#     now = datetime.datetime.utcnow().strftime(format)
#     random_string = token_hex(2)
#     filename = random_string + "_" + now + "_" + secure_filename(original_filename)
#     return filename

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
            
            if form.validate_on_submit():
                    
                    filename = save_image_upload(form.image)
                    
                    

                    c.execute("""INSERT INTO fitness(id,title, description, image)
                                VALUES(?,?,?,?)""",
                                (   new_id,
                                    form.title.data,
                                    form.description.data,
                                    filename
                                )
                    )

                    conn.commit()
                    flash("Item {} has been successfully submitted.".format(form.title.data), "success")
        
                    return redirect(url_for("home"))
            flash("No image file selected.", "danger")
            conn.close()
            return "No image file selected"
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
# def delete_item(item_id):
#     conn = get_db()
#     c = conn.cursor()

#     item_from_db=c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
#     row = c.fetchone()

#     try:
#         item = {
#             "id": row[0],
#             "title": row[1]
#         }
#     except:
#         item = {}

#     if item:
#         c.execute("DELETE FROM fitness WHERE id = ?", (item_id,))
#         conn.commit()

#         flash(("Item {} has been successfully deleted.".format(item["title"]), "success", "danger"))
#     else:
#         flash("This item dos not exist","danger")
#     return redirect(url_for("home"))
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

# @app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
# def edit_item(item_id):
#     conn = get_db()
#     c = conn.cursor()
#     item_from_db = c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
#     row = c.fetchone()

#     try:
#         item = {
#             "id": row[0],
#             "title": row[1],
#             "description": row[2],
#             "image": row[3]
#         }
#     except:
#         item = {}

#     if item:
#         form = EditItemForm()
        
#         if form.validate_on_submit():
#             image_path = item["image"]  # Default to the existing image path

#             if 'image' in request.files:
#                 image_file = request.files['image']
#                 if image_file.filename:
#                     image_filename = secure_filename(image_file.filename)
#                     image_path = os.path.join("static/uploads", image_filename)
#                     image_file.save(image_path)

#             c.execute("""UPDATE fitness SET
#                         title = ?, description = ?, image = ?
#                         WHERE id = ?""",
#                         (form.title.data, form.description.data, image_path, item_id)
#             )
#             conn.commit()
#             flash("Item {} has been successfully updated.".format(form.title.data), "success")
#             return redirect(url_for("item", item_id=item_id))
        
#         form.title.data = item["title"]
#         form.description.data = item["description"]

#         return render_template("edit_item.html", item=item, form=form, item_id=item_id)
#     else:
#         flash("Item does not exist", "danger")
#         return redirect(url_for("home"))



# @app.route("/edit_item/<int:item_id>", methods=["GET", "POST"])
# def edit_item(item_id):
#     conn = get_db()
#     c = conn.cursor()
#     form = EditItemForm()  # Use your EditItemForm here

#     if request.method == "POST" and form.validate_on_submit():
#         # Get existing item data
#         c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
#         item = c.fetchone()

#         if item:
#             existing_image_filename = item["image"]
#             # Handle the image update if a new image is provided
#             if form.image.data:
#                 # Save the new image with a new filename
#                 new_image_filename = save_image_upload(form.image.data.filename)
#                 form.image.data.save(os.path.join(app.config["IMAGE_UPLOADS"], new_image_filename))
#             else:
#                 # No new image provided, keep the existing image filename
#                 new_image_filename = existing_image_filename

#             # Update the item in the database
#             c.execute(
#                 """
#                 UPDATE fitness
#                 SET title=?, description=?, image=?
#                 WHERE id=?
#                 """,
#                 (
#                     form.title.data,
#                     form.description.data,
#                     new_image_filename,
#                     item_id,
#                 ),
#             )
#             conn.commit()
#             flash("Item {} has been successfully updated.".format(form.title.data), "success")
#             conn.close()
#             return redirect(url_for("home"))

#     # If it's a GET request or form validation fails, populate the form with existing data
#     c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
#     item = c.fetchone()
#     if item:
#         form.title.data = item[1]
#         form.description.data = item[2]
#         # Pass the existing image filename to the form to display the current image
#         form.image.data = item[3]

#     conn.close()
#     return render_template("edit_item.html", form=form, item_id=item_id)

from flask import Flask, render_template, request, redirect, url_for, flash
import os
from your_module import get_db, EditItemForm, save_image_upload

app = Flask(__name__)

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

                existing_image_filename = item["image"]

                if form.image.data and form.image.data.filename:
                    new_image_filename = save_image_upload(form.image.data.filename)
                    form.image.data.save(os.path.join(app.config["IMAGE_UPLOADS"], new_image_filename))
                else:
                    new_image_filename = existing_image_filename

                c.execute(
                    """
                    UPDATE fitness
                    SET title=?, description=?, image=?
                    WHERE id=?
                    """,
                    (
                        form.title.data,
                        form.description.data,
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
            flash("Item not found", "error")
            return redirect(url_for("home"))

        form.title.data = item[1]
        form.description.data = item[2]
        form.image.data = item[3]

    return render_template("edit_item.html", form=form, item_id=item_id)




@app.route("/running", methods=["GET","POST"])
def running():
     return render_template('running.html')        

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
