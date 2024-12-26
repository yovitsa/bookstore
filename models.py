from sqlalchemy import ForeignKey, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from db import db
import datetime
from datetime import datetime, timezone

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    price = db.Column(db.Float)
    available = db.Column(db.Integer)
    rating = db.Column(db.Integer)
    upc = db.Column(db.String, unique=True, nullable=False)
    url = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    category = db.relationship("Category", back_populates="books")
    rentals = db.relationship("BookRental", back_populates="book")

    # Convert the book instance to a dictionary
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'price': self.price,
            'available': self.available,
            'rating': self.rating,
            'upc': self.upc,
            'url': self.url,
            'category_id': self.category_id,
            'category': self.category.name if self.category else None,
            'is_available': self.is_available()
        }
    # Check if the book is currently available
    def is_available(self):
       
        for rental in self.rentals:
            if rental.returned is None:
                return False
        return True

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    books = db.relationship("Book", back_populates="category")

class BookRental(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    rented = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    returned = db.Column(db.DateTime, nullable=True)
    book = db.relationship("Book", back_populates="rentals")
    user = db.relationship("User", back_populates="rentals")
     # Convert the rental instance to a dictionary
    def to_dict(self):
        return {
            'id': self.id,
            'book_id': self.book_id,
            'user_id': self.user_id,
            'rented': self.rented,
            'returned': self.returned
        }

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    rentals = db.relationship("BookRental", back_populates="user")