import stt

def main():
    stt.setup()
    while True:
        text = input()
        if (text == "a"):
            stt.parseSound()
        else:
            break

if __name__ == "__main__":
    main()