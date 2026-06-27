import os
import json
import pyaudio
import time
from vosk import Model, KaldiRecognizer

class Parse:
    piece_list = []
    source = None
    dest = None
    
    def clear(self):
        self.piece_list = []
        self.source = None
        self.dest = None

def setup():
    # Chess vocabulary
    global pieces, files, ranks, ranks_map, inv_ranks_map, actions, filler, chess_vocabulary, grammar_json, recognizer, stream, WAIT_TIME
    pieces = ["pawn", "knight", "bishop", "rook", "queen", "king"]
    files = ["a", "b", "c", "d", "e", "f", "g", "h"]
    ranks = ["one", "two", "three", "four", "five", "six", "seven", "eight"]
    ranks_map = {
        "one": "1", "two": "2", "three": "3", "four": "4", 
        "five": "5", "six": "6", "seven": "7", "eight": "8"
    }
    inv_ranks_map = {v: k for k, v in ranks_map.items()}
    actions = ["takes", "promotes"]
    filler = ["from", "the", "goes"]
    chess_vocabulary = pieces + files + ranks + actions + filler + ["[unk]"]
    grammar_json = json.dumps(chess_vocabulary)

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
    recognizer.SetWords(True)
    WAIT_TIME = 0.4


def parse(text):
    text = text.split()
    parse = Parse()
    parse.clear()

    locations = []
    action_list = []


    # Remove fillers and turn numbers to letters
    for i in range(len(text)):
        word = text[i]
        if (word in filler):
            text.remove(word)
        elif (word in inv_ranks_map):
            text[i] = inv_ranks_map[word]
    
    # Parse the command
    for i in range(len(text)):
        word = text[i]

        if (i < len(text) - 1 and word == "eight" and text[i+1] in ranks):
            word = "a"

        elif (word in pieces):
            parse.piece_list.append(word)

        elif (word in actions):
            action_list.append(word)
        
        if (word in files):
            if (i > len(text) - 2 or text[i+1] not in ranks):
                print("Command not in correct format!")
                return False
            else:
                locations.append(word + ranks_map[text[i+1]])

        elif (word[0] in files and word[1].isnumeric() and len(word) == 2):
            locations.append(word)

        elif (word[0] in files and word[1].isnumeric() and word[2] in files and word[3].isnumeric() and len(word) == 4):
            locations.append(word[0:2])
            locations.append(word[2:4])
        
        # Number but no letter before
        #else:
        #    if (i == 0 or text[i-1] not in files):
        #        print("Command not in correct format!")
        #        return False


    # No piece given, not enough squares given
    if (len(parse.piece_list) < 1 and len(locations) <= 1):
        print("No source or destination square!")
        return
    
    # Too much information
    if (len(parse.piece_list) > 2 or len(locations) > 2):
            print("Too many pieces or squares given!")
            return

    # Piece takes another
    if (len(locations) == 0):
        if (len(parse.piece_list) < 2):
            print("No source or destination piece!")
            return

    # Simple move
    elif (len(locations) == 1):
        parse.dest = locations[0]
    # Source given move
    elif (len(locations) == 2):
        parse.source = locations[0]
        parse.dest = locations[1]
    
    #print("Order: pieces, source, destination")
    #print(f"{parse.piece_list} {parse.source} {parse.dest}\n")

    return parse


def parseSound():
    stream.start_stream()

    print("Listening")

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
                running_text = ""
                parsed_text = parse(text)
                if (parsed_text):
                    return(parsed_text)
                