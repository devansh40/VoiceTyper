import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import speech_recognition as sr
import threading
import tempfile
import os

# Text-to-Speech (offline)                                                                                          
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from gtts import gTTS
    from playsound import playsound
except Exception:
    gTTS = None
    playsound = None

# Translation
try:
    from googletrans import Translator
except Exception:
    Translator = None

# Window
root = tk.Tk()
root.title("Voice Assit")
root.geometry("1000x700")
# Color palette
BG = "#1e1e2f"
PANEL = "#2d2d44"
ACCENT = "#00c853"
ACCENT2 = "#6a1b9a"
TEXT_FG = "white"

root.config(bg=BG)

# Header
header_frame = tk.Frame(root, bg=BG)
header_frame.pack(fill="x", padx=10, pady=(12,4))

app_icon = tk.Label(header_frame, text="🎤", font=("Segoe UI", 28), bg=BG, fg=ACCENT)
app_icon.pack(side="left", padx=(12,8))

title = tk.Label(header_frame, text="Voice Assit", font=("Segoe UI", 22, "bold"), bg=BG, fg=TEXT_FG)
title.pack(side="left")

subtitle = tk.Label(header_frame, text="Fast. Accurate. Beautiful.", font=("Segoe UI", 10), bg=BG, fg="#9aa0b4")
subtitle.pack(side="left", padx=(10,0))

# Text Area (editor with scrollbar)
editor_frame = tk.Frame(root, bg=BG)

text_area = tk.Text(
    editor_frame,
    font=("Segoe UI", 14),
    bg=PANEL,
    fg=TEXT_FG,
    insertbackground=TEXT_FG,
    wrap="word",
    bd=0,
    relief="flat",
    padx=12,
    pady=12,
    height=10
)

# Status
status_label = tk.Label(
    root,
    text="Click Start to Speak",
    font=("Segoe UI", 11),
    bg=BG,
    fg=ACCENT
)

recognizer = sr.Recognizer()
listening = False

# TTS engine
tts_engine = None
if pyttsx3 is not None:
    try:
        engine = pyttsx3.init()
        if engine.getProperty("voices"):
            tts_engine = engine
        else:
            tts_engine = None
    except Exception:
        tts_engine = None

translator = None
if Translator is not None:
    try:
        translator = Translator()
    except Exception:
        translator = None

LANGUAGES = {
    "English (US)": "en-US",
    "English (India)": "en-IN",
    "हिन्दी (Hindi)": "hi-IN",
    "मराठी (Marathi)": "mr-IN",
}

TRANSLATE_LANGUAGES = {
    "English": "en",
    "हिन्दी (Hindi)": "hi",
    "मराठी (Marathi)": "mr",
    "Español (Spanish)": "es",
    "Français (French)": "fr",
    "Deutsch (German)": "de",
    "Português (Portuguese)": "pt",
    "中文 (Chinese)": "zh-cn",
    "日本語 (Japanese)": "ja",
    "한국어 (Korean)": "ko",
}

translation_available = translator is not None

GTT_LANG_MAP = {
    "en-US": "en",
    "en-IN": "en",
    "hi-IN": "hi",
    "mr-IN": "mr",
}

language_var = tk.StringVar(value="English (US)")

def set_tts_voice_by_language(lang_code):
    if tts_engine is None:
        return False
    try:
        voices = tts_engine.getProperty("voices")
    except Exception:
        return False

    search = lang_code.lower()
    best_voice = None
    for voice in voices:
        try:
            voice_langs = []
            if hasattr(voice, "languages"):
                voice_langs = [str(l).lower() for l in voice.languages if l]
            voice_text = " ".join([voice.id, voice.name] + voice_langs).lower()
        except Exception:
            voice_text = f"{voice.id} {voice.name}".lower()

        if search in voice_text or search.split("-")[0] in voice_text:
            best_voice = voice.id
            break

    if best_voice is None and lang_code == "mr-IN":
        for voice in voices:
            if "marathi" in voice.name.lower() or "marathi" in voice.id.lower():
                best_voice = voice.id
                break

    if best_voice is not None:
        try:
            tts_engine.setProperty("voice", best_voice)
            return True
        except Exception:
            return False

    return False


