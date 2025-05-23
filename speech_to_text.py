import speech_recognition as sr

def transcribe_audio():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        audio = r.listen(source)
    try:
        return r.recognize_google(audio)
    except sr.UnknownValueError:
        return "Sorry, could not understand your voice."
    except sr.RequestError:
        return "Could not connect to speech recognition service."
