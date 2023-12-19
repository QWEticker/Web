from flask import Flask
import os


app = Flask(__name__, static_folder="static")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SECRET_KEY'] = 'hard to guess'