def get_tts_mode(language_code):
    # Non-English speech prefers gTTS because pyttsx3 often lacks Hindi/Marathi voices.
    if language_code not in ("en-US", "en-IN"):
        if gTTS is not None and playsound is not None:
            return "gTTS"
        return "needs_gtts"

    if tts_engine is not None and set_tts_voice_by_language(language_code):
        return "pyttsx3"

    if gTTS is not None and playsound is not None and language_code in GTT_LANG_MAP:
        return "gTTS"

    return None


def get_gtts_language(language_code):
    return GTT_LANG_MAP.get(language_code)


def is_translation_available():
    return translator is not None


def get_translate_language(language_name):
    return TRANSLATE_LANGUAGES.get(language_name, "en")


def get_gtts_language_for_translate(language_name):
    return TRANSLATE_LANGUAGES.get(language_name)


def get_tts_mode_for_translate(language_name):
    lang_code = get_translate_language(language_name)
    if lang_code == "en":
        if tts_engine is not None and set_tts_voice_by_language("en-US"):
            return "pyttsx3"
        if gTTS is not None and playsound is not None:
            return "gTTS"
        return None
    if gTTS is not None and playsound is not None and lang_code:
        return "gTTS"
    return None


def translate_text(text, target_language_name):
    if not text:
        return ""
    if not is_translation_available():
        raise RuntimeError("Translation requires googletrans. Install with: python -m pip install googletrans==4.0.0rc1")
    try:
        dest_code = get_translate_language(target_language_name)
        result = translator.translate(text, dest=dest_code)
        return getattr(result, "text", str(result))
    except Exception as e:
        raise RuntimeError(str(e))


def translate_current_text():
    text = text_area.get(1.0, tk.END).strip()
    if not text:
        status_label.config(text="✏️ Nothing to translate")
        return
    try:
        translated = translate_text(text, target_language_var.get())
        translation_area.config(state="normal")
        translation_area.delete(1.0, tk.END)
        translation_area.insert(tk.END, translated)
        translation_area.config(state="disabled")
        status_label.config(text=f"🌐 Translated to {target_language_var.get()}")
    except RuntimeError as e:
        messagebox.showerror("Translation Error", str(e))
        status_label.config(text="❌ Translation failed")


def clear_translation():
    translation_area.config(state="normal")
    translation_area.delete(1.0, tk.END)
    translation_area.config(state="disabled")


def speak_translated_text():
    translated_text = translation_area.get(1.0, tk.END).strip()
    if not translated_text:
        status_label.config(text="🔇 No translated text available")
        return

    target_language_name = target_language_var.get()
    tts_mode = get_tts_mode_for_translate(target_language_name)
    if tts_mode is None:
        messagebox.showinfo(
            "TTS Not Installed",
            "Install pyttsx3 or gTTS+playsound: python -m pip install pyttsx3 gtts playsound"
        )
        return

    def _speak_pyttsx3():
        try:
            tts_engine.say(translated_text)
            tts_engine.runAndWait()
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("TTS Error", str(e)))

    def _speak_gtts():
        temp_file = None
        try:
            voice_lang = get_gtts_language_for_translate(target_language_name)
            if voice_lang is None:
                raise ValueError(f"Unsupported gTTS language: {target_language_name}")
            tts = gTTS(text=translated_text, lang=voice_lang)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_file = tmp.name
            tts.save(temp_file)
            playsound(temp_file)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("TTS Error", str(e)))
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    thread = threading.Thread(target=_speak_pyttsx3 if tts_mode == "pyttsx3" else _speak_gtts, daemon=True)
    thread.start()


def append_text_and_translate(text):
    text_area.insert(tk.END, text + " ")
    if auto_translate_var.get() and translation_available:
        translate_current_text()


def update_tts_language(*args):
    mode = get_tts_mode(LANGUAGES.get(language_var.get(), "en-US"))
    if mode == "pyttsx3":
        tts_status.config(text="TTS: available", fg="#b2ff59")
    elif mode == "gTTS":
        tts_status.config(text="TTS: available (gTTS)", fg="#b2ff59")
    elif mode == "needs_gtts":
        tts_status.config(text="TTS: requires gTTS+playsound", fg="#ffc107")
    else:
        tts_status.config(text="TTS: not installed", fg="#ff6666")


# Auto-speak after recognition
auto_speak_var = tk.BooleanVar(value=False)

# Auto-translate after recognition
auto_translate_var = tk.BooleanVar(value=False)

target_language_var = tk.StringVar(value="English")

# Microphone list and selection
try:
    mic_names = sr.Microphone.list_microphone_names()
except Exception:
    mic_names = []

