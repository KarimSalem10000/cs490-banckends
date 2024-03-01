from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import datetime
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError


app = Flask(__name__)
CORS(app)
x = "Brkyjj21"
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://root:{x}@localhost/sakila'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db=SQLAlchemy(app)
ma=Marshmallow(app)

class Actor(db.Model): 
    __tablename__ = 'actor'
    actor_id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self,first_name,last_name):
        self.first_name = first_name
        self.last_name = last_name

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self,name):
        self.name = name


class City(db.Model):
    __tablename__ = 'city'
    city_id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(50))
    country_id = db.Column(db.Integer)
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self,city,country_id):
        self.city = city
        self.country_id = country_id

class Film(db.Model):
    __tablename__ = 'film'
    film_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    release_year = db.Column(db.String(4))
    language_id = db.Column(db.Integer)
    rental_duration = db.Column(db.Integer)
    rental_rate = db.Column(db.Float)
    length = db.Column(db.Integer)
    replacement_cost = db.Column(db.Float)
    rating = db.Column(db.String(10))
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)
    special_features = db.Column(db.String(100))

    def __init__(self,title,description,release_year,language_id,rental_duration,rental_rate,length,replacement_cost,rating,special_features,fulltext):
        self.title = title
        self.description = description
        self.release_year = release_year
        self.language_id = language_id
        self.rental_duration = rental_duration
        self.rental_rate = rental_rate
        self.length = length
        self.replacement_cost = replacement_cost
        self.rating = rating
        self.special_features = special_features
    
class FilmSchema(ma.Schema):
    class Meta:
        fields = ('film_id','title','description','release_year','language_id','rental_duration','rental_rate','length','replacement_cost','rating','special_features')

film_schema = FilmSchema()
films_schema = FilmSchema(many=True)

from sqlalchemy import LargeBinary

class Address(db.Model):
    __tablename__ = 'address'

    address_id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(255))
    address2 = db.Column(db.String(255))
    district = db.Column(db.String(20))
    city_id = db.Column(db.Integer, db.ForeignKey('city.city_id'))
    postal_code = db.Column(db.String(10))
    phone = db.Column(db.String(20))
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self, address, address2, district, city_id, postal_code, phone):
        self.address = address
        self.address2 = address2
        self.district = district
        self.city_id = city_id
        self.postal_code = postal_code
        self.phone = phone




class Customer(db.Model):
    __tablename__ = 'customer'
    customer_id = db.Column(db.Integer, primary_key=True)
    store_id = db.Column(db.Integer)
    first_name = db.Column(db.String(45))
    last_name = db.Column(db.String(45))
    email = db.Column(db.String(50))
    address_id = db.Column(db.Integer)
    active = db.Column(db.Boolean)
    create_date = db.Column(db.DateTime, default=datetime.datetime.now)
    last_update = db.Column(db.DateTime, default=datetime.datetime.now)

    def __init__(self,first_name,last_name):
        self.first_name = first_name
        self.last_name = last_name

class CustomerSchema(ma.Schema):
    class Meta:
        fields = ('customer_id','first_name','last_name','last_update','email')

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

@app.route('/')
def hello_world():
    return '<p>Hello, World!</p>'

# Execute the SQL query to retrieve the top 5 rented films
@app.route('/topmovies', methods=['GET'])
def topmovies():
    query_result = db.session.execute(text('''
        SELECT f.film_id, f.title, c.name AS category, COUNT(*) AS rental_count
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film f ON i.film_id = f.film_id
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        GROUP BY f.film_id, f.title, c.name
        ORDER BY rental_count DESC
        LIMIT 5
    '''))
    top_movies = []
    for row in query_result:
        movie = {
            'film_id': row[0],
            'title': row[1],
            'category': row[2],
            'rental_count': row[3]
        }
        top_movies.append(movie)
    return jsonify(top_movies)


@app.route('/movieinfo/<film_id>', methods=['GET'])
def movieinfo(film_id):
    # Query the Film and Category tables to get details of the specified film
    film = Film.query.get(film_id)

    # Execute the query to retrieve movie details along with the category
    query_result = db.session.execute(text('''
        SELECT f.film_id, f.title, c.name AS category, COUNT(*) AS rental_count
        FROM rental r
        JOIN inventory i ON r.inventory_id = i.inventory_id
        JOIN film f ON i.film_id = f.film_id
        JOIN film_category fc ON f.film_id = fc.film_id
        JOIN category c ON fc.category_id = c.category_id
        WHERE f.film_id = :film_id
        GROUP BY f.film_id, f.title, c.name
    '''), {'film_id': film_id})

    # Fetch the query result (should be only one row)
    movie = query_result.fetchone()

    if movie:
        # Create a dictionary to store film details along with the category
        film_details = {
            'film_id': movie[0],
            'title': movie[1],
            'category': movie[2],
            'rental_count': movie[3],
            'description': film.description,
            'release_year': film.release_year,
            'language_id': film.language_id,
            'rental_duration': film.rental_duration,
            'rental_rate': film.rental_rate,
            'length': film.length,
            'replacement_cost': film.replacement_cost,
            'rating': film.rating,
            'special_features': film.special_features
        }

        # Return the combined data in JSON format
        return jsonify(film_details)
    else:
        return jsonify({'message': 'Film not found'}), 404

