import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QListWidget, QMessageBox, QDialog, QLabel, QTimeEdit, QListWidgetItem, QDateTimeEdit
from PyQt5.QtCore import Qt, QTimer, QTime, QVariant, QDateTime
from PyQt5.QtGui import QIcon, QFont
from playsound import playsound
from datetime import timedelta

class CountdownTimer(QDialog):
    def __init__(self, deadline=None):
        super().__init__()

        self.setWindowTitle('Countdown Timer')
        self.setGeometry(400, 400, 300, 200)

        self.time_left = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        layout = QVBoxLayout()

        self.time_input = QTimeEdit()
        self.time_input.setDisplayFormat('mm:ss')
        layout.addWidget(self.time_input)

        self.timer_label = QLabel('Waktu tersisa: 00:00', self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.timer_label)

        self.deadline = deadline
        if self.deadline is not None and isinstance(self.deadline, QDateTime):
            self.timer_label.setText(f'Deadline: {self.deadline.toString("dd/MM/yyyy hh:mm")}')

        self.start_button = QPushButton('Mulai')
        self.start_button.clicked.connect(self.start_timer)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_timer)
        layout.addWidget(self.stop_button)

        self.resume_button = QPushButton('Lanjutkan')
        self.resume_button.clicked.connect(self.resume_timer)
        layout.addWidget(self.resume_button)

        self.setLayout(layout)

    def start_timer(self):
        self.time_left = self.time_input.time()
        if self.time_left.isValid() and self.time_left > QTime(0, 0):
            self.timer.start(1000)
            self.start_button.setEnabled(False)

    def stop_timer(self):
        self.timer.stop()
        self.start_button.setEnabled(True)

    def resume_timer(self):
        self.timer.start(1000)
        self.start_button.setEnabled(False)

    def update_timer(self):
        if self.time_left > QTime(0, 0):
            self.time_left = self.time_left.addSecs(-1)
            self.timer_label.setText(f'Waktu tersisa: {self.time_left.toString("mm:ss")}')
        else:
            self.timer.stop()
            self.start_button.setEnabled(True)
            self.timer_label.setText('Waktu sudah habis!')
            playsound('alarm.mp3')

