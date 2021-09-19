from datetime import datetime
import json
from json.decoder import JSONDecodeError
from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    _orders = db.Column(db.String(100), nullable=False, default='[]')
    active_order = db.Column(db.integer(), db.ForeignKey('orders.id'))
    last_order_time = db.Column(db.DateTime)

    def __init__(self, **kwargs):
        orders = kwargs.pop('orders', None)
        if orders:
            self.orders = orders

        super().__init__(**kwargs)

    @property
    def orders(self):
        return json.loads(self._orders)

    @orders.setter
    def orders(self, value):
        if isinstance(value, str):
            self._order = value
        elif isinstance(value, list):
            try:
                self._orders = json.dumps(value)
            except JSONDecodeError:
                self._orders = '[]'

    def update(self, order):
        orders = self.orders
        orders.append(order.id)
        self.orders = orders
        self.last_order_time = order.timestamp

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    sold = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"Item('{self.name}')"

    def update(self, ordered):
        if ordered > self.stock:
            raise ValueError("Sufficient quantity not present in stock")

        self.stock -= ordered
        self.sold += ordered
        

class Order(db.Model):
    __tablename__ = 'order'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    _items = db.Column(db.String(255), nullable=False)
    _completed = db.Column(db.Boolean, nullable=False, default=False)
    _cancelled = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, **kwargs):
        items = kwargs.pop('items', None)
        if items:
            self.items = items

        super().__init__(**kwargs)

    @property
    def items(self):
        return json.loads(self._items, object_hook=lambda d: {int(k): v for k,v in d.items()})

    @items.setter
    def items(self, items):
        if isinstance(items, str):
            self._items = items
        elif isinstance(items, list):
            try:
                self._items = json.dumps(items)
            except JSONDecodeError:
                self._items = '[]'

    def __eq__(self, other):
        items = set(self.items)
        if isinstance(other, self.__class__):
            other_items = set(other.items)
        elif isinstance(other, list):
            other_items = set(other)
        return items == other_items

    def yield_items(self):
        for row in self.items:
            for item_id, nos in row.items():
                yield item_id, nos

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, value: bool):
        if value:
            for item_id, nos in self.yield_items():
                item = Item.get_by_id(item_id)
                try:
                    item.update(nos)
                except ValueError:
                    # TODO: need to add logic to send back data about the lacking items
                    pass
                db.session.add(item)

        self.timestamp = datetime.now()
        self._completed = value

        user = User.get_by_id(self.account_number)
        user.update(self)
        db.session.add(user)
        
        db.session.add(self)
        db.session.commit()

    @property
    def cancelled(self):
        return self._cancelled

    @cancelled.setter
    def cancelled(self, value: bool):
        if value:
            self.timestamp = datetime.now()

        self._cancelled = value
        db.session.add(self)
        db.session.commit()

    def cancel(self):
        self.cancelled = True
