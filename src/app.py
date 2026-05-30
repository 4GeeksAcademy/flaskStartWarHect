"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity # 1. Importa aquí
from utils import APIException, generate_sitemap

app = Flask(__name__) # 2. Define app primero
app.url_map.strict_slashes = False

# ... (tu configuración de base de datos) ...
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Inicializa las extensiones
from models import db, User, Character, Planet, Favorite # Importa db aquí
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)

# 4. Inicializa JWTManager justo después de la app
jwt = JWTManager(app)

# 5. Finalmente importa admin.py
from admin import setup_admin
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


@app.route('/planet/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    # 1. Buscar el planeta en la base de datos
    planet = Planet.query.get(planet_id)
    
    # 2. Verificar si existe
    if planet is None:
        return jsonify({"msg": "Planeta no encontrado"}), 404
    
    # 3. Eliminar el registro y confirmar cambios
    db.session.delete(planet)
    db.session.commit()
    
    return jsonify({"msg": "Planeta eliminado correctamente"}), 200


@app.route('/user/<int:user_id>', methods=['GET'])
def get_single_user(user_id):
    # Buscamos al usuario en la base de datos
    user = User.query.get(user_id)
    
    # Si no existe, devolvemos un 404
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    # Si existe, lo serializamos y lo devolvemos
    return jsonify(user.serialize()), 200


@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet = Planet.query.get(planet_id)
    
    if planet is None:
        return jsonify({"msg": "Planeta no encontrado"}), 404
        
    return jsonify(planet.serialize()), 200

@app.route('/personajes', methods=['GET'])
def get_all_personajes():
    todos_los_personajes = Personajes.query.all()
    results = [p.serialize() for p in todos_los_personajes]
    return jsonify(results), 200

@app.route('/personajes/<int:personaje_id>', methods=['GET'])
def get_single_personaje(personajes_id):
    p = Personajes.query.get(personajes_id)
    if p is None:
        return jsonify({"msg": "Personaje no encontrado"}), 404
    return jsonify(p.serialize()), 200

@app.route('/personajes', methods=['POST'])
def create_personaje():
    data = request.get_json()
    new_personaje = Personajes(
        name=data.get("name"),
        gender=data.get("gender"),
        hair_color=data.get("hair_color")
    )
    db.session.add(new_personajes)
    db.session.commit()
    return jsonify({"msg": "Personaje creado"}), 201


@app.route('/favorite', methods=['POST'])
@jwt_required()
def add_favorite():
    # 1. Obtener datos del usuario y del JSON
    user_id = get_jwt_identity()
    data = request.get_json()
    
    # 2. Creamos la lógica para saber qué tipo de favorito es
    # Asegúrate de que los nombres de los campos coincidan con tu modelo Favorite
    new_favorite = Favorite(
        user_id=user_id,
        personaje_id=data.get("personaje_id"), # Opcional: puede ser None
        planet_id=data.get("planet_id")        # Opcional: puede ser None
    )
    
    db.session.add(new_favorite)
    db.session.commit()
    
    return jsonify({"msg": "Favorito guardado correctamente"}), 201

@app.route('/user/favorites', methods=['GET'])
@jwt_required()
def get_user_favorites():
    # 1. Obtenemos el ID del usuario desde el token
    user_id = get_jwt_identity()
    
    # 2. Buscamos al usuario en la base de datos
    user = User.query.get(user_id)
    
    if user is None:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    # 3. Construimos la respuesta personalizada
    # Asumiendo que en tu modelo User tienes relaciones llamadas 'favoritos_personaje' y 'favoritos_planeta'
    response = {
        "user_email": user.email,
        "favoritos_personajes": [f.personaje.serialize() for f in user.favoritos if f.personaje_id is not None],
        "favoritos_planetas": [f.planeta.serialize() for f in user.favoritos if f.planeta_id is not None]
    }
    
    return jsonify(response), 200

@app.route('/favorite/personaje/<int:personaje_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_personaje(personaje_id):
    user_id = get_jwt_identity()
    
    # Buscamos el favorito que coincida con este usuario y este personaje
    favorite = Favorite.query.filter_by(user_id=user_id, personaje_id=personaje_id).first()
    
    if favorite is None:
        return jsonify({"msg": "Favorito no encontrado"}), 404
        
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({"msg": "Personaje eliminado de favoritos"}), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite_planet(planet_id):
    user_id = get_jwt_identity()
    
    # Buscamos el favorito que coincida con este usuario y este planeta
    favorite = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    
    if favorite is None:
        return jsonify({"msg": "Favorito no encontrado"}), 404
        
    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({"msg": "Planeta eliminado de favoritos"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)


