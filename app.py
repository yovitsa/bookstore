from flask import Flask, render_template, url_for, abort, jsonify, request
from pathlib import Path
from db import db
from models import Book, Category, User, BookRental
from sqlalchemy import select
from datetime import datetime, timezone

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///store.db"
app.instance_path = Path(".").resolve()

db.init_app(app)

# Validation functions
is_positive_number = lambda num: isinstance(num, (int, float)) and num >= 0
is_non_empty_string = lambda s: isinstance(s, str) and len(s) > 0
is_valid_rating = lambda num: isinstance(num, int) and 1 <= num <= 5

# Field mapping
required_fields = {
    "title": is_non_empty_string,
    "price": is_positive_number,
    "available": is_positive_number,
    "rating": is_valid_rating,
    "url": is_non_empty_string,
    "upc": is_non_empty_string,
    "category": is_non_empty_string,
}
# If no result 404 error
def first_or_404(stmt):
    result = db.session.execute(stmt).scalars().first()
    if result is None:
        abort(404)
    return result

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# List all books
@app.route('/books')
def list_books():
    stmt = db.select(Book)
    books = db.session.execute(stmt).scalars()
    return render_template('books.html', books=books)

# List all categories
@app.route('/categories')
def list_categories():
    stmt = db.select(Category)
    categories = db.session.execute(stmt).scalars()
    return render_template('categories.html', categories=categories)

# Show books in a specific category
@app.route('/categories/<string:name>')
def category_detail(name):
    stmt = db.select(Category).where(Category.name == name)
    category = first_or_404(stmt)
    stmt = db.select(Book).where(Book.category_id == category.id)
    books = db.session.execute(stmt).scalars()
    return render_template('category_detail.html', category=category, books=books)

# Show details of a specific book
@app.route('/book/<int:book_id>')
def book_detail(book_id):
    stmt = db.select(Book).where(Book.id == book_id)
    book = first_or_404(stmt)
    return render_template('book_detail.html', book=book)

# List all users
@app.route('/users')
def list_users():
    stmt = db.select(User)
    users = db.session.execute(stmt).scalars()
    return render_template('users.html', users=users)

# Show details of a specific user
@app.route('/user/<int:user_id>')
def user_detail(user_id):
    stmt = db.select(User).where(User.id == user_id)
    user = first_or_404(stmt)
    return render_template('user_detail.html', user=user)

# List all available books
@app.route('/available')
def available_books():
    stmt = db.select(Book).where(~Book.rentals.any() | ~Book.rentals.any(BookRental.returned == None))
    books = db.session.execute(stmt).scalars()
    return render_template('available_books.html', books=books)

# List all rented books
@app.route('/rented')
def rented_books():
    stmt = db.select(Book).where(Book.rentals.any(BookRental.returned == None))
    books = db.session.execute(stmt).scalars()
    return render_template('rented_books.html', books=books)

# API endpoint to list all books
@app.route('/api/books')
def api_books():
    stmt = db.select(Book)
    books = db.session.execute(stmt).scalars()
    books_dict = [book.to_dict() for book in books]
    return jsonify(books_dict)

# API endpoint to show details of a specific book
@app.route('/api/books/<int:book_id>')
def api_book_detail(book_id):
    stmt = db.select(Book).where(Book.id == book_id)
    book = first_or_404(stmt)
    return jsonify(book.to_dict())

# API endpoint to create a new book
@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json() 

    # Field validation
    for field in required_fields:
        # The field is missing
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
        else:
            # Extract the validation function
            func = required_fields[field]
            # Extract the value
            value = data[field]
            # Validate the value
            if not func(value):
                return jsonify({'error': f'Invalid value for field {field}: {value}'}), 400

    # Check for database duplicates
    stmt = db.select(Book).where(Book.upc == data['upc'])
    if db.session.execute(stmt).scalars().first():
        return jsonify({'error': 'That UPC already exists'}), 400

    # Look for the category in the database
    stmt = db.select(Category).where(Category.name == data['category'])
    category = db.session.execute(stmt).scalars().first()
    if not category:
        category = Category(name=data['category'])
        db.session.add(category)
        db.session.commit()

    # Add the book to the database
    book_data = {
        'title': data['title'],
        'price': data['price'],
        'available': data['available'],
        'rating': data['rating'],
        'upc': data['upc'],
        'url': data['url'],
        'category_id': category.id
    }

    book = Book(**book_data)
    db.session.add(book)
    db.session.commit()

    return jsonify(book.to_dict()), 201

# API endpoint to rent a book
@app.route('/api/books/<int:book_id>/rent', methods=['POST'])
def rent_book(book_id):
    data = request.get_json()  

    # Check if the book exists
    stmt = db.select(Book).where(Book.id == book_id)
    book = first_or_404(stmt)

    # Check if the book is available
    if not book.is_available():
        return jsonify({'error': 'That book is not available'}), 403

    # Validate user_id
    if 'user_id' not in data or not isinstance(data['user_id'], int):
        return jsonify({'error': 'Invalid or missing user_id'}), 400

    # Check if the user exists
    stmt = db.select(User).where(User.id == data['user_id'])
    user = db.session.execute(stmt).scalars().first()
    if not user:
        return jsonify({'error': 'User does not exist'}), 404

    # Create a new BookRental
    rental = BookRental(
        book_id=book.id,
        user_id=data['user_id'],
        rented=datetime.now(timezone.utc)  
    )
    db.session.add(rental)
    db.session.commit()

    return jsonify(rental.to_dict()), 201

# API endpoint to return a book
@app.route('/api/books/<int:book_id>/return', methods=['PUT'])
def return_book(book_id):
    # Check if the book exists
    stmt = db.select(Book).where(Book.id == book_id)
    book = first_or_404(stmt)

    # Check if the book is rented
    rental = None
    for rent in book.rentals:
        if rent.returned is None:
            rental = rent
            break

    if rental is None:
        return jsonify({'error': 'Book is not rented'}), 403

    # Terminate the rental
    rental.returned = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(rental.to_dict()), 200


if __name__ == "__main__":
    app.run(debug=True)  
