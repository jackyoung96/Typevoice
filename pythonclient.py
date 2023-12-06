from client_module import VoiceCommunication
from threading import Thread
import time

source_name = input('source name:').strip()
dest_name = input('destination name:').strip()
typevoice = input('typevoice (y/n):').strip()
typevoice = True if typevoice.lower() == 'y' else False
with open('ip.txt', 'r') as f:
    ip = f.readline().strip()
if not ip:
    ip = '127.0.0.1'
ip = '127.0.0.1'
    
vc = VoiceCommunication(ip, 9001, source_name=source_name, destination_name=dest_name, typevoice=typevoice)
input_text_q, output_text_q = vc.getqueue()
vc_thread = Thread(target=vc.run)
vc_thread.start()

# STT
# if source_name == "jack":
#     for _ in range(3):
#         input_text_q.put("안녕?")
#         time.sleep(3)
   
# TTS   
# while True:  
#     try:
#         print("로그다 로그!!", output_text_q.get())
#     except KeyboardInterrupt:
#         break

vc_thread.join()
