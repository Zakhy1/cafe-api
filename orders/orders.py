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

    cur_user = Users.query.filter(Users.token == auth.current_user()).first()

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
def show_orders_per_shift(shift_id):  # TODO FIX QUERIES
    orders_per_shift = Orders.query.filter(Orders.shift_id == shift_id)
    current_shift = Shifts.query.filter(Shifts.id == shift_id).first()
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


@orders.route("/api-cafe/order/<order_id>", methods=["GET"])
@auth.login_required(role=[1, 3])
def show_order(order_id):
    order = db.session.query(Orders, Users, OrderStatuses) \
        .join(Users, Orders.user_id == Users.id) \
        .join(OrderStatuses, OrderStatuses.id == Orders.status_id) \
        .filter(Orders.id == order_id) \
        .first()
    return jsonify({
        "id": order[0].id,
        "order_table": order[0].order_table,
        "created_at": order[0].date_time,
        "price": order[0].price,
        "status": order[2].status_name,
        "user": order[1].name,
        "shift": order[0].shift_id
    })


@orders.route("/api-cafe/order/<order_id>/change-status", methods=["PATCH"])
@auth.login_required()
def change_status(order_id):
    status = request.json["status"]
    status_id = 0
    if status == "canceled":
        status_id = 4
    elif status == "cooking":
        status_id = 2
    elif status == "ready":
        status_id = 1

    order = db.session.query(Orders).filter(Orders.id == order_id).first()
    order.status_id = status_id
    db.session.add(order)
    db.session.commit()
    return jsonify({"data": f"status changed to {status}"})


@orders.route("/api-cafe/order/<order_id>/position", methods=["POST"])
@auth.login_required(role=[1, 3])
def add_position(order_id):
    menu_id = int(request.json["menu_id"])
    quantity = int(request.json["count"])

    order_items = OrderItems(
        order_id=order_id, menu_item_id=menu_id, quantity=quantity
    )
    db.session.add(order_items)
    db.session.commit()

    return jsonify({
        "data": "position was added"
    })


@orders.route("/api-cafe/order/<order_id>/position/<order_item_id>", methods=["DELETE"])
@auth.login_required(role=[1, 3])
def del_menu_item(order_id, order_item_id):
    cur_items = db.session.query(OrderItems) \
        .filter(OrderItems.order_id == order_id and OrderItems.menu_item_id == order_item_id) \
        .first()
    db.session.delete(cur_items)
    db.session.commit()

    return jsonify({"data": "menu item was deleted"})


@orders.route("/api-cafe/order/taken/get")
@auth.login_required(role=[1, 2])
def show_active_shift_orders():
    current_shift = Shifts.query.filter(Shifts.active == True).first()
    orders_per_shift = Orders.query.filter(Orders.shift_id == current_shift.id).all()
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
        "start": current_shift.start_time,
        "end": current_shift.end_time,
        "active": current_shift.active,
        "orders": [list_of_orders],
        "amount_of_all": total_price
    }})
