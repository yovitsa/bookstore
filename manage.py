import csv  
from datetime import datetime 
from db import db  
from models import Book, Category, User, BookRental 
from app import app  
from sqlalchemy import select  

# This function will get a category by name
def get_category(name):
    stmt = select(Category).where(Category.name == name)  
    return db.session.execute(stmt).scalars().first()  

# Function to delete all tables in the database
def delete_all_tables():
    with app.app_context():  
        db.drop_all()  

# This function will create all tables in the database
def create_all_tables():
    with app.app_context():  
        db.create_all()  

# This Function will import books from a CSV file
def import_books_from_csv():
    with app.app_context():  
        with open('data/books.csv', newline='') as csvfile:  
            reader = csv.DictReader(csvfile)  
            for row in reader:  
                category_name = row['category']  
                category = get_category(category_name)  
                if not category:  
                    category = Category(name=category_name) 
                    db.session.add(category)  
                    db.session.commit()  

                # Create a new book with the data from the row
                book = Book(
                    title=row['title'],
                    price=row['price'],
                    available=row['available'],
                    rating=row['rating'],
                    upc=row['upc'],
                    url=row['url'],
                    category_id=category.id
                )
                db.session.add(book)  
            db.session.commit()  

# This function will import users from a CSV file
def import_users_from_csv():
    with app.app_context():  
        with open('data/users.csv', newline='') as csvfile:  
            reader = csv.DictReader(csvfile)  
            for row in reader:  
                user = User(name=row['name'])  
                db.session.add(user) 
            db.session.commit()  



#THis function will import book rentals from a CSV file
def import_book_rentals_from_csv():
    with app.app_context():
        with open('data/bookrentals.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                book = db.session.execute(db.select(Book).where(Book.upc == row['book_upc'])).scalars().first()
                user = db.session.execute(db.select(User).where(User.name == row['user_name'])).scalars().first()
                
                if not book or not user:
                    continue  
                
                rented_date = datetime.strptime(row['rented'], "%Y-%m-%d %H:%M")
                returned_date = datetime.strptime(row['returned'], "%Y-%m-%d %H:%M") if row['returned'] else None
                
                rental = BookRental(
                    book_id=book.id,
                    user_id=user.id,
                    rented=rented_date,
                    returned=returned_date
                )
                db.session.add(rental)
            db.session.commit()

if __name__ == "__main__":
    delete_all_tables() 
    create_all_tables() 
    import_books_from_csv() 
    import_users_from_csv()  
    import_book_rentals_from_csv()