from vosk import Model, KaldiRecognizer
import pyaudio
import json
import time
import requests

MODEL_PATH = "vosk-model-small-de-0.15"
SILENCE_DETECTION = 0.3

class VoiceRecognition:
    def __init__(self):
        self.model = Model(MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.mic = pyaudio.PyAudio()
        self.stream = self.mic.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=8192
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
                
        if time.time() - self.silence_time > SILENCE_DETECTION:
            self.silence_time = time.time()
            self.paragraph_buffer = ""

    def get_recognized(self):
        return self.paragraph_buffer

    def clear_recognized(self):
        self.paragraph_buffer = ""

class VoiceCommands:
    def execute(self, voice_recognition):
        recognized = voice_recognition.get_recognized()
        
        # Only execute commands if spoken to
        if "bernd" not in recognized:
            return

        # Check if the door is the target
        if "tür" in recognized:
            if "öffne" in recognized or "auf" in recognized:
                requests.get("http://192.168.1.10/opendoor")
                voice_recognition.clear_recognized()

            if "schließe" in recognized or "zu" in recognized:
                requests.get("http://192.168.1.10/closedoor")
                voice_recognition.clear_recognized()

def main():
    voice_recognition = VoiceRecognition()
    voice_commands = VoiceCommands()
    while True:
        voice_recognition.recognize()
        voice_commands.execute(voice_recognition)

if __name__ == "__main__":
    main()
