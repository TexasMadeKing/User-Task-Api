from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from werkzeug.security import generate_password_hash
import os
from faker import Faker
import requests


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
bcrypt = Bcrypt(app)
CORS(app)
fake = Faker()



class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    task = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __init__(self, task, description, user_id):
        self.task = task
        self.description = description
        self.user_id = user_id

class TaskSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Task
        include_fk = True


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)

    def __init__(self, username, password, email):
        self.username = username
        self.password = password
        self.email = email

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

user_schema = UserSchema()
multi_user_schema = UserSchema(many=True)
task_schema = TaskSchema()
multi_task_schema = TaskSchema(many=True)


#  Add Endpoints Here

@app.route("/user/add", methods=["POST"])
def add_user():
    if request.content_type != "application/json":
        return jsonify("Error Adding User Enter AS type JSON!")

    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")
    email = post_data.get("email")

    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    new_record = User(username=username, password=pw_hash, email=email)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(user_schema.dump(new_record))


#  Verification Endpoint
@app.route('/user/verify', methods=["POST"])
def verification():
    if request.content_type != "application/json":
        return jsonify("Error Improper Validation Credintials!")
    
    post_data = request.get_json()
    username = post_data.get("username")
    password = post_data.get("password")

    user = db.session.query(User).filter(User.username == username).first()

    if user is None:
        return jsonify("User could not be Verified")

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify("User could not be Verified")

    return jsonify("User Verified")


#  Get All Users
@app.route("/user/get", methods=["GET"])
def get_users():
    all_users = db.session.query(User).all()
    return jsonify(multi_user_schema.dump(all_users))

#  Delete User EndPoint

@app.route('/user/delete/<id>', methods=["DELETE"])
def user_delete(id):
    delete_user = db.session.query(User).filter(User.id == id).first()
    db.session.delete(delete_user)
    db.session.commit()
    return jsonify(" Another one Bites the Dust!")


#  Update Username/Email   

@app.route('/user/update/<id>', methods=["PUT"])
def update_usermail(id):
    if request.content_type != "application/json":
        return jsonify("JSON Needed or no Coookies for you!")
    
    put_data = request.get_json()
    username = put_data.get("username")
    email = put_data.get("email")

    usermail_update = db.session.query(User).filter(User.id == id).first()

    if username != None:
        usermail_update.username = username
    if email != None:
        usermail_update.email = email
    
    db.session.commit()
    return jsonify(user_schema.dump(usermail_update))

# Password Update
@app.route('/user/pw/<id>', methods=["PUT"])
def pw_update(id):
    if request.content_type != "application/json":
        return jsonify("JSON JSon JSoN")
    
    password = request.get_json().get("password")
    user = db.session.query(User).filter(User.id == id).first()
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    user.password = pw_hash

    db.session.commit()
    return jsonify(user_schema.dump(user))


#  Task Endpoints
@app.route("/task/add", methods=["POST"])
def add_task():
    if request.content_type != "application/json":
        return jsonify("Error Adding Task Enter AS type JSON!")

    post_data = request.get_json()
    task = post_data.get("task")
    description = post_data.get("description")
    user_id = post_data.get("user_id")

    new_record = Task(task=task, description=description, user_id=user_id)
    db.session.add(new_record)
    db.session.commit()

    return jsonify(task_schema.dump(new_record))

#  Get All Tasks
@app.route("/task/get", methods=["GET"])
def get_tasks():
    all_tasks = db.session.query(Task).all()
    return jsonify(multi_task_schema.dump(all_tasks))

#  Delete Task EndPoint
@app.route('/task/delete/<id>', methods=["DELETE"])
def task_delete(id):
    delete_task = db.session.query(Task).filter(Task.id == id).first()
    db.session.delete(delete_task)
    db.session.commit()
    return jsonify("Task Deleted!")

#  Update Task EndPoint
@app.route('/task/update/<id>', methods=["PUT"])
def update_task(id):
    if request.content_type != "application/json":
        return jsonify("JSON Needed or no Coookies for you!")
    
    put_data = request.get_json()
    task = put_data.get("task")
    description = put_data.get("description")

    task_update = db.session.query(Task).filter(Task.id == id).first()

    if task != None:
        task_update.task = task
    if description != None:
        task_update.description = description
    
    db.session.commit()
    return jsonify(task_schema.dump(task_update))

@app.route('/print-endpoints', methods=["GET"])
def print_endpoints_route():
    print_endpoints()
    return "Endpoints printed in the console."

def add_fake_users(count=10):
    with app.app_context():  # Create an application context
        for _ in range(count):
            username = fake.user_name()
            password = fake.password(length=10)
            email = fake.email()

            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=pw_hash, email=email)
            db.session.add(new_user)
        db.session.commit()

def add_fake_tasks(count=10):
    with app.app_context():  # Create an application context
        users = User.query.all()  # Use User.query within the application context
        if not users:
            print("No users found! Please add some users first.")
            return

        for _ in range(count):
            task = fake.sentence(nb_words=5)
            description = fake.sentence(nb_words=15)
            user_id = fake.random_element(elements=[user.id for user in users])

            new_task = Task(task=task, description=description, user_id=user_id)
            db.session.add(new_task)
        db.session.commit()

def print_endpoints():
    endpoints = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            endpoints.append({
                'endpoint': rule.endpoint,
                'methods': ','.join(rule.methods),
                'path': str(rule)
            })
    print("API Endpoints:")
    for endpoint in endpoints:
        print(f"Endpoint: {endpoint['endpoint']}, Methods: {endpoint['methods']}, Path: {endpoint['path']}")



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # add_fake_users(10)  # Add fake users within the application context
    # Uncomment the following line to add fake tasks
    # add_fake_tasks(10)
    
    print_endpoints()  # Print endpoints before starting the server
    app.run()
