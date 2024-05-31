import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QTableWidget, \
    QTableWidgetItem, QMessageBox, QComboBox, QInputDialog, QDateEdit, QSpinBox, QLabel, QDialog, QHBoxLayout, QHeaderView
from PyQt5.QtCore import QDate, Qt
from db import Database
from bson.objectid import ObjectId
from datetime import datetime, timedelta

class ReservaUI(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Sistema de Reservas de Biblioteca')

        self.layout = QVBoxLayout()
        self.form_layout = QFormLayout()

        self.usuario_combo = QComboBox()
        self.libro_combo = QComboBox()
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())

        self.load_usuarios()
        self.load_libros()

        self.form_layout.addRow('Usuario', self.usuario_combo)
        self.form_layout.addRow('Libro', self.libro_combo)
        self.form_layout.addRow('Fecha', self.fecha_input)

        self.add_button = QPushButton('Agregar Reserva')
        self.update_button = QPushButton('Actualizar Reserva')
        self.delete_button = QPushButton('Eliminar Reserva')
        self.delete_usuario_button = QPushButton('Eliminar Usuario')
        self.delete_libro_button = QPushButton('Eliminar Libro')
        self.add_usuario_button = QPushButton('Agregar Usuario')
        self.add_libro_button = QPushButton('Agregar Libro')

        self.search_layout = QFormLayout()
        self.search_input = QLineEdit()
        self.search_button = QPushButton('Buscar Reservas por Documento')
        self.search_layout.addRow('Documento de Identidad', self.search_input)
        self.search_layout.addRow(self.search_button)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Usuario', 'Libro', 'Fecha', 'Días Restantes', 'Fecha Máxima de Devolución'])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # Deshabilitar la edición de celdas
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)  # Ajustar automáticamente el ancho de las columnas

        # Centrar el contenido de todas las celdas
        for i in range(self.table.columnCount()):
            self.table.horizontalHeaderItem(i).setTextAlignment(Qt.AlignCenter)

        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.add_button)
        self.layout.addWidget(self.update_button)
        self.layout.addWidget(self.delete_button)
        self.layout.addWidget(self.delete_usuario_button)
        self.layout.addWidget(self.delete_libro_button)
        self.layout.addWidget(self.add_usuario_button)
        self.layout.addWidget(self.add_libro_button)
        self.layout.addLayout(self.search_layout)
        self.layout.addWidget(self.table)

        self.setLayout(self.layout)

        self.add_button.clicked.connect(self.add_reserva)
        self.update_button.clicked.connect(self.update_reserva)
        self.delete_button.clicked.connect(self.delete_reserva)
        self.delete_usuario_button.clicked.connect(self.delete_usuario)
        self.delete_libro_button.clicked.connect(self.delete_libro)
        self.add_usuario_button.clicked.connect(self.add_usuario)
        self.add_libro_button.clicked.connect(self.add_libro)
        self.search_button.clicked.connect(self.search_reservas)

        self.dias_reserva_input = QSpinBox()
        self.dias_reserva_input.setMinimum(1)
        self.dias_reserva_input.setMaximum(90)  # Ajusta el valor máximo según tus necesidades
        self.form_layout.addRow('Días de Reserva', self.dias_reserva_input)

        self.table.setColumnWidth(0, 150)  # Ajusta el ancho de la columna 'ID'
        self.table.setColumnWidth(1, 300)  # Ajusta el ancho de la columna 'Usuario'
        self.table.setColumnWidth(2, 300)  # Ajusta el ancho de la columna 'Libro'
        self.table.setColumnWidth(3, 150)  # Ajusta el ancho de la columna 'Fecha'
        self.table.setColumnWidth(4, 150)  # Ajusta el ancho de la columna 'Días Restantes'
        self.table.verticalHeader().setDefaultSectionSize(30)  # Ajusta el alto de las filas

        self.reload_button = QPushButton('Recargar')
        self.layout.addWidget(self.reload_button)
        self.reload_button.clicked.connect(self.reload_app)

        self.load_reservas()

    def load_usuarios(self):
        self.usuario_combo.clear()
        usuarios = self.db.read_usuarios()
        for usuario in usuarios:
            self.usuario_combo.addItem(f"{usuario['nombre']} - {usuario['documento_identidad']}", usuario['_id'])

    def load_libros(self):
        self.libro_combo.clear()
        libros = self.db.read_libros()
        for libro in libros:
            self.libro_combo.addItem(f"{libro['titulo']} - {libro['autor']}", libro['_id'])

    def load_reservas(self):
        self.table.setRowCount(0)
        reservas = self.db.read_reservas()
        for reserva in reservas:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            self.table.setItem(row_position, 0, QTableWidgetItem(str(reserva['_id'])))
            usuario = self.db.get_usuario(reserva['usuario_id'])
            libro = self.db.get_libro(reserva['libro_id'])
            if usuario and libro:
                self.table.setItem(row_position, 1,
                                   QTableWidgetItem(f"{usuario['nombre']} - {usuario['documento_identidad']}"))
                self.table.setItem(row_position, 2, QTableWidgetItem(f"{libro['titulo']} - {libro['autor']}"))
                self.table.setItem(row_position, 3, QTableWidgetItem(reserva['fecha']))
                fecha_reserva = datetime.strptime(reserva['fecha'], "%Y-%m-%d")
                fecha_vencimiento = fecha_reserva + timedelta(days=reserva['dias_reserva'])
                # Calcular los días restantes considerando también las horas
                dias_restantes = (fecha_vencimiento - datetime.now()).total_seconds() / 3600 / 24
                # Redondear hacia arriba para asegurarnos de que se envíe el correo cuando quede exactamente 1 día
                if dias_restantes <= 1:
                    dias_restantes = 1
                else:
                    dias_restantes = int(dias_restantes) + 1
                self.table.setItem(row_position, 4, QTableWidgetItem(str(dias_restantes)))
                self.table.setItem(row_position, 5, QTableWidgetItem(fecha_vencimiento.strftime("%Y-%m-%d")))
                # Enviar un correo electrónico de recordatorio solo cuando quede 1 día antes de la devolución
                if dias_restantes == 1 and not reserva.get('recordatorio_enviado', False):
                    to_email = usuario['email']
                    subject = "Recordatorio de Devolución de Libro"
                    message = (f"Hola {usuario['nombre']},\n\n"
                               f"Este es un recordatorio de que debes devolver el libro '{libro['titulo']}' "
                               f"mañana, {fecha_vencimiento.strftime('%Y-%m-%d')}.\n\n"
                               f"Gracias por utilizar nuestro servicio de biblioteca.\n\n"
                               f"Saludos,\nTu biblioteca de confianza.")
                    self.db.send_email(to_email, subject, message)
                    # Marcar el recordatorio como enviado en la base de datos
                    self.db.update_reserva(reserva['_id'], {'recordatorio_enviado': True})
        # Centrar el contenido de todas las celdas
        for i in range(self.table.rowCount()):
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item:
                    item.setTextAlignment(Qt.AlignCenter)

    def add_reserva(self):
        usuario_id = self.usuario_combo.currentData()
        libro_id = self.libro_combo.currentData()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d")
        dias_reserva = self.dias_reserva_input.value()

        if fecha_reserva > datetime.now():
            QMessageBox.warning(self, "Error", "La fecha de la reserva no puede ser después de la fecha actual.")
            return

        reserva = {
            "usuario_id": usuario_id,
            "libro_id": libro_id,
            "fecha": fecha,
            "dias_reserva": dias_reserva
        }
        self.db.create_reserva(reserva)
        self.load_reservas()

    def update_reserva(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            reserva_id = ObjectId(self.table.item(selected_row, 0).text())
            usuario_id = self.usuario_combo.currentData()
            libro_id = self.libro_combo.currentData()
            fecha = self.fecha_input.date().toString("yyyy-MM-dd")
            fecha_reserva = datetime.strptime(fecha, "%Y-%m-%d")
            dias_reserva = self.dias_reserva_input.value()

            if fecha_reserva > datetime.now():
                QMessageBox.warning(self, "Error", "La fecha de la reserva no puede ser después de la fecha actual.")
                return

            updated_reserva = {
                "usuario_id": usuario_id,
                "libro_id": libro_id,
                "fecha": fecha,
                "dias_reserva": dias_reserva
            }
            print(f"Actualizando reserva con valores: {updated_reserva}")
            self.db.update_reserva(reserva_id, updated_reserva)
            self.load_reservas()

    def delete_reserva(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            reserva_id = ObjectId(self.table.item(selected_row, 0).text())
            confirmation, ok = QInputDialog.getText(self, "Confirmar Eliminación", "Ingrese 'CONFIRMAR' para eliminar:")
            if ok and confirmation == "CONFIRMAR":
                try:
                    self.db.delete_reserva(reserva_id)
                    self.load_reservas()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo eliminar la reserva: {e}")
            else:
                QMessageBox.warning(self, "Cancelado", "La eliminación de la reserva ha sido cancelada.")

    def delete_usuario(self):
        usuarios = self.db.read_usuarios()
        usuarios_dict = {f"{usuario['nombre']} - {usuario['documento_identidad']}": usuario['_id'] for usuario in
                         usuarios}

        dialog = QDialog(self)
        dialog.setWindowTitle('Eliminar Usuario')
        layout = QVBoxLayout(dialog)

        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_input = QLineEdit()
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)

        user_combo = QComboBox()
        for user in usuarios_dict.keys():
            user_combo.addItem(user)
        layout.addWidget(user_combo)

        delete_button = QPushButton('Eliminar')
        layout.addWidget(delete_button)

        def filter_users():
            search_text = search_input.text().lower()
            user_combo.clear()
            for user in usuarios_dict.keys():
                if search_text in user.lower():
                    user_combo.addItem(user)

        search_input.textChanged.connect(filter_users)

        def confirm_delete():
            selected_user = user_combo.currentText()
            if selected_user:
                user_id = usuarios_dict[selected_user]
                confirm = QMessageBox.question(
                    self,
                    'Confirmar eliminación',
                    f"¿Estás seguro de que deseas eliminar el usuario {selected_user}?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    self.db.delete_usuario(user_id)
                    dialog.accept()
                    self.load_usuarios()
            else:
                QMessageBox.warning(self, "Error", "Seleccione un usuario para eliminar.")

        delete_button.clicked.connect(confirm_delete)
        dialog.exec_()

    def delete_libro(self):
        libros = self.db.read_libros()
        libros_dict = {f"{libro['titulo']} - {libro['autor']}": libro['_id'] for libro in libros}

        dialog = QDialog(self)
        dialog.setWindowTitle('Eliminar Libro')
        layout = QVBoxLayout(dialog)

        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar:")
        search_input = QLineEdit()
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        layout.addLayout(search_layout)

        book_combo = QComboBox()
        for book in libros_dict.keys():
            book_combo.addItem(book)
        layout.addWidget(book_combo)

        delete_button = QPushButton('Eliminar')
        layout.addWidget(delete_button)

        def filter_books():
            search_text = search_input.text().lower()
            book_combo.clear()
            for book in libros_dict.keys():
                if search_text in book.lower():
                    book_combo.addItem(book)

        search_input.textChanged.connect(filter_books)

        def confirm_delete():
            selected_book = book_combo.currentText()
            if selected_book:
                book_id = libros_dict[selected_book]
                confirm = QMessageBox.question(
                    self,
                    'Confirmar eliminación',
                    f"¿Estás seguro de que deseas eliminar el libro {selected_book}?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm == QMessageBox.Yes:
                    self.db.delete_libro(book_id)
                    dialog.accept()
                    self.load_libros()
            else:
                QMessageBox.warning(self, "Error", "Seleccione un libro para eliminar.")

        delete_button.clicked.connect(confirm_delete)
        dialog.exec_()

    def add_usuario(self):
        while True:
            nombre, nombre_ok = QInputDialog.getText(self, "Agregar Usuario", "Nombre:")
            if not nombre_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not nombre.strip():
                QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            else:
                break

        while True:
            email, email_ok = QInputDialog.getText(self, "Agregar Usuario", "Email:")
            if not email_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not email.strip():
                QMessageBox.warning(self, "Error", "El email es obligatorio.")
            else:
                break

        while True:
            documento_identidad, doc_ok = QInputDialog.getText(self, "Agregar Usuario", "Documento de Identidad:")
            if not doc_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not documento_identidad.strip():
                QMessageBox.warning(self, "Error", "El documento de identidad es obligatorio.")
            else:
                existing_usuario = self.db.find_usuario_by_documento(documento_identidad.strip())
                if existing_usuario:
                    QMessageBox.warning(self, "Error",
                                        f"El documento de identidad ya está registrado a nombre de {existing_usuario['nombre']}.")
                else:
                    break

        while True:
            telefono, tel_ok = QInputDialog.getText(self, "Agregar Usuario", "Teléfono:")
            if not tel_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not telefono.strip():
                QMessageBox.warning(self, "Error", "El teléfono es obligatorio.")
            else:
                break

        usuario = {
            "nombre": nombre.strip(),
            "email": email.strip(),
            "documento_identidad": documento_identidad.strip(),
            "telefono": telefono.strip()
        }
        self.db.create_usuario(usuario)
        self.load_usuarios()

    def add_libro(self):
        while True:
            titulo, titulo_ok = QInputDialog.getText(self, "Agregar Libro", "Título:")
            if not titulo_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not titulo.strip():
                QMessageBox.warning(self, "Error", "El título es obligatorio.")
            else:
                break

        while True:
            autor, autor_ok = QInputDialog.getText(self, "Agregar Libro", "Autor:")
            if not autor_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not autor.strip():
                QMessageBox.warning(self, "Error", "El autor es obligatorio.")
            else:
                break

        while True:
            isbn, isbn_ok = QInputDialog.getText(self, "Agregar Libro", "ISBN:")
            if not isbn_ok:
                return  # Retornar a la pantalla principal si el usuario cancela o cierra el cuadro de diálogo
            elif not isbn.strip():
                QMessageBox.warning(self, "Error", "El ISBN es obligatorio.")
            else:
                break

        libro = {
            "titulo": titulo.strip(),
            "autor": autor.strip(),
            "isbn": isbn.strip()
        }
        self.db.create_libro(libro)
        self.load_libros()

    def search_reservas(self):
        documento_identidad = self.search_input.text().strip()
        if documento_identidad:
            usuario = self.db.usuarios.find_one({"documento_identidad": documento_identidad})
            if usuario:
                usuario_id = usuario['_id']
                reservas = self.db.reservas.find({"usuario_id": usuario_id})
                self.table.setRowCount(0)
                for reserva in reservas:
                    row_position = self.table.rowCount()
                    self.table.insertRow(row_position)
                    self.table.setItem(row_position, 0, QTableWidgetItem(str(reserva['_id'])))
                    libro = self.db.get_libro(reserva['libro_id'])
                    if libro:
                        self.table.setItem(row_position, 1, QTableWidgetItem(f"{usuario['nombre']} - {usuario['documento_identidad']}"))
                        self.table.setItem(row_position, 2, QTableWidgetItem(f"{libro['titulo']} - {libro['autor']}"))
                        self.table.setItem(row_position, 3, QTableWidgetItem(reserva['fecha']))
                        fecha_reserva = datetime.strptime(reserva['fecha'], "%Y-%m-%d")
                        fecha_vencimiento = fecha_reserva + timedelta(days=reserva['dias_reserva'])
                        # Calcular los días restantes considerando también las horas
                        dias_restantes = (fecha_vencimiento - datetime.now()).total_seconds() / 3600 / 24
                        # Redondear hacia arriba para asegurarnos de que se envíe el correo cuando quede exactamente 1 día
                        if dias_restantes <= 1:
                            dias_restantes = 1
                        else:
                            dias_restantes = int(dias_restantes) + 1
                        self.table.setItem(row_position, 4, QTableWidgetItem(str(dias_restantes)))
                        self.table.setItem(row_position, 5, QTableWidgetItem(fecha_vencimiento.strftime("%Y-%m-%d")))
                # Centrar el contenido de todas las celdas
                for i in range(self.table.rowCount()):
                    for j in range(self.table.columnCount()):
                        item = self.table.item(i, j)
                        if item:
                            item.setTextAlignment(Qt.AlignCenter)
            else:
                QMessageBox.warning(self, "No encontrado", "No se encontró ningún usuario con ese documento de identidad.")
        else:
            QMessageBox.warning(self, "Error", "Por favor, ingrese un documento de identidad para buscar.")

    def reload_app(self):
        # Reiniciar los elementos de la interfaz de usuario
        self.usuario_combo.clear()
        self.libro_combo.clear()
        self.fecha_input.setDate(QDate.currentDate())
        self.dias_reserva_input.setValue(1)
        self.search_input.clear()

        # Cargar los datos actualizados
        self.load_usuarios()
        self.load_libros()
        self.load_reservas()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = ReservaUI()
    ui.show()
    sys.exit(app.exec_())