from datetime import datetime
from secrets import token_hex

from flask import jsonify, request, abort
from flask_httpauth import HTTPTokenAuth

from models import app, db, Shifts, Orders, Users

auth = HTTPTokenAuth(scheme='Bearer')


# To all other I don't know how to initialise app object in this file
# because I had cyclical import error


# auth part

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
@app.route("/api-cafe/register", methods=["POST"])
@auth.login_required(role=1)
def register():  # register new user by FormData
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
    # except:  # I don't know what error to expect
    #     db.session.rollback()
    #     return jsonify({"error": "by adding to DB"})


@app.route("/api-cafe/user/<user_id>/to-dismiss")
@auth.login_required(role=1)
def dismiss(user_id):
    curr_user = Users.query.filter(Users.id == user_id).first_or_404()
    curr_user.role_id = 4  # that role id means dismissed user
    db.session.add(curr_user)
    db.session.commit()
    return jsonify({"data": f"User {curr_user.name} was dismissed"})


@app.route("/api-cafe/login", methods=["POST"])
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


@app.route("/api-cafe/logout", methods=["GET"])
@auth.login_required
def logout():  # deletes user token, which used by authorisation
    token = auth.current_user()
    logged_user = Users.query.filter(Users.token == token).first_or_404()
    logged_user.token = None
    db.session.commit()
    return jsonify({"message": "token was deleted successful"})


@app.errorhandler(403)
def err_403():  # custom error handler
    return jsonify({
        "error": {
            "code": 403,
            "message": "Forbidden for you",
        }
    }), 403


@app.route("/api-cafe/user", methods=["GET"])
@auth.login_required(role=1)
def user():  # returns list of dicts, which contains users info
    users = Users.query.all()
    result = []
    for u in users:
        user_dict = {
            "id": u.id, "name": u.name, "surname": u.surname,
            "patronymic": u.patronymic, "email": u.email, "phone": u.phone_number,
            "login": u.login
        }
        result.append(user_dict)
    return jsonify({"data": result})


@app.route("/api-cafe/user/<user_id>", methods=["GET"])
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


def convert_to_date(time):
    """
    converts XXXX-XX-XX XX:XX datetime to pythonic date object
    :param time:
    :return: datetime object
    """
    split_time = time.split()
    tuple_time = split_time[0].split("-"), split_time[1].split(":")
    res = []

    for i in tuple_time:
        for j in i:
            res.append(int(j))

    return datetime(res[0], res[1], res[2], res[3], res[4])


def compare_date(start_time, end_time):
    return True if start_time < end_time else False


@app.route("/api-cafe/work-shift", methods=["POST"])
@auth.login_required(role=1)
def work_shift():  # this func for creating new work-shifts
    start_time = request.json["start"]
    end_time = request.json["end"]

    start = convert_to_date(start_time)
    end = convert_to_date(end_time)

    if not compare_date(start, end):
        return jsonify({"error": {
            "code": 422,
            "message": "Validation error",
            "errors": {
                "date": "time fields incorrect"
            }}})

    new_work_shift = Shifts(
        start_time=start.strftime("%y-%m-%d %H:%m"),
        end_time=end.strftime("%y-%m-%d %H:%m"),
        active=False,
    )
    db.session.add(new_work_shift)
    db.session.commit()

    return jsonify({
        "work_shift_id": new_work_shift.id,
        "start_time": new_work_shift.start_time.strftime("%y-%m-%d %H:%m"),
        "end_time": new_work_shift.end_time.strftime("%y-%m-%d %H:%m"),
    })


@app.route("/api-cafe/work-shift/<shift_id>/open", methods=["GET"])
@auth.login_required(role=1)
def start_work_shift(shift_id):
    shift = Shifts.query.filter(Shifts.id == shift_id).first_or_404()
    if shift.active:
        return jsonify({"error": {
            "code": 403,
            "message": "Forbidden. There are open shifts!"
        }})

    shift.active = True
    db.session.add(shift)
    db.session.commit()
    return jsonify({"data": {
        "id": shift_id,
        "start": shift.start_time.strftime("%y-%m-%d %H:%m"),
        "end": shift.end_time.strftime("%y-%m-%d %H:%m"),
        "active": shift.active,
    }})


@app.route("/api-cafe/work-shift/<shift_id>/close")
@auth.login_required(role=1)
def end_work_shift(shift_id):
    current_shift = Shifts.query.filter(Shifts.id == shift_id).first_or_404()
    if not current_shift.active:
        return jsonify({"error": {
            "code": 403,
            "message": "Forbidden. The shift is already closed!"
        }
        }), 403
    current_shift.active = False
    db.session.add(current_shift)
    db.session.commit()

    return jsonify({"data": {
        "id": shift_id,
        "start": current_shift.start_time.strftime("%y-%m-%d %H:%m"),
        "end": current_shift.end_time.strftime("%y-%m-%d %H:%m"),
        "active": current_shift.active,
    }})


@app.route("/api-cafe/work-shift/<shift_id>/user", methods=["POST"])
@auth.login_required(role=1)
def add_user_to_shift(shift_id):
    user_id = request.json["user_id"]
    current_user = Users.query.filter(Users.id == user_id).first_or_404()
    current_user.shift_id = shift_id
    db.session.add(current_user)
    db.session.commit()
    return jsonify({
        "data": {
            "id_user": user_id,
            "status": "added"
        }
    }
    )


@app.route("/api-cafe/order", methods=["POST"])
@auth.login_required(role=3)
def create_order():
    shift_id = request.json["work_shift_id"]
    table_id = request.json["table_id"]
    order_id = len(Orders.query.all()) + 1
    number_of_persons = request.json["number_of_person"]

    cur_user = Users.query.filter(Users.token == auth.current_user()).first_or_404()

    shift_workers = Users.query.filter(Users.shift_id == shift_id)
    list_of_shift_workers = [i.name for i in shift_workers]

    order = Orders(
        order_table=f"Столик №{table_id}",
        date_time=datetime.now().strftime("%y-%m-%d %H:%m"),
        price=0,
        status_id=3,  # order was added
        user_id=cur_user.id,
        shift_id=shift_id
    )

    db.session.add(order)
    db.session.commit()

    return jsonify(
        {"data": {
            "id": order_id,
            "table_id": table_id,
            "shift_workers": ", ".join(list_of_shift_workers),
            "create_at": datetime.now().strftime("%y-%m-%d %H:%m"),
            "status": "Принят",
            "price": 0
        }
        }
    )


# TODO fix register, single view to user, dismiss user


if __name__ == "__main__":
    app.run(debug=True)

# TODO fix tests in postman
