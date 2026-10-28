from flask import Flask
import os
app = Flask(__name__)
app.run(debug=os.getenv("DEBUG"))