mic_var = tk.StringVar(value=mic_names[0] if mic_names else "Default")


# Voice Function
def listen_voice():
    global listening
    try:
        # choose microphone by name if available
        mic_index = None
        try:
            if mic_names and mic_var.get() in mic_names:
                mic_index = mic_names.index(mic_var.get())
        except Exception:
            mic_index = None

        if mic_index is not None:
            source = sr.Microphone(device_index=mic_index)
        else:
            source = sr.Microphone()

        with source as source:
            recognizer.adjust_for_ambient_noise(source)

            while listening:
                try:
                    # update status on main thread
                    root.after(0, lambda: status_label.config(text=f"🎙 Listening ({language_var.get()})..."))

                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)

                    text = recognizer.recognize_google(audio, language=LANGUAGES.get(language_var.get(), "en-US"))

                    # insert recognized text on main thread
                    root.after(0, lambda t=text: append_text_and_translate(t))
                    # auto-speak if enabled
                    if auto_speak_var.get():
                        root.after(0, lambda t=text: speak_text(t))
                    root.after(0, lambda: status_label.config(text="✅ Voice Recognized"))

                except sr.WaitTimeoutError:
                    root.after(0, lambda: status_label.config(text="⌛ Listening timed out"))
                except sr.UnknownValueError:
                    root.after(0, lambda: status_label.config(text="❓ Could not understand audio"))
                except sr.RequestError as e:
                    root.after(0, lambda: messagebox.showerror("Speech API Error", str(e)))
                    root.after(0, lambda: status_label.config(text="❌ API Error"))
                except Exception:
                    root.after(0, lambda: status_label.config(text="❌ Error"))
                finally:
                    # small idle so loop can exit promptly when stopped
                    if not listening:
                        break
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Microphone Error", str(e)))

# Start Button
def start_listening():
    global listening
    if not listening:
        listening = True
        start_btn.config(state="disabled")
        stop_btn.config(state="normal")
        thread = threading.Thread(target=listen_voice, daemon=True)
        thread.start()

# Stop Button
def stop_listening():
    global listening
    listening = False
    start_btn.config(state="normal")
    stop_btn.config(state="disabled")
    root.after(0, lambda: status_label.config(text="🛑 Stopped"))

# Hold-to-talk bindings
hold_var = tk.BooleanVar(value=False)
def update_hold_bindings():
    if hold_var.get():
        start_btn.config(command=lambda: None)
        start_btn.bind("<ButtonPress-1>", lambda e: start_listening())
        start_btn.bind("<ButtonRelease-1>", lambda e: stop_listening())
        start_btn.config(text="🎙 Hold to Speak")
    else:
        start_btn.config(command=start_listening)
        start_btn.unbind("<ButtonPress-1>")
        start_btn.unbind("<ButtonRelease-1>")
        start_btn.config(text="▶ Start")

# Clear Text
def clear_text():
    text_area.delete(1.0, tk.END)
    clear_translation()

# Save File
def save_file():
    file = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")]
    )

    if file:
        with open(file, "w", encoding="utf-8") as f:
            f.write(text_area.get(1.0, tk.END))

        messagebox.showinfo("Saved", "File Saved!")

# Button Frame
button_frame = tk.Frame(root, bg=BG)
button_frame.pack(fill="x", padx=20, pady=(6,0))

# Buttons
start_btn = tk.Button(
    button_frame,
    text="▶ Start",
    font=("Segoe UI", 12, "bold"),
    bg=ACCENT,
    fg="white",
    padx=16,
    pady=8,
    bd=0,
    relief="raised",
    command=start_listening
)

start_btn.grid(row=0, column=0, padx=10)

stop_btn = tk.Button(
    button_frame,
    text="⏹ Stop",
    font=("Segoe UI", 12, "bold"),
    bg="#d50000",
    fg="white",
    padx=16,
    pady=8,
    bd=0,
    relief="raised",
    command=stop_listening
)

stop_btn.grid(row=0, column=1, padx=10)
stop_btn.config(state="disabled")

clear_btn = tk.Button(
    button_frame,
    text="🗑 Clear",
    font=("Segoe UI", 12, "bold"),
    bg="#2962ff",
    fg="white",
    padx=12,
    pady=8,
    bd=0,
    relief="raised",
    command=clear_text
)

clear_btn.grid(row=0, column=2, padx=10)

