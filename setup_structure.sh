#!/bin/bash

# Shell script to create folder structure for Sydney Flowers Express project

# Create root project directory
mkdir -p sydney-flowers-express2

# Create key folders
mkdir -p sydney-flowers-express2/templates
mkdir -p sydney-flowers-express2/static/css
mkdir -p sydney-flowers-express2/static/js
mkdir -p sydney-flowers-express2/static/images

# Create empty placeholder files (not actual content)
touch sydney-flowers-express2/app.py
touch sydney-flowers-express2/requirements.txt
touch sydney-flowers-express2/README.md
touch sydney-flowers-express2/users.db

# Placeholder HTML templates
touch sydney-flowers-express2/templates/index.html
touch sydney-flowers-express2/templates/login.html
touch sydney-flowers-express2/templates/register.html
touch sydney-flowers-express2/templates/catalogue.html
touch sydney-flowers-express2/templates/cart.html
touch sydney-flowers-express2/templates/checkout.html
touch sydney-flowers-express2/templates/admin_dashboard.html

# Placeholder static files
touch sydney-flowers-express2/static/css/style.css
touch sydney-flowers-express2/static/js/main.js

echo "✅ Folder structure created (content not included)."