@app.route('/topactors', methods=['GET'])
def top_actors():
    # Execute the SQL query to retrieve the top 5 actors
    query_result = db.session.execute(text('''
        SELECT a.actor_id, a.first_name, a.last_name, COUNT(*) AS count
        FROM actor a
        JOIN film_actor fa ON a.actor_id = fa.actor_id
        GROUP BY a.actor_id
        ORDER BY count DESC
        LIMIT 5
    '''))

    # Extract the top 5 actors' information from the query result
    top_actors = []
    for row in query_result:
        actor_info = {
            'actor_id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'count': row[3]
        }
        top_actors.append(actor_info)

    # Return the JSON response
    return jsonify(top_actors)

@app.route('/actorinfo/<actor_id>', methods=['GET'])
def actorinfo(actor_id):
    # Query the Actor table to get details of the specified actor
    actor = Actor.query.get(actor_id)

    if actor:
        # Execute the SQL query to retrieve the top five rented movies for the given actor
        query_result = db.session.execute(text('''
            SELECT f.film_id, f.title, COUNT(*) AS rental_count
            FROM rental r
            JOIN inventory i ON r.inventory_id = i.inventory_id
            JOIN film f ON i.film_id = f.film_id
            JOIN film_actor fa ON f.film_id = fa.film_id
            WHERE fa.actor_id = :actor_id
            GROUP BY f.film_id, f.title
            ORDER BY rental_count DESC
            LIMIT 5
        '''), {'actor_id': actor_id})

        # Create a list to store the top five rented movies
        top_movies = []
        for row in query_result:
            movie = {
                'film_id': row[0],
                'title': row[1],
                'rental_count': row[2]
            }
            top_movies.append(movie)

        # Create a dictionary to store actor details and top five rented movies
        actor_info = {
            'actor_id': actor.actor_id,
            'first_name': actor.first_name,
            'last_name': actor.last_name,
            'last_update': actor.last_update,
            'top_movies': top_movies
        }

        # Return the actor details along with top five rented movies in JSON format
        return jsonify(actor_info)
    else:
        # Return a 404 response if the actor with the provided ID is not found
        return jsonify({'message': 'Actor not found'}), 404


# @app.route('/actorinfo/<actor_id>', methods=['GET'])
# def actor_info(actor_id):
#     # Query the Actor table to get details of the specified actor

#     if actor:
#         # Create a dictionary to store actor details
#         actor_details = {
#             'actor_id': actor.actor_id,
#             'first_name': actor.first_name,
#             'last_name': actor.last_name
#         }

#         # Return the actor details in JSON format
#         return jsonify(actor_details)
#     else:
#         # Return a 404 response if the actor with the provided ID is not found
#         return jsonify({'message': 'Actor not found'}), 404

# list all the users
@app.route('/listusers', methods=['GET'])
def listusers():
    # Joining Customer with Address table to get address details
    users_with_address = db.session.query(Customer, Address).join(Address, Customer.address_id == Address.address_id).all()
    
    # Creating a list to store user details along with their addresses
    result = []
    for user, address in users_with_address:
        result.append({
            'customer_id': user.customer_id,
            'store_id': user.store_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'address': address.address,
            'address2': address.address2,
            'district': address.district,
            'city_id': address.city_id,
            'postal_code': address.postal_code,
            'phone': address.phone,
            'last_update': address.last_update
        })
    
    return jsonify(result)

@app.route('/listuser/<customer_id>', methods=['GET']) 
def list_user(customer_id):
    # Execute the SQL query to retrieve user details along with their currently rented DVDs
    query_result = db.session.execute(text('''
        SELECT c.customer_id, c.first_name, c.last_name, c.email, 
               a.address, a.postal_code, a.phone, COUNT(r.rental_id) AS rental_count,
               GROUP_CONCAT(CONCAT(f.film_id, ':', f.title)) AS rented_dvds
        FROM customer c
        JOIN address a ON c.address_id = a.address_id
        LEFT JOIN rental r ON c.customer_id = r.customer_id
        LEFT JOIN inventory i ON r.inventory_id = i.inventory_id
        LEFT JOIN film f ON i.film_id = f.film_id
        WHERE c.customer_id = :customer_id AND r.return_date IS NULL
        GROUP BY c.customer_id
    '''), {'customer_id': customer_id})

    # Fetch the user details and rented DVDs from the query result
    user = query_result.fetchone()
    rented_dvds = []

    # If user exists, create a dictionary to store user details along with their rented DVDs
    if user:

        if user.rented_dvds:
            for dvd in user.rented_dvds.split(','):
                film_id, title = dvd.split(':')
                rented_dvds.append({'film_id': film_id, 'title': title})

            

        # Query the Address table to get the address details of the user
    user = Customer.query.get(customer_id)
    if user:
        address = Address.query.get(user.address_id)
        city_info = City.query.get(address.city_id)

        result = {
            'customer_id': user.customer_id,
            'store_id': user.store_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'address_id': address.address_id,
            'address': address.address,
            'address2': address.address2,
            'district': address.district,
            'city': city_info.city,
            'postal_code': address.postal_code,
            'phone': address.phone,
            'last_update': address.last_update,
            'rented_dvds': rented_dvds
        }
        return jsonify(result)
    return jsonify({'message': 'User not found or no rented DVDs'}), 404