save_btn = tk.Button(
    button_frame,
    text="💾 Save",
    font=("Segoe UI", 12, "bold"),
    bg="#ff6d00",
    fg="white",
    padx=12,
    pady=8,
    bd=0,
    relief="raised",
    command=save_file
)

save_btn.grid(row=0, column=3, padx=10)

# Speak Button
def speak_text(text=None):
    # get text if not provided
    if text is None:
        text = text_area.get(1.0, tk.END).strip()
    if not text:
        return

    language_code = LANGUAGES.get(language_var.get(), "en-US")
    tts_mode = get_tts_mode(language_code)
    if tts_mode == "needs_gtts":
        root.after(0, lambda: messagebox.showinfo(
            "TTS Dependency Required",
            "Hindi/Marathi speech requires gTTS+playsound. Install with:\npython -m pip install gtts playsound"
        ))
        return

    if tts_mode is None:
        root.after(0, lambda: messagebox.showinfo(
            "TTS Not Installed",
            "Install pyttsx3 or gTTS+playsound: python -m pip install pyttsx3 gtts playsound"
        ))
        return

    def _speak_pyttsx3():
        try:
            tts_engine.say(text)
            tts_engine.runAndWait()
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("TTS Error", str(e)))

    def _speak_gtts():
        temp_file = None
        try:
            voice_lang = get_gtts_language(language_code)
            if voice_lang is None:
                raise ValueError(f"Unsupported gTTS language: {language_code}")
            tts = gTTS(text=text, lang=voice_lang)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                temp_file = tmp.name
            tts.save(temp_file)
            playsound(temp_file)
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("TTS Error", str(e)))
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

    thread = threading.Thread(target=_speak_pyttsx3 if tts_mode == "pyttsx3" else _speak_gtts, daemon=True)
    thread.start()

speak_btn = tk.Button(
    button_frame,
    text="🔊 Speak",
    font=("Segoe UI", 12, "bold"),
    bg=ACCENT2,
    fg="white",
    padx=12,
    pady=8,
    bd=0,
    relief="raised",
    command=lambda: speak_text()
)

speak_btn.grid(row=0, column=4, padx=10)

# Options frame (visible controls)
options_frame = tk.Frame(root, bg=BG)
options_frame.pack(fill="x", padx=20, pady=6)

# Hold-to-talk checkbox
hold_check = tk.Checkbutton(
    options_frame,
    text="Hold to Talk",
    variable=hold_var,
    onvalue=True,
    offvalue=False,
    bg="#1e1e2f",
    fg="white",
    selectcolor="#1e1e2f",
    command=update_hold_bindings,
    font=("Arial", 11, "bold")
)
hold_check.pack(side="left", padx=(0, 20))

# Microphone selector
if mic_names:
    mic_label = tk.Label(options_frame, text="Microphone:", bg="#1e1e2f", fg="white", font=("Arial", 11))
    mic_label.pack(side="left")

    mic_menu = tk.OptionMenu(options_frame, mic_var, *mic_names)
    mic_menu.config(bg=PANEL, fg=TEXT_FG, font=("Segoe UI", 10))
    mic_menu.pack(side="left", padx=(6, 20))
else:
    mic_label = tk.Label(options_frame, text="Microphone: (no devices found)", bg=BG, fg="#ff6666", font=("Segoe UI", 11))
    mic_label.pack(side="left", padx=(0, 20))

# Language selector
language_label = tk.Label(options_frame, text="Language:", bg="#1e1e2f", fg="white", font=("Arial", 11))
language_label.pack(side="left")

language_menu = tk.OptionMenu(options_frame, language_var, *LANGUAGES.keys(), command=update_tts_language)
language_menu.config(bg=PANEL, fg=TEXT_FG, font=("Segoe UI", 10))
language_menu.pack(side="left", padx=(6, 20))

# Small help label
help_label = tk.Label(
    options_frame,
    text="Use Start/Stop or enable Hold to Talk, choose a language, and press Start.",
    bg=BG,
    fg="#bfe7d4",
    font=("Segoe UI", 10),
    wraplength=420,
    justify="left"
)
help_label.pack(side="left", padx=(0, 20), fill="x", expand=True)

# Auto-speak checkbox in options
auto_check = tk.Checkbutton(
    options_frame,
    text="Auto-Speak",
    variable=auto_speak_var,
    onvalue=True,
    offvalue=False,
    bg="#1e1e2f",
    fg="white",
    selectcolor="#1e1e2f",
    font=("Arial", 11)
)
auto_check.pack(side="right", padx=(0, 20))

