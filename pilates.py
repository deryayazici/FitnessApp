from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('pilates.html')

@app.route('/submit-pilates-data', methods=['POST'])
def submit_data():
    
    date = request.form['date']
    duration = request.form['duration']
    intensity = request.form['intensity']
    pilates_type = request.form['pilates_type']
    exercises = request.form['exercises']
    effort = request.form['effort']
    notes = request.form['notes']
    progress = request.form['progress']

    print(f"Date: {date}, Duration: {duration}, Intensity: {intensity}, Type: {pilates_type}, Exercises: {exercises}, Effort: {effort}, Notes: {notes}, Progress: {progress}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
