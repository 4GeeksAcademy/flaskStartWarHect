"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Planet, Favorite
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def get_users():
    users = User.query.all()
    # Usamos list comprehension y el método serialize que definiste en models.py
    all_users = [user.serialize() for user in users]
    return jsonify(all_users), 200

# POST: Crear usuario correctamente con persistencia
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name') # Asegúrate de pedir name, ya que tu modelo lo requiere

    if not email or not password or not name:
        return jsonify({"msg": "Faltan datos requeridos"}), 400

    # Crear el objeto y guardarlo en la base de datos
    new_user = User(email=email, password=password, name=name)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "Usuario creado exitosamente"}), 201


@app.route('/user/<int:user_id>', methods=['PATCH'])
def update_user(user_id):
    # 1. Buscar el usuario en la base de datos
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    # 2. Obtener los datos del cuerpo de la petición
    data = request.get_json()

    # 3. Actualizar solo los campos que vienen en el JSON
    if "name" in data:
        user.name = data["name"]
    if "email" in data:
        user.email = data["email"]
    # No actualizamos la contraseña sin validaciones extra de seguridad

    # 4. Guardar cambios
    db.session.commit()

    return jsonify({"msg": "Usuario actualizado", "user": user.serialize()}), 200


@app.route('/character', methods=['POST'])
def create_character():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"msg": "El nombre es obligatorio"}), 400

    new_character = Character(name=name)
    db.session.add(new_character)
    db.session.commit()
    
    return jsonify({"msg": "Personaje creado", "character": new_character.serialize()}), 201


@app.route('/planet', methods=['POST'])
def create_planet():
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({"msg": "El nombre es obligatorio"}), 400

    new_planet = Planet(name=name)
    db.session.add(new_planet)
    db.session.commit()
    
    return jsonify({"msg": "Planeta creado", "planet": new_planet.serialize()}), 201


@app.route('/character/<int:character_id>', methods=['PATCH'])
def update_character(character_id):
    # Buscar el personaje
    character = Character.query.get(character_id)
    if character is None:
        return jsonify({"msg": "Personaje no encontrado"}), 404

    data = request.get_json()

    # Actualizar solo si el campo viene en el JSON
    if "name" in data:
        character.name = data["name"]

    db.session.commit()
    return jsonify({"msg": "Personaje actualizado", "character": character.serialize()}), 200


@app.route('/planet/<int:planet_id>', methods=['PATCH'])
def update_planet(planet_id):
    # Buscar el planeta
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "Planeta no encontrado"}), 404

    data = request.get_json()

    # Actualizar solo si el campo viene en el JSON
    if "name" in data:
        planet.name = data["name"]

    db.session.commit()
    return jsonify({"msg": "Planeta actualizado", "planet": planet.serialize()}), 200

  

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
