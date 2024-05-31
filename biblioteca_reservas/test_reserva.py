import sys
import pytest
from PyQt5.QtCore import Qt
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from db import Database
from ui import ReservaUI
from PyQt5.QtTest import QTest
from PyQt5.QtWidgets import QApplication, QInputDialog, QMessageBox


@pytest.fixture(scope='module')
def db():
    # Configuración de la base de datos de prueba
    client = MongoClient("mongodb://localhost:27017/")
    test_db = client["biblioteca"]
    database = Database(uri="mongodb://localhost:27017/", db_name="biblioteca")
    yield database
    # Limpieza de la base de datos después de las pruebas
    client.drop_database("biblioteca")
    client.close()

@pytest.fixture(scope='module')
def app():
    # Inicializar la aplicación de PyQt para pruebas de interfaz
    qt_app = QApplication([])
    ui = ReservaUI()
    yield ui
    qt_app.quit()

def test_create_usuario(db):
    usuario = {
        "nombre": "Juan Perez",
        "email": "juan.perez@example.com",
        "documento_identidad": "1234567890",
        "telefono": "123456789"
    }
    usuario_id = db.create_usuario(usuario)
    fetched_usuario = db.get_usuario(usuario_id)
    assert fetched_usuario is not None
    assert fetched_usuario['nombre'] == "Juan Perez"
    assert fetched_usuario['email'] == "juan.perez@example.com"

def test_create_libro(db):
    libro = {
        "titulo": "Cien Años de Soledad",
        "autor": "Gabriel Garcia Marquez",
        "isbn": "978-3-16-148410-0"
    }
    libro_id = db.create_libro(libro)
    fetched_libro = db.get_libro(libro_id)
    assert fetched_libro is not None
    assert fetched_libro['titulo'] == "Cien Años de Soledad"
    assert fetched_libro['autor'] == "Gabriel Garcia Marquez"

def test_create_reserva(db):
    usuario = {
        "nombre": "Maria Lopez",
        "email": "maria.lopez@example.com",
        "documento_identidad": "0987654321",
        "telefono": "987654321"
    }
    usuario_id = db.create_usuario(usuario)
    libro = {
        "titulo": "El Amor en los Tiempos del Cólera",
        "autor": "Gabriel Garcia Marquez",
        "isbn": "978-3-16-148410-1"
    }
    libro_id = db.create_libro(libro)
    reserva = {
        "usuario_id": usuario_id,
        "libro_id": libro_id,
        "fecha": datetime.now().strftime('%Y-%m-%d'),
        "dias_reserva": 15
    }
    reserva_id = db.create_reserva(reserva)
    fetched_reserva = db.reservas.find_one({"_id": reserva_id})
    assert fetched_reserva is not None
    assert fetched_reserva['usuario_id'] == usuario_id
    assert fetched_reserva['libro_id'] == libro_id

def test_read_usuarios(db):
    usuarios = db.read_usuarios()
    assert isinstance(usuarios, list)

def test_read_libros(db):
    libros = db.read_libros()
    assert isinstance(libros, list)

def test_read_reservas(db):
    reservas = db.read_reservas()
    assert isinstance(reservas, list)

def test_update_usuario(db):
    usuario = db.read_usuarios()[0]
    usuario_id = usuario['_id']
    db.update_usuario(usuario_id, {"telefono": "1122334455"})
    updated_usuario = db.get_usuario(usuario_id)
    assert updated_usuario['telefono'] == "1122334455"

def test_update_libro(db):
    libro = db.read_libros()[0]
    libro_id = libro['_id']
    db.update_libro(libro_id, {"isbn": "123-4-56-789012-3"})
    updated_libro = db.get_libro(libro_id)
    assert updated_libro['isbn'] == "123-4-56-789012-3"

def test_update_reserva(db):
    reserva = db.read_reservas()[0]
    reserva_id = reserva['_id']
    db.update_reserva(reserva_id, {"dias_reserva": 30})
    updated_reserva = db.reservas.find_one({"_id": reserva_id})
    assert updated_reserva['dias_reserva'] == 30

def test_delete_usuario(db):
    usuario = db.read_usuarios()[0]
    usuario_id = usuario['_id']
    db.delete_usuario(usuario_id)
    deleted_usuario = db.get_usuario(usuario_id)
    assert deleted_usuario is None

def test_delete_libro(db):
    libro = db.read_libros()[0]
    libro_id = libro['_id']
    db.delete_libro(libro_id)
    deleted_libro = db.get_libro(libro_id)
    assert deleted_libro is None

def test_delete_reserva(db):
    reserva = db.read_reservas()[0]
    reserva_id = reserva['_id']
    db.delete_reserva(reserva_id)
    deleted_reserva = db.reservas.find_one({"_id": reserva_id})
    assert deleted_reserva is None

def test_ui_add_usuario(app):
    # Simulando la adición automática de un usuario
    usuario_data = {
        "nombre": "Usuario de Prueba",
        "email": "usuario.prueba@example.com",
        "documento_identidad": "123456789",
        "telefono": "987654321"
    }
    app.db.create_usuario(usuario_data)
    app.load_usuarios()
    assert app.usuario_combo.count() > 0