class ToDoListApp(QWidget):
    def __init__(self):
        super().__init__()
        try:
            # Membuat koneksi ke database
            self.connection = sqlite3.connect('todolist.db')
            self.create_table()

        except sqlite3.Error as e:
            QMessageBox.critical(self, 'Kesalahan Database', f'Terdapat kesalahan saat membuka database: {str(e)}')
            sys.exit(1)

        self.task_counter = 1
        self.input_text = ""

        # Set ukuran tetap jendela
        self.setMinimumSize(600, 400)

        self.initUI()

    def show_completed_tasks(self):
        completed_tasks_window = QDialog(self)
        completed_tasks_window.setWindowTitle('History Tugas Selesai')
        completed_tasks_window.setGeometry(200, 200, 400, 300)

        completed_tasks_list = QListWidget(completed_tasks_window)

        # Mengambil data dari database dan menampilkan dalam QListWidget
        with self.connection:
            cursor = self.connection.execute('SELECT id, task, completion_time FROM completed_tasks')
            completed_tasks = cursor.fetchall()

            for task_id, task, completion_time in completed_tasks:
                item_text = f'{task} - Completed at: {completion_time}'
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, QVariant(task_id))  # Menyimpan ID tugas untuk penghapusan

                completed_tasks_list.addItem(item)

        layout = QVBoxLayout()

        # Tambahkan tombol hapus histori dengan gaya CSS
        delete_button = QPushButton('Hapus Histori Tugas', completed_tasks_window)
        delete_button.clicked.connect(lambda: self.delete_completed_task(completed_tasks_list))
        delete_button.setStyleSheet("background-color: #FF0000; color: white;")  # Ganti #FF0000 dengan kode warna yang diinginkan
        layout.addWidget(delete_button)

        layout.addWidget(completed_tasks_list)
        completed_tasks_window.setLayout(layout)

        completed_tasks_window.exec_()

    def delete_completed_task(self, completed_tasks_list):
        selected_item = completed_tasks_list.currentItem()
        if selected_item is not None:
            task_id = selected_item.data(Qt.UserRole)
            result = QMessageBox.question(
                self, 'Hapus Histori', f'Apakah Anda yakin ingin menghapus histori tugas ini?', QMessageBox.Yes | QMessageBox.No
            )
            if result == QMessageBox.Yes:
                completed_tasks_list.takeItem(completed_tasks_list.row(selected_item))
                self.delete_completed_task_from_db(task_id)
        else:
            QMessageBox.warning(self, 'Peringatan', 'Pilih histori yang akan dihapus terlebih dahulu.')

    def delete_completed_task_from_db(self, task_id):
        # Menghapus tugas yang telah diselesaikan dari database berdasarkan ID
        with self.connection:
            self.connection.execute('DELETE FROM completed_tasks WHERE id = ?', (task_id,))

    def create_table(self):
        # Membuat tabel 'completed_tasks' jika belum ada
        with self.connection:
            self.connection.execute('''
                CREATE TABLE IF NOT EXISTS completed_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    completion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def save_completed_task_to_db(self, task):
        # Menyimpan tugas yang telah diselesaikan ke dalam database
        with self.connection:
            self.connection.execute('INSERT INTO completed_tasks (task) VALUES (?)', (task,))

    def update_date_label(self):
        current_datetime = QDateTime.currentDateTime()
        date_text = current_datetime.toString('dddd, dd MMMM yyyy - hh:mm:ss')
        self.date_label.setText(date_text)

    def initUI(self):
        layout = QVBoxLayout()

        self.setWindowTitle('Aplikasi To-Do List')
        self.setGeometry(100, 100, 400, 300)

        title_label = QLabel('STUDYMATE', self)

        title_gradient = 'QLabel { color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00BFFF, stop:1 #000080); background-color: transparent; }'
        title_label.setStyleSheet(title_gradient)

        font = QFont('Sacramento', 20, QFont.Bold)
        title_label.setFont(font)

        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Tambahkan label untuk menampilkan hari, tanggal, bulan, dan tahun
        self.date_label = QLabel(self)
        self.date_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.date_label)

        self.task_list = QListWidget(self)
        self.task_input = None

        reset_button = QPushButton('Reset Tugas', self)
        reset_button.clicked.connect(self.reset_task_list)

        layout.addWidget(reset_button)
        layout.addWidget(self.task_list)

        reset_button.setGeometry(10, 10, 200, 50)
        self.task_list.setGeometry(10, 60, 300, 150)

        button_layout = QHBoxLayout()

        self.add_button = QPushButton('Tambah Tugas', self)
        self.add_button.clicked.connect(self.show_task_input)
        self.add_button.setStyleSheet("background-color: #00A9FF; color: white; padding: 8px; border-radius: 8px;")
        button_layout.addWidget(self.add_button)
        self.add_button.setCursor(Qt.PointingHandCursor)

        self.remove_button = QPushButton('Hapus Tugas', self)
        self.remove_button.setStyleSheet("background-color: #00A9FF; color: white; padding: 8px; border-radius: 8px;")
        self.remove_button.clicked.connect(self.remove_task)
        button_layout.addWidget(self.remove_button)
        self.remove_button.setCursor(Qt.PointingHandCursor)

        self.complete_button = QPushButton('Selesaikan Tugas', self)
        self.complete_button.setStyleSheet("background-color: #00A9FF; color: white; padding: 8px; border-radius: 8px;")
        self.complete_button.clicked.connect(self.complete_task)
        self.complete_button.setEnabled(False)
        button_layout.addWidget(self.complete_button)
        self.complete_button.setCursor(Qt.PointingHandCursor)

        self.timer_button = QPushButton('Kerjakan Tugas', self)
        self.timer_button.setStyleSheet("background-color: #00A9FF; color: white; padding: 8px; border-radius: 8px;")
        self.timer_button.clicked.connect(self.open_timer_window)
        button_layout.addWidget(self.timer_button)
        self.timer_button.setCursor(Qt.PointingHandCursor)

        history_button = QPushButton('Lihat History', self)
        history_button.clicked.connect(self.show_completed_tasks)
        history_button.setStyleSheet("background-color: #00A9FF; color: white; padding: 8px; border-radius: 8px;")
        button_layout.addWidget(history_button)
        history_button.setCursor(Qt.PointingHandCursor)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Mulai timer untuk memperbarui label setiap detik
        self.date_timer = QTimer(self)
        self.date_timer.timeout.connect(self.update_date_label)
        self.date_timer.start(1000)

        self.load_tasks()
        self.task_list.itemSelectionChanged.connect(self.check_selection)

    def show_task_input(self):
        if self.task_input is None:
            self.task_input = QLineEdit(self)
            self.task_input.setPlaceholderText('Tambahkan tugas...')
            layout = self.layout()
            layout.insertWidget(2, self.task_input)

            # input untuk deadline
            self.deadline_input = QDateTimeEdit(self)
            self.deadline_input.setDisplayFormat('dd/MM/yyyy hh:mm')
            self.deadline_input.setDateTime(QDateTime.currentDateTime())  # Set default ke waktu sekarang
            layout.insertWidget(3, self.deadline_input)

            self.add_button.setText('Simpan')
            self.add_button.clicked.disconnect(self.show_task_input)
            self.add_button.clicked.connect(self.add_task)
        else:
            self.add_task()

    def add_task(self):
        if self.task_input is not None and self.deadline_input is not None:
            self.input_text = self.task_input.text()
            self.task_input.deleteLater()
            self.task_input = None

            # mengambil deadline dari input
            deadline = self.deadline_input.dateTime()

            task = self.input_text
            if task:
                task_with_number = f'{self.task_counter}. {task}'

                # menambahkan deadline ke dalam teks tugas
                task_with_number_and_deadline = f'{task_with_number} - Deadline: {deadline.toString("dd/MM/yyyy hh:mm")}'

                item = QListWidgetItem(task_with_number_and_deadline)

                # Mengatur deadline pada item
                self.set_deadline(item, deadline)

                self.task_list.addItem(item)

                if self.check_deadline_alert(item):
                    self.activate_deadline_alert()

                self.save_task(task_with_number_and_deadline)
                self.input_text = ""
                self.add_button.setText('Tambah Tugas')
                self.add_button.clicked.disconnect(self.add_task)
                self.add_button.clicked.connect(self.show_task_input)
                self.task_counter += 1
            else:
                QMessageBox.critical(self, 'Kesalahan', 'Tidak dapat menambahkan tugas kosong.')

        else:
            QMessageBox.critical(self, 'Kesalahan', 'Pastikan untuk mengisi tugas dan deadline.')

    def remove_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item is not None:
            result = QMessageBox.question(self, 'Hapus Tugas', f'Apakah Anda yakin ingin menghapus tugas:\n{selected_item.text()}?', QMessageBox.Yes | QMessageBox.No)
            if result == QMessageBox.Yes:
                self.task_list.takeItem(self.task_list.row(selected_item))
                self.save_tasks()
                self.complete_button.setEnabled(False)
        else:
            QMessageBox.warning(self, 'Peringatan', 'Pilih tugas yang akan dihapus terlebih dahulu.')

    def complete_task(self):
        selected_item = self.task_list.currentItem()
        if selected_item is not None:
            task_text = selected_item.text()
            self.save_completed_task_to_db(task_text)
            new_window = QDialog(self)
            new_window.setWindowTitle('Tugas Selesai')
            new_window.setGeometry(200, 200, 300, 100)
            layout = QVBoxLayout()
            task_label = QLabel(f'{task_text}\n\nTugas ini telah selesai!', new_window)
            layout.addWidget(task_label)
            new_window.setLayout(layout)
            new_window.exec_()
            self.remove_task()
        else:
            QMessageBox.warning(self, 'Peringatan', 'Pilih tugas yang akan ditandai sebagai selesai terlebih dahulu.')

    def save_task(self, task):
        with open('todolist.txt', 'a') as f:
            f.write(task + '\n')

    def save_tasks(self):
        tasks = [self.task_list.item(i).text() for i in range(self.task_list.count())]
        with open('todolist.txt', 'w') as f:
            f.write('\n'.join(tasks))

    def load_tasks(self):
        try:
            with open('todolist.txt', 'r') as f:
                tasks = f.read().split('\n')
                for task in tasks:
                    if task:
                        item = QListWidgetItem(task)
                        item.setData(Qt.UserRole, QVariant(QDateTime()))
                        self.task_list.addItem(item)
        except FileNotFoundError:
            pass

    def reset_task_list(self):
        result = QMessageBox.question(self, 'Reset Tugas', 'Apakah Anda yakin ingin mereset daftar tugas?', QMessageBox.Yes | QMessageBox.No)
        if result == QMessageBox.Yes:
            self.task_list.clear()
            self.save_tasks()
            self.complete_button.setEnabled(False)

    def check_selection(self):
        selected_item = self.task_list.currentItem()
        if selected_item is not None:
            self.complete_button.setEnabled(True)
        else:
            self.complete_button.setEnabled(False)

    def open_timer_window(self):
        selected_item = self.task_list.currentItem()
        if selected_item is not None:
            try:
                deadline = self.get_deadline(selected_item)
                timer_window = CountdownTimer(deadline)
                timer_window.exec_()

            except Exception as e:
                QMessageBox.critical(self, 'Kesalahan', f'Terdapat kesalahan saat membuka jendela timer: {str(e)}')

    def set_deadline(self, item, deadline):
        item.setData(Qt.UserRole, QVariant(deadline))

    def get_deadline(self, item):
        return item.data(Qt.UserRole)

    def check_deadline_alert(self, item):
        deadline = self.get_deadline(item)
        if isinstance(deadline, QDateTime) and deadline.isValid():
            current_datetime = QDateTime.currentDateTime()
            deadline_datetime = QDateTime(deadline.date(), QTime(0, 0))
            one_day = timedelta(days=1)
            alert_datetime = current_datetime.addSecs(int(one_day.total_seconds()))
            return deadline_datetime == alert_datetime
        return False

    def activate_deadline_alert(self):
        try:
            playsound('./alarm.mp3')
        except Exception as e:
            QMessageBox.warning(self, 'Peringatan', f'Tidak dapat memutar suara alarm: {str(e)}')

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('todolist.jpg'))
    ex = ToDoListApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

