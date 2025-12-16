import sys
import speech_recognition as sr
import time
import subprocess
import pyautogui
import pyaudio
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTextEdit, QLabel, QPushButton, QMessageBox)
from PyQt6.QtCore import pyqtSignal, QObject, Qt, QTimer

# --- НАСТРОЙКИ ---
LANGUAGE = "ru-RU"
URL_TO_OPEN = "https://aistudio.google.com/"

# --- ИГНОР ОШИБОК ALSA/JACK ---
from ctypes import *
try:
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    asound = cdll.LoadLibrary('libasound.dylib')
    asound.snd_lib_error_set_handler(c_error_handler)
except:
    pass

class GoogleBackgroundListener(QObject):
    text_ready = pyqtSignal(str, str)
    status_update = pyqtSignal(str)

    def __init__(self, device_index, role_name):
        super().__init__()
        self.device_index = device_index
        self.role_name = role_name
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.2 
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = False 

    def start(self):
        try:
            self.mic_source = sr.Microphone(device_index=self.device_index)
            self.status_update.emit(f"✅ {self.role_name}: Слушаю...")
            self.stop_listening = self.recognizer.listen_in_background(
                self.mic_source, 
                self.callback_recognition,
                phrase_time_limit=None 
            )
        except Exception as e:
            self.status_update.emit(f"❌ Нет доступа к микрофону! ({self.role_name})")

    def callback_recognition(self, recognizer, audio):
        try:
            text = recognizer.recognize_google(audio, language=LANGUAGE)
            if len(text) > 1:
                self.text_ready.emit(self.role_name, text)
        except:
            pass

class SpyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.listeners = []
        self.last_role = None 
        self.initUI()
        
        # Попытка вызвать запросы прав при старте
        QTimer.singleShot(1000, self.trigger_permissions)
        QTimer.singleShot(2000, self.setup_workspace) 
        QTimer.singleShot(4000, self.start_listeners) 

    def initUI(self):
        self.setWindowTitle('SPY CHROME PRO')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: #121212; color: white;")

        layout = QVBoxLayout()

        self.status_label = QLabel("Загрузка...")
        self.status_label.setStyleSheet("color: #00ff00; font-size: 12px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; color: #e0e0e0; border: 1px solid #333;
                font-family: Arial; font-size: 14px; padding: 10px;
            }
        """)
        layout.addWidget(self.text_area)

        # Кнопки
        btn_layout = QHBoxLayout()

        # Кнопка помощи с правами
        self.perm_btn = QPushButton("🆘 ДАТЬ ПРАВА")
        self.perm_btn.setStyleSheet("background-color: #ff9800; color: black; font-weight: bold; padding: 10px;")
        self.perm_btn.clicked.connect(self.open_permissions_help)
        btn_layout.addWidget(self.perm_btn)

        self.send_btn = QPushButton("🚀 ОТПРАВИТЬ")
        self.send_btn.setStyleSheet("""
            QPushButton { background-color: #2e7d32; color: white; padding: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #4caf50; }
        """)
        self.send_btn.clicked.connect(self.send_all_to_browser)
        btn_layout.addWidget(self.send_btn)

        self.clear_btn = QPushButton("🗑")
        self.clear_btn.setFixedSize(50, 50)
        self.clear_btn.setStyleSheet("background-color: #d32f2f; border-radius: 5px;")
        self.clear_btn.clicked.connect(self.clear_log)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def trigger_permissions(self):
        """Пытаемся спровоцировать macOS на запрос прав"""
        self.status_label.setText("🔨 Проверка прав...")
        # 1. Провокация Автоматизации (AppleEvents)
        try:
            subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to get name'], timeout=1)
        except: pass
        
        # 2. Провокация Микрофона (через PyAudio короткий старт)
        try:
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
            stream.stop_stream()
            stream.close()
            p.terminate()
        except: pass

    def open_permissions_help(self):
        """Открывает настройки macOS для пользователя"""
        msg = QMessageBox()
        msg.setWindowTitle("Инструкция по правам")
        msg.setText("MacOS блокирует управление. Сделай следующее:")
        msg.setInformativeText("1. Сейчас откроются настройки.\n2. Включи тумблер для SpyChromePro.\n3. Перезапусти приложение.")
        msg.exec()

        # Открываем Универсальный доступ (Accessibility)
        subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])

    def setup_workspace(self):
        screen = QApplication.primaryScreen()
        geom = screen.availableGeometry()
        half_w = int(geom.width() / 2)
        self.setGeometry(geom.x() + half_w, geom.y(), half_w, geom.height())
        
        try:
            subprocess.Popen(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--new-window", URL_TO_OPEN])
            self.status_label.setText("⏳ Жду Chrome...")
        except:
             self.status_label.setText("❌ Chrome не найден!")

        QTimer.singleShot(2000, lambda: self.move_chrome_left(geom.x(), geom.y(), half_w, geom.height()))

    def move_chrome_left(self, x, y, w, h):
        script = f'''
        tell application "System Events"
            try
                tell process "Google Chrome"
                    set frontWindow to window 1
                    set position of frontWindow to {{{x}, {y}}}
                    set size of frontWindow to {{{w}, {h}}}
                    set frontmost to true
                end tell
            end try
        end tell
        '''
        try:
            subprocess.run(['osascript', '-e', script])
            self.status_label.setText("✅ Готов к работе")
        except:
            self.status_label.setText("⚠️ Нет прав на управление окнами!")

    def send_all_to_browser(self):
        full_text = self.text_area.toPlainText()
        if not full_text.strip(): return

        clipboard = QApplication.clipboard()
        clipboard.clear()
        clipboard.setText(full_text)
        
        # Активация Chrome
        subprocess.run(['osascript', '-e', 'tell application "Google Chrome" to activate'])
        time.sleep(0.5) 
        
        # Эмуляция нажатий
        try:
            pyautogui.press('esc') 
            time.sleep(0.1)
            pyautogui.hotkey('command', 'v')
            time.sleep(0.3)
            pyautogui.hotkey('command', 'enter')
            self.status_label.setText("✅ Отправлено!")
        except:
             self.status_label.setText("❌ ОШИБКА: Нет прав Accessibility!")
             self.open_permissions_help()

    def start_listeners(self):
        p = pyaudio.PyAudio()
        blackhole_idx = None
        for i in range(p.get_device_count()):
            try:
                info = p.get_device_info_by_index(i)
                if "BlackHole" in info['name']:
                    blackhole_idx = i; break
            except: pass
        
        mic_idx = p.get_default_input_device_info()['index'] if p.get_device_count() > 0 else 0

        if blackhole_idx is not None:
            l_int = GoogleBackgroundListener(blackhole_idx, "ИНТЕРВЬЮЕР")
            l_int.text_ready.connect(self.append_text)
            l_int.status_update.connect(self.update_status)
            self.listeners.append(l_int)
            l_int.start()
        else:
            self.status_label.setText("⚠️ BlackHole не найден!")

        l_mic = GoogleBackgroundListener(mic_idx, "Я")
        l_mic.text_ready.connect(self.append_text)
        l_mic.status_update.connect(self.update_status)
        self.listeners.append(l_mic)
        l_mic.start()

    def update_status(self, text):
        if "⚡️" not in self.status_label.text():
            self.status_label.setText(text)

    def append_text(self, role, text):
        text = text.strip()
        cursor = self.text_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        
        if self.last_role != role:
            self.text_area.insertPlainText("\n") 
            color = "#ff6666" if "ИНТЕРВЬЮЕР" in role else "#66ff66"
            html = f"<div style='margin-top: 10px;'><b><span style='color:{color}'>{role}:</span></b> {text.capitalize()}</div>"
            cursor.insertHtml(html)
        else:
            html = f" <span style='color: #ddd;'>{text}</span>"
            cursor.insertHtml(html)

        self.last_role = role
        self.text_area.moveCursor(cursor.MoveOperation.End)

    def clear_log(self):
        self.text_area.clear()
        self.last_role = None
        self.status_label.setText("🗑 Лог очищен")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SpyApp()
    ex.show()
    sys.exit(app.exec())