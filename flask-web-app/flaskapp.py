from flask import Flask, jsonify, render_template, make_response, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, emit
from time import time
from random import random
import json

# define the flask app
app = Flask(__name__)

# define the socket.io app
socketio = SocketIO(app)

# config the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = '<CONNECTION STRING TO YOUR MYSQL DB>'
db = SQLAlchemy(app)

# define a User model used by sqlalchemy to fetch data from the mysql db
# the database currently holds just one table named 'users'. This table
# has 3 columns - uid, name, and avatar (url to the bmp)
class User(db.Model):
    __tablename__ = 'users'
    uid = db.Column('uid', db.Integer, primary_key=True)
    name = db.Column('name', db.String(50), unique=True)
    avatar = db.Column('avatar', db.String(100))

    def to_json(self):
        return {
            'uid' : self.uid,
            'name' : self.name,
            'avatar' : self.avatar
        }

@app.route('/')
def displayLiveChart():
    return render_template('index.html', data='test')

@app.route('/users/', methods=['GET'])
def fetchAllUsers():
    return jsonify({'users': [s.to_json() for s in User.query.all()]})

@app.route('/users/<string:uid>', methods=['GET'])
def fetchUser(uid):
    return jsonify({'user': User.query.get(uid).to_json()})

@app.route('/racingLogEntry', methods=['POST'])
def postRacingLogEntry():
    socketio.emit('log',  request.json, namespace='/chart')  
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

if __name__ == '__main__':
    socketio.run(app)
