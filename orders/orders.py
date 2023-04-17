from datetime import datetime

from flask import Blueprint, request, jsonify

from models import db, Shifts, Users, Orders, OrderStatuses, OrderItems
from users.users import auth

orders = Blueprint("orders", __name__)


@orders.route("/api-cafe/order", methods=["POST"])
@auth.login_required(role=3)
def create_order():
    shift_id = request.json["work_shift_id"]
    table_id = request.json["table_id"]
    order_id = len(Orders.query.all()) + 1
    # number_of_persons = request.json["number_of_person"]

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


@orders.route("/api-tort/work-shift/<shift_id>/orders")
@auth.login_required(role=3)
def show_orders_per_shift(shift_id):
    orders_per_shift = Orders.query.filter(Orders.shift_id == shift_id)
    current_shift = Shifts.query.filter(Shifts.id == shift_id).first_or_404()
    list_of_orders = []
    total_price = 0
    for order in orders_per_shift:
        total_price += order.price
        order_dict = {
            "id": order.id, "table": order.order_table,
            "shift_workers": Users.query.filter(Users.id == order.user_id).name,
            "created_at": order.date_time,
            "status": OrderStatuses.query.filter(OrderStatuses.id == order.status_id).status_name,
            "price": order.price
        }
        list_of_orders.append(order_dict)
    return jsonify({"data": {
        "id": current_shift.id,
        "start": current_shift.start,
        "end": current_shift.end,
        "active": current_shift.active,
        "orders": [list_of_orders],
        "amount_of_all": total_price
    }})


@orders.route("api-cafe/order/<order_id>", methods=["GET"])
@auth.login_required(role=[1, 2])
def show_order(order_id):  # TODO test func
    order = Orders.query(Orders).join(Users, Users.id == Orders.id).join(OrderStatuses)  # TODO test query
    return jsonify({
        "id": order.id,
        "order_table": order.order_table,
        "created_at": order.date_time,
        "price": order.price,
        "status": order.status_name,
        "user": order.name,
        "shift": order.shift_id
    })


@orders.route("/api-cafe/order/<order_id>/change-status", methods=["PATCH"])
@auth.login_required(role=[1, 2])
def change_status(order_id):  # TODO test this func
    status = request.json["status"]
    status_id = 0
    if status == "canceled":
        status_id = ...
    elif status == "payed":
        status_id = ...

    order = Orders.query.filter(Orders.id == order_id)
    order.status_id = status_id
    return jsonify({"data": f"status changed to {status}"})


@orders.route("/api-cafe/order/<order_id>/position", methods=["POST"])
@auth.login_required(role=[1, 2])
def add_position(order_id):
    menu_id = request.json["menu_id"]
    count = request.json["count"]

    order_items = OrderItems.query.filter(Orders.id == order_id)

    # TODO complete func
