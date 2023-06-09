from datetime import datetime

from flask import Blueprint, request, jsonify, abort

from models import db, Shifts, Users
from users.users import auth

work_shifts = Blueprint("work_shift", __name__)


def convert_to_date(str_time):
    """
    converts XXXX-XX-XX XX:XX datetime to pythonic date object
    :param str_time:
    :return: datetime object
    """
    split_time = str_time.split()
    tuple_time = split_time[0].split("-"), split_time[1].split(":")
    res = []

    for i in tuple_time:
        for j in i:
            res.append(int(j))

    return datetime(res[0], res[1], res[2], res[3], res[4])


def compare_date(start_time, end_time):
    return True if start_time < end_time else False


@work_shifts.route("/api-cafe/work-shift", methods=["GET", "POST"])
@auth.login_required(role=1)
def create_work_shift():  # this func for creating new work-shifts
    if request.method == "POST":
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

    elif request.method == "GET":
        all_work_shifts = Shifts.query.all()
        result = []
        for shift in all_work_shifts:
            shift_dict = {
                "id": shift.id,
                "start_time": shift.start_time.strftime("%y-%m-%d %H:%m"),
                "end_time": shift.end_time.strftime("%y-%m-%d %H:%m"),
                "active": shift.active.strftime("%y-%m-%d %H:%m"),
            }
            result.append(shift_dict)
        return jsonify({"data": result})


@work_shifts.route("/api-cafe/work-shift/<shift_id>/open", methods=["GET"])
@auth.login_required(role=1)
def start_work_shift(shift_id):
    shift = Shifts.query.filter(Shifts.id == shift_id).first()
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


@work_shifts.route("/api-cafe/work-shift/<shift_id>/close")
@auth.login_required(role=1)
def end_work_shift(shift_id):
    current_shift = Shifts.query.filter(Shifts.id == shift_id).first()
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


@work_shifts.route("/api-cafe/work-shift/<shift_id>/user", methods=["POST"])
@auth.login_required(role=1)
def add_user_to_shift(shift_id):
    user_id = request.json["user_id"]
    current_user = Users.query.filter(Users.id == user_id).first()
    current_user.shift_id = shift_id
    db.session.add(current_user)
    db.session.commit()
    return jsonify({
        "data": {
            "id_user": user_id,
            "status": "added"
        }
    })


@work_shifts.route("/api-cafe/work-shift/<shift_id>/user/<user_id>", methods=["DELETE"])
@auth.login_required(role=1)
def delete_user_from_shift(shift_id, user_id):
    user = Users.query.filter(Users.id == int(user_id)).first()
    if user.shift_id == int(shift_id):
        user.shift_id = None
        db.session.add(user)
        db.session.commit()
        return jsonify({
            "data": {
                "id_user": user_id,
                "status": "deleted"
            }
        })
    else:
        return jsonify({"error": "not match"})

