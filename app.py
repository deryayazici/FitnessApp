import sys
from flask import Flask, render_template, request, redirect, url_for, g, send_from_directory, flash
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField
from werkzeug.utils import secure_filename
import sqlite3
import os


app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"

class NewItemForm(FlaskForm):
    title       = StringField("Title")
    description = TextAreaField("Description")
    image       = FileField("Image")
    submit      = SubmitField("submit")
 

@app.route("/")
def home():
    conn = get_db()
    c = conn.cursor()

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
                                form.image.data
                            )
                )

                print ("image path: " + image_path)
                conn.commit()
                flash("Item {} has been successfully submitted.".format(request.form.get("title")), "success")
                conn.close()
     
                return redirect(url_for("home"))
            return "No image file selected"
        return render_template('exercise.html', form=form)
    return render_template('exercise.html', form=NewItemForm())

@app.route('/static/uploads/<filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename)

@app.route("/delete_item/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    conn = get_db()
    c = conn.cursor()

    
    c.execute("DELETE FROM fitness WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

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
static/images/swimming.jpg