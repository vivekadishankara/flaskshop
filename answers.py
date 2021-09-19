from models import db, Order, Item, User
from app import app


# Create an example json representation of an order
order = [
    {
        'account_number': '1',
        '_items': '[{1:2}, {2:4}, {3:5}]'
    },
    {
        'account_number': '2',
        '_items': '[{1:5}, {2:3}, {3:1}]'
    }
]


# A POST endpoint that accepts the json representation of the orders,
# and maintains these. Return a unique order id and reject duplicate
# orders.
@app.route("/orders_id", methods=["POST"])
def order_id(order):
    orders = Order.query.all()
    for db_order in orders:
        # I dont understand this condition but nonetheless
        if db_order == order:
            return 0
    order = Order(**order)
    db.session.add(order)
    db.session.commit()
    order_id = order.id
    return order_id


# An endpoint that will return the top three selling items by total value.
# I am a bit skeptical about the query used coz value may mean price*sold
@app.route("top_three", methods=["GET"])
def top_three():
    items = Item.query.order_by(Item.sold)[:3].all()
    return items


# An endpoint that will return the count of members that have made an
# order in the last three days.
@app.route("user_nos", method=["GET"])
def user_nos():
    users = User.query.filter().all()
    nos = len(users)
    return nos


# A POST endpoint that accepts a list of member account numbers, and
# cancels their associated orders. Return a count of cancelled orders.
@app.route("cancel_orders", methods=["POST"])
def cancel_orders(user_ids):
    cancelled_orders = 0
    for id in user_ids:
        user = User.get_by_id(id)
        active_order = user.active_order
        if active_order:
            active_order.cancel()
            cancelled_orders += 1
        return cancelled_orders