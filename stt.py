import os
import json
import pyaudio
from vosk import Model, KaldiRecognizer

# Chess vocabulary
pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
files = ["a", "b", "c", "d", "e", "f", "g", "h"]
ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]
ranks_map = {
    "one": "1", "two": "2", "three": "3", "four": "4", 
    "five": "5", "six": "6", "seven": "7", "eight": "8"
}
actions = ["to", "takes", "promotes"]
filler = ["from", "my"]
chess_vocabulary = pieces + files + ranks + actions + filler
grammar_json = json.dumps(chess_vocabulary)

def parse(text):
    text = text.split()

    for word in text:
        if (word in filler):
            text.remove(word)
    
    for i in range(len(text)):
        word = text[i]

        if (word == "two" and i < len(text) - 2):
            next_word = text[i+1]
            next_next_word = text[i+2]
            if (next_word in files and next_next_word in ranks):
                text[i] = "to"
        
        elif (word in ranks):
            text[i] = ranks_map[word]

    print(f"Parsed command: {text}")

def main():
    # Initialize Vosk model
    model_path = "vosk-model-small-en-us-0.15"
    if not os.path.exists(model_path):
        print("Please download the model and place it in the 'model' directory.")
        exit(1)

    model = Model(model_path)

    # Bind the grammar to the recognizer
    recognizer = KaldiRecognizer(model, 16000, grammar_json)

    # Set up Microphone Audio Stream
    mic = pyaudio.PyAudio()
    stream = mic.open(
        format=pyaudio.paInt16, 
        channels=1, 
        rate=16000, 
        input=True, 
        frames_per_buffer=8192
    )
    stream.start_stream()

    print("Listening")

    while True:
        data = stream.read(4096, exception_on_overflow=False)
        
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "")
            
            if text:
                print(f"Recognized command: {text}")
                parse(text)

if __name__ == "__main__":
    main()