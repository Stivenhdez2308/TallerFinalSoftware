import smtplib
from pymongo import MongoClient
from bson.objectid import ObjectId
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

class Database:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="biblioteca"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.reservas = self.db["reservas"]
        self.usuarios = self.db["usuarios"]
        self.libros = self.db["libros"]
        self.email_user = "stivehdez23@gmail.com"
        self.email_password = "ruwl fyrb heqd ngwx"

    # Método para enviar correos electrónicos
    def send_email(self, to_email, subject, message):
        msg = MIMEMultipart()
        msg['From'] = self.email_user
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(message, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            print(f"Correo enviado a {to_email}")
        except Exception as e:
            print(f"Error al enviar el correo: {e}")

    # Métodos para la colección de reservas
    def create_reserva(self, reserva):
        # Calcular la fecha máxima de devolución
        fecha_reserva = datetime.strptime(reserva['fecha'], '%Y-%m-%d')
        fecha_devolucion_maxima = fecha_reserva + timedelta(days=reserva['dias_reserva'])
        reserva['fecha_devolucion_maxima'] = fecha_devolucion_maxima.strftime('%Y-%m-%d')
        reserva['recordatorio_enviado'] = False  # Añadir el campo recordatorio_enviado
        reserva_id = self.reservas.insert_one(reserva).inserted_id
        # Enviar correo de notificación solo si se realizó la reserva con éxito
        usuario = self.get_usuario(reserva['usuario_id'])
        libro = self.get_libro(reserva['libro_id'])
        if usuario and libro:
            to_email = usuario['email']
            subject = "Reserva de Libro Confirmada"
            message = (f"Hola {usuario['nombre']},\n\n"
                       f"Tu reserva del libro '{libro['titulo']}' ha sido realizada con éxito.\n"
                       f"Fecha de reserva: {reserva['fecha']}\n"
                       f"Días de reserva: {reserva['dias_reserva']}\n"
                       f"Fecha límite: {(datetime.strptime(reserva['fecha'], '%Y-%m-%d') + timedelta(days=reserva['dias_reserva'])).strftime('%Y-%m-%d')}\n\n"
                       f"Gracias por usar nuestro servicio de biblioteca.\n\n"
                       f"Saludos,\nTu biblioteca de confianza.")
            self.send_email(to_email, subject, message)
        return reserva_id

    def read_reservas(self):
        return list(self.reservas.find())

    def update_reserva(self, reserva_id, updated_reserva):
        return self.reservas.update_one({"_id": ObjectId(reserva_id)}, {"$set": updated_reserva})

    def delete_reserva(self, reserva_id):
        return self.reservas.delete_one({"_id": ObjectId(reserva_id)})

    # Métodos para la colección de usuarios
    def create_usuario(self, usuario):
        return self.usuarios.insert_one(usuario).inserted_id

    def read_usuarios(self):
        return list(self.usuarios.find())

    def update_usuario(self, usuario_id, updated_usuario):
        return self.usuarios.update_one({"_id": ObjectId(usuario_id)}, {"$set": updated_usuario})

    def delete_usuario(self, usuario_id):
        return self.usuarios.delete_one({"_id": ObjectId(usuario_id)})

    def get_usuario(self, usuario_id):
        return self.usuarios.find_one({"_id": ObjectId(usuario_id)})

    def find_usuario_by_documento(self, documento):
        return self.usuarios.find_one({"documento_identidad": documento})

    # Métodos para la colección de libros
    def create_libro(self, libro):
        return self.libros.insert_one(libro).inserted_id

    def read_libros(self):
        return list(self.libros.find())

    def update_libro(self, libro_id, updated_libro):
        return self.libros.update_one({"_id": ObjectId(libro_id)}, {"$set": updated_libro})

    def delete_libro(self, libro_id):
        return self.libros.delete_one({"_id": ObjectId(libro_id)})

    def get_libro(self, libro_id):
        return self.libros.find_one({"_id": ObjectId(libro_id)})

    def find_reservas_by_usuario(self, usuario_id):
        return list(self.reservas.find({"usuario_id": ObjectId(usuario_id)}))