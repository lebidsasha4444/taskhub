import os

from flask import Flask

app = Flask(__name__)
app.run(debug=os.getenv("DEBUG"))
