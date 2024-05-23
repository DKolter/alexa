from vosk import Model, KaldiRecognizer
import pyaudio
import json
import time
import requests
import os

MODEL_PATH = "/home/dkolter/Desktop/alexa/vosk-model-small-de-0.15"
SILENCE_DETECTION = 0.3
WORDS = '["alexa", "tür", "auf", "zu", "öffne", "öffnen", "schließe",\
         "schließen", "licht", "an", "aus", "hell", "dunkel",\
         "grün", "rot", "blau", "gelb", "lila", "pink", "weiß",\
         "orange"]'

class VoiceRecognition:
    def __init__(self):
        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000, WORDS)
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=8192,
        )
        self.stream.start_stream()
        self.silence_time = time.time()
        self.paragraph_buffer = ""

    def recognize(self):
        data = self.stream.read(8192)
        if self.recognizer.AcceptWaveform(data):
            result = json.loads(self.recognizer.Result())
            result = result["text"].strip()
            if result != "":
                self.silence_time = time.time()
                self.paragraph_buffer += result + " "
                print(self.paragraph_buffer)
                
        if time.time() - self.silence_time > SILENCE_DETECTION:
            self.silence_time = time.time()
            self.paragraph_buffer = ""

    def get_recognized(self):
        return self.paragraph_buffer

    def clear_recognized(self):
        self.paragraph_buffer = ""

class VoiceCommands:
    def __init__(self):
        self.light_colors = {
            "grün": "GREEN",
            "rot": "RED",
            "orange": "ORANGE",
            "weiß": "WHITE",
            "pink": "PINK",
            "gelb": "YELLOW",
            "blau": "BLUE",
            "lila": "PURPLE",
        }

    def execute_light_command(self, command):
        try:
            requests.get(f"http://192.168.1.114/light/{command}")
        except Exception:
            pass
        
        if command == "BRIGHTER":
            for _ in range(7):
                os.system("irsend SEND_ONCE RGBLED BRIGHTER")
        elif command == "DARKER":
            for _ in range(7):
                os.system("irsend SEND_ONCE RGBLED DARKER")
        else:
            os.system(f"irsend SEND_ONCE RGBLED {command}")

    def execute(self, voice_recognition):
        recognized = voice_recognition.get_recognized()
        
        # Only execute commands if spoken to
        if "alexa" not in recognized:
            return

        # Check if the door is the target
        if "tür" in recognized:
            if "öffne" in recognized or "auf" in recognized:
                try:
                    requests.get("http://192.168.1.108/opendoor")
                except Exception:
                    pass
                voice_recognition.clear_recognized()

            if "schließe" in recognized or "zu" in recognized:
                try:
                    requests.get("http://192.168.1.108/closedoor")
                except Exception:
                    pass
                voice_recognition.clear_recognized()
        
        # Check if the light is the target
        elif "licht" in recognized:
            if "hell" in recognized:
                self.execute_light_command("BRIGHTER")
                return
            elif "dunkel" in recognized:
                self.execute_light_command("DARKER")
                return

            for color in self.light_colors:
                if color in recognized:
                    self.execute_light_command(self.light_colors[color])
                    voice_recognition.clear_recognized()
                    return

            self.execute_light_command("TOGGLE")
            voice_recognition.clear_recognized()

def main():
    voice_recognition = VoiceRecognition()
    voice_commands = VoiceCommands()
    while True:
        voice_recognition.recognize()
        voice_commands.execute(voice_recognition)

if __name__ == "__main__":
    main()
