import socket
import sounddevice as sd
from threading import Thread, Lock, Condition
from time import sleep
import pickle
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from socket import timeout

import io
from models.tts import base_tts
from models.stt import base_stt
from pydub import AudioSegment
from faster_whisper import WhisperModel

import queue

class SharedBuf:
    def __init__(self):
        self.buffer = np.array([], dtype='float32')

    def clearbuf(self):
        self.buffer = []

    def addbuf(self, arr):
        self.buffer = np.append(self.buffer, arr)

    def extbuf(self, arr):
        self.buffer = np.append(self.buffer, arr)

    def getlen(self):
        return len(self.buffer)

    def getbuf(self):
        return self.buffer

    def getx(self, x):
        data = self.buffer[0:x]
        self.buffer = self.buffer[x:]
        return data

class VoiceCommunication:
    MAX_BYTES_SEND = 512
    MAX_HEADER_LEN = 20
    SLEEPTIME = 0.0002
    BUFMAX = 512  # Assuming 16000 is your sample rate
    key = b'thisisthepasswordforAESencryptio'
    running = True
    item_available = Condition()
    audio_available = Condition()
    
    # AUdio settings
    samplerate = 16000
    chunk_length = 1000
    buffer_length = int(samplerate * chunk_length / 1000)
    
    input_text_q = queue.Queue()
    output_text_q = queue.Queue()

    def __init__(self, server_ip, server_port, source_name, destination_name, typevoice=False):
        self.server_ip = server_ip
        self.server_port = server_port
        self.source_name = source_name
        self.destination_name = destination_name
        self.typevoice = typevoice
        self.running = True
        self.sdstream = sd.Stream(samplerate=16000, channels=1, dtype='float32')
        self.sdstream.start()
        self.key = b'thisisthepasswordforAESencryptio'
        self.iv = get_random_bytes(16)
        self.cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
        self.socket = self.connect(source_name, destination_name)
        if typevoice:
            self.BUFMAX = self.samplerate * 2
            
        # STT
        self.stt_function = base_stt
        
        # TTS
        self.tts_function = base_tts
        
        
    # Other methods (encrypt, decrypt, split_send_bytes, etc.) go here
    # Make sure to replace global variables with instance variables (e.g., self.running)
    def get_iv(self):
        return get_random_bytes(16)


    def decrypt(self, enc_data):
        cphr = AES.new(self.key, AES.MODE_CBC, enc_data[:16])
        decoded = cphr.decrypt(enc_data)[16:]
        return decoded.rstrip()


    def encrypt(self, data_string):
        iv = self.get_iv()
        # cphr = AES.new(self.key, AES.MODE_CBC, iv)
        d = iv + data_string
        d = (d + (' ' * (len(d) % 16)).encode())
        return self.cipher.encrypt(d)


    def split_send_bytes(self, s, inp):
        data_len = (len(inp))
        if data_len == 0:
            print('ERROR: trying to send 0 bytes')  # should not happen in theory but threads are weird
            return

        # tells the client on the other end how many bytes it's expecting to receive
        header = str(data_len).encode('utf8')
        header_builder = b'0' * (self.MAX_HEADER_LEN - len(header)) + header
        s.send(header_builder)

        # send content in small batches. Maximum value of MAX_BYTES_SEND is 1024
        for i in range(data_len // self.MAX_BYTES_SEND):
            s.send(inp[i * self.MAX_BYTES_SEND:i * self.MAX_BYTES_SEND + self.MAX_BYTES_SEND])

        # send any remaining data
        if data_len % self.MAX_BYTES_SEND != 0:
            s.send(inp[-(data_len % self.MAX_BYTES_SEND):])


    def split_recv_bytes(self, s):
        dat = b''

        # receive header that specifies number of incoming bytes
        data_len_raw = s.recv(self.MAX_HEADER_LEN)
        try:
            data_len = (data_len_raw).decode('utf8')
            data_len = int(data_len)
        except UnicodeDecodeError as e:
            print(data_len_raw)
            raise e
        while data_len == 0:
            print(f"received 0 bytes. raw = {data_len_raw}")  # should never happen
            data_len = int((s.recv(self.MAX_BYTES_SEND)).decode('utf8'))

        # read bytes
        for i in range(data_len // self.MAX_BYTES_SEND):
            dat += s.recv(self.MAX_BYTES_SEND)
        if data_len % self.MAX_BYTES_SEND != 0:
            dat += s.recv(data_len % self.MAX_BYTES_SEND)

        return dat

    def connect(self, source_name, destination_name):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.server_ip, self.server_port))
        # Send and receive data as required
        
        print(f"hello {source_name}")
        print(f"message length = {len((source_name + (' ' * (512 - len(source_name)))).encode())}")
        s.send((source_name + (' ' * (512 - len(source_name)))).encode())

        s.send((destination_name + (' ' * (512 - len(destination_name)))).encode())
        sleep(2)
        
        val = s.recv(2)
        if val.decode() != 'go':
            raise TypeError
        # returns socket fd
        s.settimeout(5.0)
        return s

    # Record, transmit, receive, play methods go here
    def record(self, t):
        if self.running:
            return self.sdstream.read(t)[0]

    def transmit(self, buf, socket):
        pickled = buf.tobytes()
        encrypted_str = self.encrypt(pickled)
        # encrypted_str = base64.b64encode(pickled)

        try:
            self.split_send_bytes(socket, encrypted_str)
        except timeout:
            print("SOCKET TIMEOUT")
            self.running = False
        except BrokenPipeError:
            print("Recipient disconnected")
            self.running = False


    def record_transmit_thread(self, serversocket):
        print("***** STARTING RECORD TRANSMIT THREAD *****")
        tbuf = SharedBuf()

        def recorder_producer(buf):
            while self.running:
                sleep(self.SLEEPTIME)
                data = self.record(32)
                with self.item_available:
                    self.item_available.wait_for(lambda: buf.getlen() <= self.BUFMAX)
                    buf.extbuf(data)
                    self.item_available.notify()

            print("RECORDER ENDS HERE")
        
        def tts_producer(buf):
            
            while self.running:
                sleep(self.SLEEPTIME)

                input_text = self.input_text_q.get()
                audio_array = self.tts_function(input_text)
                
                with self.item_available:
                    self.item_available.wait_for(lambda: buf.getlen() <= self.BUFMAX)
                    buf.extbuf(audio_array)
                    self.item_available.notify()

            print("TTS ENDS HERE")

        def transmitter_consumer(buf, serversocket):
            while self.running:
                sleep(self.SLEEPTIME)
                with self.item_available:
                    self.item_available.wait_for(lambda: buf.getlen() >= 32)
                    # TODO: 여기에 TTS 모듈
                    self.transmit(buf.getx(32), serversocket)
                    self.item_available.notify()

            print("TRANSMITTER ENDS HERE")

        if self.typevoice:
            rec_thread = Thread(target=tts_producer, args=(tbuf,))
        else:
            rec_thread = Thread(target=recorder_producer, args=(tbuf,))
        tr_thread = Thread(target=transmitter_consumer, args=(tbuf, serversocket))

        rec_thread.start()
        tr_thread.start()

        rec_thread.join()
        tr_thread.join()
        return


    # use a sound library to play the buffer
    def play(self, buf):
        # print("playing_audio")
        if self.running:
            self.sdstream.write(buf)


    def receive(self, socket):
        while self.running:
            try:
                dat = self.split_recv_bytes(socket)
                dat = self.decrypt(dat)
                # dat = base64.b64decode(dat)
                buf = np.frombuffer(dat, dtype='float32')  # read decrypted numpy array
                yield buf
            except pickle.UnpicklingError as e:
                print(f"    @@@@@ UNPICKLE ERROR @@@@@   \n DATA RECEIVED {len(dat)} :: {dat}")  # INPUT______ of len = {sys.getsizeof(dat)} ::{decrypt(dat)} :: {str(e)}")
                continue
            except timeout:
                print("SOCKET TIMEOUT")
                yield None
            except ConnectionResetError:
                print("Recipient disconnected")
                yield None
            except:
                print("something unknown")
                yield None


    def receive_play_thread(self, serversocket):
        print("***** STARTING RECEIVE PLAY THREAD *****")
        rbuf = SharedBuf()

        def receiver_producer(buff, serversocket):
            rece_generator = self.receive(serversocket)
            while self.running:
                sleep(self.SLEEPTIME)
                try:
                    data = next(rece_generator)
                except StopIteration:
                    break
                if data is not None:
                    with self.audio_available:
                        self.audio_available.wait_for(lambda: buff.getlen() <= self.BUFMAX)
                        buff.extbuf(data)
                        self.audio_available.notify()

            print("RECEIVER ENDS HERE")

        def stt_consumer(buff):
            
            while self.running:
                sleep(self.SLEEPTIME)
                with self.audio_available:
                    self.audio_available.wait_for(lambda: buff.getlen() >= self.buffer_length)
                    chunk = buff.getx(buff.getlen())

                    text = self.stt_function(chunk)
                    if text:
                        self.output_text_q.put(text)
                                                            
                    self.audio_available.notify()

            print("STT ENDS HERE")
        
        def player_consumer(buff):
            
            while self.running:
                sleep(self.SLEEPTIME)
                with self.audio_available:
                    self.audio_available.wait_for(lambda: buff.getlen() >= 32)
                    self.play(buff.getx(buff.getlen()))
                    self.audio_available.notify()
                    
            print("PLAYER ENDS HERE")

        rece_thread = Thread(target=receiver_producer, args=(rbuf, serversocket))
        if self.typevoice:
            play_thread = Thread(target=stt_consumer, args=(rbuf,))
        else:
            play_thread = Thread(target=player_consumer, args=(rbuf,))
        
        rece_thread.start()
        play_thread.start()
        # input("press enter to exit")
        # running = False

        rece_thread.join()
        play_thread.join()
        return

    def run(self):
        print("Use typevoice:", self.typevoice)
        try:
            t_thread = Thread(target=self.record_transmit_thread, args=(self.socket,))
            p_thread = Thread(target=self.receive_play_thread, args=(self.socket,))
            t_thread.start()
            p_thread.start()
            input("Press Enter to exit")
            self.running = False
            self.sdstream.stop()
            t_thread.join()
            p_thread.join()
        except KeyboardInterrupt:
            print("keyboard interrupt")
        self.socket.close()
    
    def getqueue(self):
        return self.input_text_q, self.output_text_q
        
# Usage
if __name__ == '__main__':
    source_name = input('source name:').strip()
    dest_name = input('destination name:').strip()
    typevoice = input('typevoice (y/n):').strip()
    typevoice = True if typevoice.lower() == 'y' else False
    with open('ip.txt', 'r') as f:
        ip = f.readline().strip()
    if not ip:
        ip = '127.0.0.1'
    print("IP address:", ip )
    
    vc = VoiceCommunication(ip, 9001, 
                            source_name=source_name, 
                            destination_name=dest_name, 
                            typevoice=typevoice)
    input_text_q, output_text_q = vc.getqueue()
    vc.run()