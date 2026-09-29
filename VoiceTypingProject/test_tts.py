import pyttsx3

print('pyttsx3 module:', pyttsx3)

try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    print('voices found:', len(voices))
    for i, v in enumerate(voices):
        print(i, v.id, getattr(v, 'name', ''))

    if voices:
        print('Running a short TTS sample...')
        engine.say('This is a test from pyttsx3.')
        engine.runAndWait()
    else:
        print('No voices available.')
except Exception as e:
    print('TTS error:', e)

print('Test finished.')
