import sys
from flask import Flask, render_template, request, redirect, url_for, g, send_from_directory, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from wtforms.validators import InputRequired, DataRequired, Length
from werkzeug.utils import secure_filename
import sqlite3
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"

class ItemForm(FlaskForm):
    title       = StringField("Title", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=3, max=20, message="Input must be between 3 and 20 characters long")])
    description = TextAreaField("Description", validators=[InputRequired("Input is required!"), DataRequired("Data is required!"), Length(min=5, max=500, message="Input must be between 3 and 90 characters long")])
    image       = FileField("Image")
   

class NewItemForm(ItemForm):
      submit     = SubmitField("submit")

class EditItemForm(ItemForm):
      submit     = SubmitField("Update item")

class DeleteItemForm(FlaskForm):
    submit = SubmitField("Delete item")

class FilterForm(FlaskForm):
    title  = StringField("Title")
    submit = SubmitField("Filter")

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
# -----------
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


@app.route("/running", methods=["GET","POST"])
def running():
     return render_template('running.html')


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

        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                image_filename = secure_filename(image_file.filename)
        
                image_path = os.path.join("static/uploads", image_filename)
                image_file.save(image_path)

                c.execute("""INSERT INTO fitness(id,title, description, image)
                            VALUES(?,?,?,?)""",
                            (   new_id,
                                form.title.data,
                                form.description.data,
                                image_path
                            )
                )

                print ("image path: " + image_path)
                conn.commit()
                flash("Item {} has been successfully submitted.".format(form.title.data), "success")
                conn.close()
     
                return redirect(url_for("home"))
            flash("No image file selected.", "danger")
            conn.close()
        return "No image file selected"
    return render_template('exercise.html', form=NewItemForm())

@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename)

# @app.route("/delete_item/<int:item_id>", methods=["POST"])
# def delete_item(item_id):
#     conn = get_db()
#     c = conn.cursor()

    
#     c.execute("DELETE FROM fitness WHERE id = ?", (item_id,))
#     conn.commit()
#     conn.close()

#     return redirect(url_for("home"))

@app.route("/item/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    conn = get_db()
    c = conn.cursor()

    item_from_db=c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
    row = c.fetchone()

    try:
        item = {
            "id": row[0],
            "title": row[1]
        }
    except:
        item = {}

    if item:
        c.execute("DELETE FROM fitness WHERE id = ?", (item_id,))
        conn.commit()

        flash(("Item {} has been successfully deleted.".format(item["title"]), "success", "danger"))
    else:
        flash("This item dos not exist","danger")
    return redirect(url_for("home"))

@app.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    conn = get_db()
    c = conn.cursor()
    item_from_db = c.execute("SELECT * FROM fitness WHERE id = ?", (item_id,))
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
        form = EditItemForm()
        
        if form.validate_on_submit():
            image_path = item["image"]  # Default to the existing image path

            if 'image' in request.files:
                image_file = request.files['image']
                if image_file.filename:
                    image_filename = secure_filename(image_file.filename)
                    image_path = os.path.join("static/uploads", image_filename)
                    image_file.save(image_path)

            c.execute("""UPDATE fitness SET
                        title = ?, description = ?, image = ?
                        WHERE id = ?""",
                        (form.title.data, form.description.data, image_path, item_id)
            )
            conn.commit()
            flash("Item {} has been successfully updated.".format(form.title.data), "success")
            return redirect(url_for("item", item_id=item_id))
        
        form.title.data = item["title"]
        form.description.data = item["description"]

        return render_template("edit_item.html", item=item, form=form, item_id=item_id)
    else:
        flash("Item does not exist", "danger")
        return redirect(url_for("home"))

        

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
