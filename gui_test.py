import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit, QLabel, QFormLayout
from PyQt5.QtCore import Qt, QEvent
from client_module import VoiceCommunication  # VoiceCommunication 모듈은 실제 모듈명으로 변경해야 합니다.
from threading import Thread
from time import sleep

class ChatWindow(QWidget):
    def __init__(self, source_name, dest_name, typevoice, input_text_q, output_text_q):
        super().__init__()
        
        self.source_name = source_name
        self.dest_name = dest_name
        self.typevoice = typevoice
        
        # text queue
        self.input_text_q = input_text_q
        self.output_text_q = output_text_q

        self.initUI()
        

    def initUI(self):
        layout = QVBoxLayout()

        if self.typevoice:
            self.text_area = QTextEdit()
            self.text_area.setReadOnly(True)
            layout.addWidget(self.text_area)

            self.input_line = QLineEdit()
            self.input_line.setPlaceholderText("메시지를 입력하세요...")
            self.input_line.installEventFilter(self)  # 이벤트 필터 설치
            self.input_line.returnPressed.connect(self.sendMessage)  # 엔터 키 이벤트 연결
            layout.addWidget(self.input_line)

            send_button = QPushButton('보내기')
            send_button.clicked.connect(self.sendMessage)
            layout.addWidget(send_button)

            self.setLayout(layout)
            self.setWindowTitle(f"{self.source_name}의 채팅방 (Type-Voice 사용)")
        else:
            self.setLayout(layout)
            self.setWindowTitle(f"{self.source_name}의 채팅방 (음성 통화)")
        
        if self.typevoice:
            tts_thread = Thread(target=self.get_tts_message, daemon=True)
            tts_thread.start()

    def eventFilter(self, source, event):
        if (source == self.input_line and 
            event.type() == QEvent.KeyPress and 
            event.key() == Qt.Key_Space):
            self.send_message_by_space()
            return True  # 이벤트 처리 완료
        return super().eventFilter(source, event)  # 다른 이벤트는 기본 처리

    def get_tts_message(self):
        while True:
            sleep(0.01)
            text = self.output_text_q.get()
            self.text_area.append(f"{self.dest_name}: {text}")

    def send_message_by_space(self):
        text = self.input_line.text()
        text = text.strip().split()[-1]
        if text:
            self.input_text_q.put(text)
        text = self.input_line.setText(text + ' ')

    def sendMessage(self):
        text = self.input_line.text()
        if text:
            self.text_area.append(f"{self.source_name}: {text}")
            
            # self.input_text_q.put(text)

            self.input_line.clear()

def main():
    app = QApplication(sys.argv)
    
    source_name = input('source name:').strip()
    dest_name = input('destination name:').strip()
    typevoice = input('typevoice (y/n):').strip()
    typevoice = True if typevoice.lower() == 'y' else False
    with open('ip.txt', 'r') as f:
        ip = f.readline().strip()
    if not ip:
        ip = '127.0.0.1'
    ip = '127.0.0.1'

    try:
        vc = VoiceCommunication(ip, 9001, source_name=source_name, destination_name=dest_name, typevoice=typevoice)
        input_text_q, output_text_q = vc.getqueue()
        vc_thread = Thread(target=vc.run)
        vc_thread.start()
        
        ex = ChatWindow(source_name, dest_name, typevoice, input_text_q, output_text_q)
        ex.show()

    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
