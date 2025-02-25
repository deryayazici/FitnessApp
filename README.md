# FitnessApp
FitnessApp is a Flask-based web application designed for fitness enthusiasts. 

## Technologies Used
-**Python**: Core programming language.

-**Flask**: Web framework for handling routes and sessions.

-**SQLite**: Lightweight database for storing user and fitness data.

-**HTML/CSS**: Frontend design.

## Features Available

- **User Authentication**
  - Login with username and password.
  - Sign-up with additional fields.
- **Dynamic Fitness Content**
   - Displays fitness items such as title, description, and images.
   - Automatically updates as new content is added to the database.
- **Security**
  - Google reCAPTCHA integration to prevent bot sign-ups and logins.
- **Database Integration**
   - SQLite is used to store user data and fitness items.
- **Responsive Interface**
  - Clean, easy-to-use interface for accessing all app features.

    
## Prerequisites 
- Python 3.7 or higher
- pip (Python package installer)

## Installation 

1. **Clone the repository:**

   ```bash
   git clone https://github.com/deryayazici/FitnessApp.git
   cd FitnessApp
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On MacOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ``` bash
   pip install -r requirements.txt
   ```

## Configuration

**Google reCAPTCHA Setup**
1. **Register Your Site:**
   - Visit the [Google reCAPTCHA Admin Console](https://www.google.com/recaptcha) and click **Register a new site.**
   - Choose the desired reCAPTCHA type.
   - Add ```localhost``` as an allowed domain and submit to obtain your keys.
  
2. **Configure Your App:**
   In ```app.py```, update the following variables with your keys:
   ``` python
   RECAPTCHA_SITE_KEY = "your_site_key_here"
   RECAPTCHA_SECRET_KEY = "your_secret_key_here"
   ```

## Database
- The app uses SQLite. Tables are created automatically on the first run.

## Running the Application
```bash
python app.py
```
