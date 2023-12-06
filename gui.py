import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLineEdit, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from client_module import VoiceCommunication  # VoiceCommunication 모듈은 실제 모듈명으로 변경해야 합니다.
from threading import Thread
from time import sleep

class MyApp(QWidget):
    def __init__(self, typevoice, input_text_q, output_text_q):
        super().__init__()

        # typevoice 여부
        self.typevoice = typevoice
        
        # 레이아웃 설정
        self.layout = QVBoxLayout()

        # 입력 필드 생성
        if self.typevoice:
            self.input_line = QLineEdit()  
            self.input_line.setPlaceholderText("여기에 텍스트 입력")
            self.input_line.textEdited.connect(self.on_space_pressed)
            self.input_line.returnPressed.connect(self.on_return_pressed)

            # 출력 필드 생성
            self.output_line = QLineEdit()
            self.output_line.setReadOnly(True)

            # 레이아웃에 위젯 추가
            self.layout.addWidget(self.input_line)
            self.layout.addWidget(self.output_line)

        # 위젯 설정
        self.setLayout(self.layout)
        self.setWindowTitle('Input to Output')
        
        # text queue
        self.input_text_q = input_text_q
        self.output_text_q = output_text_q
        
        if typevoice:
            stt_thread = Thread(target=self.get_stt_message, daemon=True)
            stt_thread.start()
        
    def get_stt_message(self):
        while True:
            sleep(0.01)
            text = self.output_text_q.get()
            self.output_line.setText(self.output_line.text().strip() + ' ' + text.strip())

    def on_space_pressed(self):
        # 입력 필드에서 텍스트를 가져와 출력 필드에 설정
        input_text = self.input_line.text()
        if input_text.endswith(' '):
            if input_text.strip():
                self.input_text_q.put(input_text.strip().split(' ')[-1])
        
    def on_return_pressed(self):
        # 입력 필드에서 텍스트를 가져와 출력 필드에 설정
        print("return pressed", flush=True)
        input_text = self.input_line.text()
        self.input_text_q.put(input_text.strip().split(' ')[-1])
        self.input_line.setText('')

if __name__ == '__main__':
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
        
        ex = MyApp(typevoice, input_text_q, output_text_q)
        ex.show()
    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        sys.exit(app.exec_())
