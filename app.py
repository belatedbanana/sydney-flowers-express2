from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/catalogue')
def catalogue():
    return render_template('catalogue.html')

@app.route('/customise', methods=['GET', 'POST'])
def customise():
    if request.method == 'POST':
        flower_type = request.form['flowerType']
        colour = request.form['colourScheme']
        message = request.form['message']
        size = request.form['size']

        # TODO: process/store the data, or show confirmation
        return render_template('customise_confirmation.html', 
                               flower_type=flower_type, 
                               colour=colour,
                               message=message,
                               size=size)

    return render_template('customise.html')

if __name__ == '__main__':
    app.run(debug=True)
