from flask import Flask, render_template, request
from liquid_to_jinja import convert_liquid_to_jinja  # Importing the previously given conversion function

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    jinja_template = ""
    liquid_template = ""  # Initialize the liquid template as an empty string.

    if request.method == 'POST':
        liquid_template = request.form['liquid_template']  # Get the liquid template from form data.
        jinja_template = convert_liquid_to_jinja(liquid_template)  # Convert the Liquid template to Jinja template.

    return render_template('index.html', liquid_template=liquid_template, jinja_template=jinja_template)

if __name__ == '__main__':
    app.run(debug=True)