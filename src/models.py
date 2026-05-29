from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from eralchemy2 import render_er

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    favorite: Mapped[list["Favorite"]] = relationship(back_populates="user")

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name
        }

class Character(db.Model):
    __tablename__ = 'character'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    favorite: Mapped[list["Favorite"]] = relationship(back_populates="character")
    


    def serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Planet(db.Model):
    __tablename__ = 'planet'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    favorite: Mapped[list["Favorite"]] = relationship(back_populates="planet")
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Personajes(db.Model):
    __tablename__ = 'personajes'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Relación con favoritos
    favorite: Mapped[list["Favorite"]] = relationship(back_populates="personajes")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }


class Favorite(db.Model):
    __tablename__ = 'favorite'
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Llaves foráneas
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    character_id: Mapped[int | None] = mapped_column(ForeignKey("character.id"), nullable=True)
    personaje_id: Mapped[int | None] = mapped_column(ForeignKey("personajes.id"), nullable=True)
    planet_id: Mapped[int | None] = mapped_column(ForeignKey("planet.id"), nullable=True)
    
    # Relaciones únicas
    user: Mapped["User"] = relationship(back_populates="favorite")
    character: Mapped["Character"] = relationship(back_populates="favorite")
    personajes: Mapped["Personajes"] = relationship(back_populates="favorite")
    planet: Mapped["Planet"] = relationship(back_populates="favorite")


try:
    render_er(db.Model, 'diagram.png')
    print("Diagrama generado exitosamente como diagram.png")
except Exception as e:
    print(f"Error al generar el diagrama: {e}")