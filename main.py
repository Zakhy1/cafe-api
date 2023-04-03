from secrets import token_hex
from flask import jsonify, request, abort
from flask_httpauth import HTTPTokenAuth

from models import app, Users, db

auth = HTTPTokenAuth(scheme='Bearer')


# To all other I don't know how to initialise app object in this file
# because I had cyclical import error


@app.route("/api/v1.0/register", methods=["POST"])
@auth.login_required(role=1)
def register():
    try:
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
    except:  # I don't know what error to expect
        db.session.rollback()
        return jsonify({"error": "by adding to DB"})


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


@app.route("/api/v1.0/login", methods=["POST"])
def get_token():  # generates a token when login by login and password is successful
    login = request.form["login"]
    password = request.form["password"]
    user = Users.query.filter(Users.login == login, Users.password == password).first_or_404()
    if user:
        user.token = token_hex(15)
        db.session.add(user)
        db.session.commit()
        return jsonify({"token": user.token})
    return jsonify({
        "error": {
            "code": 401,
            "message": "Authentication failed"}
    }), 401


# TODO test this shit
@app.route("/api/v1.0/logout")
@auth.login_required
def logout():
    token = auth.current_user()
    user = Users.query.filter(Users.token == token).first()
    db.session.delete(user)
    db.session.commit()


@app.errorhandler(403)
def err_403():
    return jsonify({
        "error": {
            "code": 403,
            "message": "Forbidden for you",
        }
    }), 403


@app.route("/api/v1.0/user")
@auth.login_required(role=1)
def user():
    users = Users.query.all()
    # TODO find a way to show all users
    return jsonify()


if __name__ == "__main__":
    app.run(debug=True)
