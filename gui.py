import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLineEdit
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
            self.input_line.textEdited.connect(self.send_message_by_space)
            self.input_line.returnPressed.connect(self.send_message)  # 엔터 키 이벤트 연결
            layout.addWidget(self.input_line)

            send_button = QPushButton('보내기')
            send_button.clicked.connect(self.send_message)
            layout.addWidget(send_button)

            self.setLayout(layout)
            self.setWindowTitle(f"{self.source_name}의 채팅방 (Type-Voice 사용)")
        else:
            self.setLayout(layout)
            self.setWindowTitle(f"{self.source_name}의 채팅방 (음성 통화)")
        
        if self.typevoice:
            stt_thread = Thread(target=self.get_stt_message, daemon=True)
            stt_thread.start()

    def get_stt_message(self):
        while True:
            sleep(0.01)
            text = self.output_text_q.get()
            self.text_area.append(f"{self.dest_name}: {text}")

    def send_message_by_space(self):
        # 입력 필드에서 텍스트를 가져와 출력 필드에 설정
        text = self.input_line.text()
        if text.endswith(' '):
            if text.strip():
                self.input_text_q.put(text.strip().split(' ')[-1])

    def send_message(self):
        text = self.input_line.text()
        
        if not text.endswith(' '):
            if text.strip():
                self.input_text_q.put(text.strip().split(' ')[-1])
        
        if text:
            self.text_area.append(f"{self.source_name}: {text}")
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