# TTS status
tts_status = tk.Label(options_frame, text="TTS: not installed", bg="#1e1e2f", fg="#ff6666", font=("Arial", 10, "italic"))
tts_status.pack(side="right", padx=(0,10))

# Translation controls
translation_controls_frame = tk.Frame(root, bg=BG)
translation_controls_frame.pack(fill="x", padx=20, pady=(0,4))

target_label = tk.Label(translation_controls_frame, text="Translate to:", bg=BG, fg="white", font=("Arial", 11))
target_label.pack(side="left")

target_menu = tk.OptionMenu(translation_controls_frame, target_language_var, *TRANSLATE_LANGUAGES.keys())
target_menu.config(bg=PANEL, fg=TEXT_FG, font=("Segoe UI", 10))
target_menu.pack(side="left", padx=(6, 20))

translate_btn = tk.Button(
    translation_controls_frame,
    text="🌍 Translate",
    font=("Segoe UI", 11, "bold"),
    bg=ACCENT,
    fg="white",
    padx=12,
    pady=6,
    bd=0,
    relief="raised",
    command=translate_current_text
)
translate_btn.pack(side="left", padx=10)

clear_translation_btn = tk.Button(
    translation_controls_frame,
    text="🧹 Clear Translation",
    font=("Segoe UI", 11, "bold"),
    bg="#2962ff",
    fg="white",
    padx=12,
    pady=6,
    bd=0,
    relief="raised",
    command=clear_translation
)
clear_translation_btn.pack(side="left", padx=10)

speak_translation_btn = tk.Button(
    translation_controls_frame,
    text="🔊 Speak Translation",
    font=("Segoe UI", 11, "bold"),
    bg=ACCENT2,
    fg="white",
    padx=12,
    pady=6,
    bd=0,
    relief="raised",
    command=speak_translated_text
)
speak_translation_btn.pack(side="left", padx=10)

auto_translate_check = tk.Checkbutton(
    translation_controls_frame,
    text="Auto-Translate",
    variable=auto_translate_var,
    onvalue=True,
    offvalue=False,
    bg="#1e1e2f",
    fg="white",
    selectcolor="#1e1e2f",
    font=("Arial", 11)
)
auto_translate_check.pack(side="right", padx=(0,20))

# Editor frame holds the keyboard text editor and translation panel below
editor_frame.pack(fill="both", expand=True, side="top", padx=12, pady=(6,0))

# Add label for keyboard text area
keyboard_label = tk.Label(
    editor_frame,
    text="Keyboard Text",
    font=("Segoe UI", 11, "bold"),
    bg=BG,
    fg=TEXT_FG
)
keyboard_label.pack(anchor="w", padx=(0,4), pady=(0,4))

# Add scrollbar inside editor_frame
scrollbar = tk.Scrollbar(editor_frame, orient='vertical', command=text_area.yview)
text_area.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side='right', fill='y')
text_area.pack(side='left', fill='both', expand=True)

# Translation output panel below editor
translation_frame = tk.Frame(root, bg=BG)
translation_frame.pack(fill="x", expand=False, side="bottom", padx=12, pady=(12,0))
translation_frame.pack_propagate(False)
translation_frame.configure(height=180)

translation_label = tk.Label(
    translation_frame,
    text="Translation Output",
    font=("Segoe UI", 11, "bold"),
    bg=BG,
    fg=TEXT_FG
)
translation_label.pack(anchor="w", padx=(0,4), pady=(0,4))

translation_area = tk.Text(
    translation_frame,
    font=("Segoe UI", 14),
    bg=PANEL,
    fg=TEXT_FG,
    insertbackground=TEXT_FG,
    wrap="word",
    bd=0,
    relief="flat",
    padx=12,
    pady=12,
    height=6
)
translation_area.config(state="disabled")
translation_scrollbar = tk.Scrollbar(translation_frame, orient='vertical', command=translation_area.yview)
translation_area.config(yscrollcommand=translation_scrollbar.set)
translation_scrollbar.pack(side='right', fill='y')
translation_area.pack(side='left', fill='both', expand=True)

# Status bar at bottom
status_bar = tk.Label(root, text="Ready", anchor='w', bg=BG, fg="#9aa0b4", font=("Segoe UI", 10))
status_bar.pack(side='bottom', fill='x')

# Run
root.mainloop()