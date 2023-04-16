from models import app

from users.users import users
from work_shifts.work_shifts import work_shifts
from orders.orders import orders

# blueprints

app.register_blueprint(users)
app.register_blueprint(work_shifts)
app.register_blueprint(orders)

# TODO fix register, single view to user


if __name__ == "__main__":
    app.run(debug=True)
