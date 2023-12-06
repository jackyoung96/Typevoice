import sys
from PyQt5.QtWidgets import QApplication, QWidget, QListWidget, QListWidgetItem, QVBoxLayout, QPushButton, QTextEdit, QLineEdit
from PyQt5.QtGui import QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QSize
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
        # 전체 배경과 텍스트 색상 설정
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(18,18,18)) # 배경색
        palette.setColor(QPalette.WindowText, Qt.white) # 텍스트 색상
        self.setPalette(palette)

        layout = QVBoxLayout()

        if self.typevoice:
            self.messageList = QListWidget()
            self.messageList.setStyleSheet("""
                QListWidget {
                    background-color: #121212;
                    color: white;
                    font-size: 16px;
                    border: none;
                }
            """)
            layout.addWidget(self.messageList)

            self.input_line = QLineEdit()
            self.input_line.setAlignment(Qt.AlignRight)  # 입력 필드의 텍스트를 우측 정렬로 설정
            self.input_line.setStyleSheet("""
                QLineEdit {
                    background-color: #121212;
                    color: white;
                    border: 2px solid #474747;
                    border-radius: 20px;
                    padding: 5px 15px;
                    font-size: 16px;
                }
            """)
            self.input_line.setPlaceholderText("메시지를 입력하세요...")
            self.input_line.textEdited.connect(self.send_message_by_space)
            self.input_line.returnPressed.connect(self.send_message)  # 엔터 키 이벤트 연결
            layout.addWidget(self.input_line)

            # 통화 종료 버튼 설정
            hangupButton = QPushButton()
            hangupButton.setIcon(QIcon('hangup.png'))  # 이미지 파일 경로를 지정해야 합니다
            hangupButton.setIconSize(QSize(80, 40))  # 이미지 크기 설정
            hangupButton.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;
                    color: white;
                    font-weight: bold;
                    border-radius: 20px; /* 모서리 둥글게 처리 */
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #FF5252;
                }
                QPushButton:pressed {
                    background-color: #C62828;
                }
            """)
            hangupButton.setFixedSize(80, 40)  # 버튼 크기 설정
            
            # 버튼을 수평으로 가운데 정렬
            buttonContainer = QWidget(self)
            buttonLayout = QVBoxLayout(buttonContainer)
            buttonLayout.addWidget(hangupButton)
            buttonLayout.setAlignment(Qt.AlignCenter)
            buttonContainer.setLayout(buttonLayout)
            layout.addWidget(buttonContainer, alignment=Qt.AlignCenter)
            
            hangupButton.clicked.connect(self.hangupCall)

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

            # 메시지 리스트에 아이템 추가
            item = QListWidgetItem(text)
            item.setForeground(QColor('white'))  # 글자색 설정
            item.setTextAlignment(Qt.AlignLeft)
            self.messageList.addItem(item)

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
            # 메시지 리스트에 아이템 추가
            item = QListWidgetItem(text)
            item.setForeground(QColor('white'))  # 글자색 설정
            item.setTextAlignment(Qt.AlignRight)
            self.messageList.addItem(item)
            self.input_line.clear()
    
    def hangupCall(self):
        # 통화 종료 로직 (여기서는 단순히 앱을 종료합니다)
        self.close()

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
        
        chat = ChatWindow(source_name, dest_name, typevoice, input_text_q, output_text_q)
        chat.resize(800, 600)  # 창 크기 설정
        chat.show()

    except KeyboardInterrupt:
        print("keyboard interrupt")
    finally:
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
