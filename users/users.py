from secrets import token_hex

from flask import Blueprint, request, jsonify, abort
from flask_httpauth import HTTPTokenAuth

from models import Users, db

users = Blueprint("users", __name__)

# users part
auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token):  # If token exist -> returns token
    if Users.query.filter(Users.token == token).first_or_404():
        return token
    else:
        abort(401)


@auth.get_user_roles
def get_user_roles(user):  # returns by token a role id
    current_user = Users.query.filter(Users.token == user).first_or_404()
    if current_user:
        return current_user.role_id


# main part
@users.route("/api-cafe/register", methods=["POST"])
@auth.login_required(role=1)
def register():  # register new user by FormData TODO fix register
    name = request.form["name"]
    surname = request.form["surname"]
    patronymic = request.form["patronymic"]
    email = request.form["email"]
    phone_number = request.form["phone_number"]
    login = request.form["login"]
    password = request.form["password"]
    role_id = request.form["role_id"]

    new_user = Users(
        name=name, surname=surname, patronymic=patronymic,
        email=email, phone_number=phone_number, login=login,
        password=password, role_id=role_id
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "user was registered",
                    "current_user": auth.current_user()})


@users.route("/api-cafe/user/<user_id>/to-dismiss")
@auth.login_required(role=1)
def dismiss(user_id):
    curr_user = Users.query.filter(Users.id == user_id).first_or_404()
    curr_user.role_id = 4  # that role id means dismissed user
    db.session.add(curr_user)
    db.session.commit()
    return jsonify({"data": f"User {curr_user.name} was dismissed"})


@users.route("/api-cafe/login", methods=["POST"])
def get_token():  # generates a token when login by login and password is successful
    login = request.json["login"]
    password = request.json["password"]
    logged_user = Users.query.filter(Users.login == login,
                                     Users.password == password).first_or_404()
    if logged_user:
        logged_user.token = token_hex(15)
        db.session.add(logged_user)
        db.session.commit()
        return jsonify({"token": logged_user.token})
    return jsonify({
        "error": {
            "code": 401,
            "message": "Authentication failed"}
    }), 401


@users.route("/api-cafe/logout", methods=["GET"])
@auth.login_required
def logout():  # deletes user token, which used by authorisation
    token = auth.current_user()
    logged_user = Users.query.filter(Users.token == token).first_or_404()
    logged_user.token = None
    db.session.commit()
    return jsonify({"message": "token was deleted successful"})


@users.errorhandler(403)
def err_403():  # custom error handler
    return jsonify({
        "error": {
            "code": 403,
            "message": "Forbidden for you",
        }
    }), 403


@users.route("/api-cafe/user", methods=["GET"])
@auth.login_required(role=1)
def user():  # returns list of dicts, which contains users info
    all_users = Users.query.all()
    result = []
    for u in all_users:
        user_dict = {
            "id": u.id, "name": u.name, "surname": u.surname,
            "patronymic": u.patronymic, "email": u.email, "phone": u.phone_number,
            "login": u.login
        }
        result.append(user_dict)
    return jsonify({"data": result})


@users.route("/api-cafe/user/<user_id>", methods=["GET"])
@auth.login_required(role=1)
def get_user(user_id):  # returns a dict which contains info about user
    curr_user = Users.query.filter(Users.id == user_id).first_or_404()

    user_dict = {
        "id": curr_user.id, "name": curr_user.name, "surname": curr_user.surname,
        "patronymic": curr_user.patronymic, "email": curr_user.email,
        "phone": curr_user.phone_number,
        "login": curr_user.login
    }
    return jsonify({"data": user_dict})
