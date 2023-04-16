from datetime import datetime

from flask import Blueprint, request, jsonify

from models import db, Shifts, Users, Orders
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
