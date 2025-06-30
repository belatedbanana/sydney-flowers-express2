# Sydney Flowers Express

Sydney Flowers Express is a modern web application for ordering, customising, and managing flower bouquets, designed for both individual customers and florists. The app features a beautiful, mobile-friendly interface, secure user authentication, an admin dashboard, and a persistent review system.

## Features

- 🌸 **Browse and order bouquets** from a curated catalogue
- 🎨 **Custom bouquet builder** with live preview and pricing
- 🛒 **Shopping cart** and secure checkout
- 👤 **User registration and login** with password hashing and XSS protection
- 📝 **Customer reviews** with live character count and moderation
- 🛠️ **Admin dashboard** for managing users and orders
- 📊 **Top-selling flowers** and sales statistics
- 💌 **Newsletter signup** with confetti animation
- 🔒 **Input validation and sanitisation** throughout

## Tech Stack

- Python 3 & Flask
- SQLAlchemy (SQLite database)
- Bootstrap 5 (Minty theme) & Bootstrap Icons
- Jinja2 templates
- JavaScript (for interactivity and validation)

## Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/belatedbanana/sydney-flowers-express2.git
   cd sydney-flowers-express2
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   - The app uses SQLite by default.
   - To initialise the schema, run:
     ```sh
     flask shell
     >>> from app import db
     >>> db.create_all()
     >>> exit()
     ```
   - The app seeds demo reviews automatically on first run.

4. **Run the app:**
   ```sh
   flask run
   ```

5. **Access the app:**
   - Open [http://localhost:5000](http://localhost:5000) in your browser.

## File Structure

- `app.py` — Main Flask application
- `templates/` — HTML templates (Jinja2)
- `static/` — CSS, JS, images
- `database/users.db` — SQLite database file
- `database/schema.sql` — (Optional) SQL schema definition

## Security

- All user input is validated and escaped to prevent XSS.
- Passwords are hashed using Werkzeug.
- Admin routes are protected with decorators.

## Credits

- Bootswatch Minty theme
- Bootstrap Icons
- [canvas-confetti](https://www.npmjs.com/package/canvas-confetti) for newsletter animation

---

*Sydney Flowers Express — Fast, fresh, and fabulous flowers for every