#list the details of a single user
# list the details of a single user
@app.route('/userdetails/<customer_id>', methods=['GET'])
def user(customer_id):
    # Query the Customer table to get details of the specified customer
    user = Customer.query.get(customer_id)
    if user:
        # Query the Address table to get the address details of the user
        address = Address.query.get(user.address_id)
        city_info = City.query.get(address.city_id)


        # Create a dictionary to store user details along with their address
        result = {
            'customer_id': user.customer_id,
            'store_id': user.store_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'address_id': address.address_id,
            'address': address.address,
            'address2': address.address2,
            'district': address.district,
            'city': city_info.city,
            'postal_code': address.postal_code,
            'phone': address.phone,
            'last_update': address.last_update
        }
        # Return the combined data in JSON format
        return jsonify(result)
    else:
        # Return a 404 response if the customer with the provided ID is not found
        return jsonify({'message': 'Customer not found'}), 404



@app.route('/userupdate/<customer_id>', methods=['PUT'])
def userupdate(customer_id):
    # Query the Customer table to get details of the specified customer
    user = Customer.query.get(customer_id)
    
    # Return 404 if user is not found
    if not user:
        return jsonify({'message': 'Customer not found'}), 404

    # Update customer details
    user.first_name = request.json.get('first_name', user.first_name)
    user.last_name = request.json.get('last_name', user.last_name)
    user.email = request.json.get('email', user.email)
    user.store_id = 1

    # Query the Address table to get the address details of the user
    address = Address.query.get(user.address_id)
    address.address = request.json.get('address', address.address)
    address.address2 = request.json.get('address2', address.address2)
    address.district = request.json.get('district', address.district)
    
    # Update city information if provided in the request
    city_name = request.json.get('city')
    if city_name:
        city = City.query.filter_by(city=city_name).first()
        if city:
            address.city_id = city.city_id

    # Commit changes to the database
    db.session.commit()

    return jsonify({'message': 'User details updated successfully'}), 200




# Add a new user
from datetime import datetime

@app.route('/useradd', methods=['POST'])
def useradd():
    # Ensure the required fields are present in the request JSON
    required_fields = ['first_name', 'last_name', 'email', 'address', 'address2', 'district', 'city', 'postal_code', 'phone']
    if not all(field in request.json for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400
    
    # Extract data from the request JSON
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    address = request.json['address']
    address2 = request.json.get('address2', '')
    district = request.json['district']
    city_name = request.json['city']
    postal_code = request.json['postal_code']
    phone = request.json['phone']

    # Query the City table to get the city ID based on the city name
    city = City.query.filter_by(city=city_name).first()
    if not city: 
        return jsonify({'message': 'City not found'}), 404
    
    new_city = City(city=city_name, country_id=1)
    db.session.add(new_city)
    db.session.commit()

    # Create a new Address object and add it to the database
    new_address = Address(address=address, address2=address2, district=district, city_id=city.city_id, postal_code=postal_code, phone=phone)
    db.session.add(new_address)
    db.session.commit()

    # Create a new Customer object and add it to the database
    new_customer = Customer(first_name=first_name, last_name=last_name, email=email, address_id=new_address.id, store_id=1)
    db.session.add(new_customer)
    db.session.commit()

    return jsonify({'message': 'User added successfully', 'user_id': new_customer.id}), 201

# Delete a user
@app.route('/userdelete/<customer_id>', methods=['DELETE'])
def userdelete(customer_id):
    try:
        # Query the database to find the user by ID
        user = Customer.query.get(customer_id)
        
        # If the user does not exist, return a 404 response
        if not user:
            return jsonify({'message': 'User not found'}), 404

        # Delete the user from the database
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'}), 200
    except IntegrityError as e:
        db.session.rollback()  # Rollback the transaction to avoid leaving the database in an inconsistent state
        return jsonify({'error': 'Could not delete user. Associated records exist.'}), 500







if __name__ == '__main__':
    app.run(debug=True)