def test_ui_add_libro(app):
    # Simulando la adición automática de un libro
    libro_data = {
        "titulo": "Libro de Prueba",
        "autor": "Autor de Prueba",
        "isbn": "1234567890"
    }
    app.db.create_libro(libro_data)
    app.load_libros()
    assert app.libro_combo.count() > 0

def test_ui_add_reserva(app):
    app.load_usuarios()
    app.load_libros()
    if app.usuario_combo.count() > 0 and app.libro_combo.count() > 0:
        app.usuario_combo.setCurrentIndex(0)
        app.libro_combo.setCurrentIndex(0)
        app.dias_reserva_input.setValue(10)
        app.add_reserva()
        assert app.table.rowCount() > 0

def test_ui_update_reserva(app):
    app.load_reservas()
    if app.table.rowCount() > 0:
        app.table.selectRow(0)
        app.dias_reserva_input.setValue(20)
        app.update_reserva()
        reserva_id = ObjectId(app.table.item(0, 0).text())
        updated_reserva = app.db.reservas.find_one({"_id": reserva_id})
        assert updated_reserva['dias_reserva'] == 20

def test_load_reservas_displays_reservations(app, db):
    # Eliminar todas las reservas existentes
    reservas = db.read_reservas()
    for reserva in reservas:
        db.delete_reserva(reserva['_id'])

    # Crear algunos datos de prueba
    usuario_data = {
        "nombre": "Usuario de Prueba",
        "email": "usuario.prueba@example.com",
        "documento_identidad": "123456789",
        "telefono": "987654321"
    }
    usuario_id = db.create_usuario(usuario_data)

    libro_data = {
        "titulo": "Libro de Prueba",
        "autor": "Autor de Prueba",
        "isbn": "1234567890"
    }
    libro_id = db.create_libro(libro_data)

    reserva_data = {
        "usuario_id": usuario_id,
        "libro_id": libro_id,
        "fecha": datetime.now().strftime('%Y-%m-%d'),
        "dias_reserva": 15
    }
    reserva_id = db.create_reserva(reserva_data)

    app.load_reservas()

    assert app.table.rowCount() == 1
    assert app.table.item(0, 0).text() == str(reserva_id)
    assert app.table.item(0, 1).text() == f"{usuario_data['nombre']} - {usuario_data['documento_identidad']}"
    assert app.table.item(0, 2).text() == f"{libro_data['titulo']} - {libro_data['autor']}"
    assert app.table.item(0, 3).text() == reserva_data['fecha']

def test_load_reservas_calculates_remaining_days(app, db):
    # Eliminar todas las reservas existentes
    reservas = db.read_reservas()
    for reserva in reservas:
        db.delete_reserva(reserva['_id'])

    # Crear algunos datos de prueba
    usuario_data = {
        "nombre": "Usuario de Prueba",
        "email": "usuario.prueba@example.com",
        "documento_identidad": "123456789",
        "telefono": "987654321"
    }
    usuario_id = db.create_usuario(usuario_data)

    libro_data = {
        "titulo": "Libro de Prueba",
        "autor": "Autor de Prueba",
        "isbn": "1234567890"
    }
    libro_id = db.create_libro(libro_data)

    reserva_data = {
        "usuario_id": usuario_id,
        "libro_id": libro_id,
        "fecha": (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
        "dias_reserva": 15
    }
    reserva_id = db.create_reserva(reserva_data)

    app.load_reservas()

    assert app.table.rowCount() == 1
    dias_restantes = int(app.table.item(0, 4).text())
    fecha_vencimiento = datetime.strptime(app.table.item(0, 5).text(), '%Y-%m-%d')

    assert dias_restantes == 5  # Asumiendo que la reserva se realizó hace 10 días y tiene 15 días de duración
    assert fecha_vencimiento == datetime.strptime(reserva_data['fecha'], '%Y-%m-%d') + timedelta(days=reserva_data['dias_reserva'])

def test_load_reservas_sends_reminder_email(app, db, monkeypatch):
    # Crear algunos datos de prueba
    usuario_data = {
        "nombre": "Usuario de Prueba",
        "email": "usuario.prueba@example.com",
        "documento_identidad": "123456789",
        "telefono": "987654321"
    }
    usuario_id = db.create_usuario(usuario_data)

    libro_data = {
        "titulo": "Libro de Prueba",
        "autor": "Autor de Prueba",
        "isbn": "1234567890"
    }
    libro_id = db.create_libro(libro_data)

    reserva_data = {
        "usuario_id": usuario_id,
        "libro_id": libro_id,
        "fecha": (datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d'),
        "dias_reserva": 15
    }
    reserva_id = db.create_reserva(reserva_data)

    # Monkeypatch para simular el envío de correo electrónico
    email_sent = False

    def mock_send_email(to_email, subject, message):
        nonlocal email_sent
        email_sent = True

    monkeypatch.setattr(app.db, 'send_email', mock_send_email)

    app.load_reservas()

    assert email_sent


########

