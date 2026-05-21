import os
import json
import pyaudio
import time
from vosk import Model, KaldiRecognizer

# Chess vocabulary
pieces = ["pawn", "knight", "bishop", "rook", "queen", "king", "castle"]
files = ["a", "b", "c", "d", "e", "f", "g", "h"]
ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]
ranks_map = {
    "one": "1", "two": "2", "three": "3", "four": "4", 
    "five": "5", "six": "6", "seven": "7", "eight": "8"
}
actions = ["takes", "promotes"]
filler = ["from", "my", "the", "goes"]
chess_vocabulary = pieces + files + ranks + actions + filler + ["[unk]"]
grammar_json = json.dumps(chess_vocabulary)


def parse(text):
    text = text.split()

    piece_list = []
    locations = []
    action_list = []

    piece = "None"
    source = "None"
    dest = "None"
    target = "None"
    promote = False

    # Remove fillers
    for word in text:
        if (word in filler):
            text.remove(word)
    
    # Parse the command
    for i in range(len(text)):
        word = text[i]

        if (word == "two" and i > 0):
            prev_word = text[i-1]
            if (prev_word not in files):
                action_list.append("to")

        elif (word in pieces):
            piece_list.append(word)

        elif (word in actions):
            action_list.append(word)
        
        elif (word in files):
            if (i > len(text) - 2 or text[i+1] not in ranks):
                print("Command not in correct format!")
                return
            else:
                locations.append(word + ranks_map[text[i+1]])
        
        else:
            if (i == 0 or text[i-1] not in files):
                print("Command not in correct format!")
                return


    # Fill the empty variables
    if (len(piece_list) < 1):
        print("Command not in correct format!")
        return
    
    piece = piece_list[0]

    if ("promotes" in action_list):
        promote = True

    # Piece takes another
    if (len(locations) == 0):
        if (len(piece_list) != 2):
            print("Command not in correct format!")
            return
        else:
            target = piece_list[1]
    # Simple move
    elif (len(locations) == 1):
        dest = locations[0]
    # Source given move
    elif (len(locations) == 2):
        source = locations[0]
        dest = locations[1]
    else:
        print("Command not in correct format!")
        return
    
    print("Order: piece, source, destination, target, promotion")
    print(f"{piece} {source} {dest} {target} {promote}\n")



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

    recognizer.SetWords(True)
    WAIT_TIME = 0.4
    last_speech_time = time.time()
    running_text = ""

    print()

    while True:
        data = stream.read(4096, exception_on_overflow=False)

        if len(data) == 0:
            break
        
        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            if "result" in result:
                filtered_words = []
                
                for word_info in result["result"]:
                    word = word_info["word"]
                    confidence = word_info["conf"] # Value between 0.0 and 1.0
                    
                    # Filter out unknown words and weak guesses
                    if word == "[unk]" or confidence < 0.4: 
                        print(f"Dropped untrusted word: '{word}' (Confidence: {confidence:.2f})")
                    else:
                        filtered_words.append(word)
                
                # Rebuild your clean sentence
                text = " ".join(filtered_words)
                if text:
                    running_text += " " + text
                    last_speech_time = time.time()
        else:
            # Partial results mean the user is still speaking
            partial = json.loads(recognizer.PartialResult()).get("partial", "")
            if partial:
                last_speech_time = time.time()

        if running_text and (time.time() - last_speech_time > WAIT_TIME):
                print(f"Validated Chess Command: {text}")
                parse(text)
                running_text = ""

if __name__ == "__main__":
    main()