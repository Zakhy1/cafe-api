from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configuration

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqlconnector://root:@localhost/prj"
db = SQLAlchemy()
db.init_app(app)


# Models

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    surname = db.Column(db.String(100))
    patronymic = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(20), unique=True)
    login = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(500), nullable=False)
    photo_file = db.Column(db.String(255))
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
    shift_id = db.Column(db.Integer, db.ForeignKey("shifts.id"))
    token = db.Column(db.String(500))

    def __repr__(self):
        return f"User: {self.login}"


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(100))


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_table = db.Column(db.String(100))
    date_time = db.Column(db.DateTime, default=datetime.utcnow())
    price = db.Column(db.Float)
    status_id = db.Column(db.Integer, db.ForeignKey("order_statuses.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    def __repr__(self):
        return f"Order: №{self.id}"


class OrderStatuses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(100))

    def __repr__(self):
        return f"OrderStatus: {self.status_name}"


class OrderItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"))
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"))
    quantity = db.Column(db.Integer)

    def __repr__(self):
        return f"User: {self.id}"


class MenuItems(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Float)

    def __repr__(self):
        return f"MenuItem: {self.name}"


class Shifts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    active = db.Column(db.Boolean)

    def __repr__(self):
        return f"Shift: {self.start_time} - {self.end_time}"


# functions for models

def migrate():
    """
    To migrate() function first deletes all tables in the database,
    then creates them based on the described models
    :return:
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
