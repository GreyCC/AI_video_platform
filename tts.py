import time
import queue
import logging
import threading
import uuid
from enum import Enum
import pyttsx3
# import win32com.client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# TTS Engine Types
class TTS_ENGINE(Enum):
    WINAPI = "winapi"
    SAPI5 = "sapi5"
    ESPEAK = "espeak"
    PYTTS3 = "pyttsx3"


class TTSManager:
    """Advanced TTS Manager with specific support for Cantonese on Windows"""

    def __init__(self):
        self.engines = {
            TTS_ENGINE.WINAPI: None,
            TTS_ENGINE.SAPI5: None,
            TTS_ENGINE.ESPEAK: None,
            TTS_ENGINE.PYTTS3: None
        }
        self.active_engine = None
        self.is_speaking = False
        self.pending_speech = None
        self.speech_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.engine_name = None
        self.voice_id = None
        self.current_rate = 0
        self.cantonese_rate = 0
        self.english_rate = 0
        self.setup_engines()

    def setup_engines(self):
        """Set up all available TTS engines"""
        self.engines = {}
        self.engines[TTS_ENGINE.WINAPI] = self.init_winapi_speech()
        self.engines[TTS_ENGINE.SAPI5] = self.init_sapi5()
        self.engines[TTS_ENGINE.ESPEAK] = self.init_espeak()
        self.engines[TTS_ENGINE.PYTTS3] = self.init_pytt3()

        # Initialize the first engine
        self.init_worker_thread()

    def init_winapi_speech(self):
        """Initialize Windows API speech engine"""
        try:
            return win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as e:
            logger.error(f"Failed to initialize Windows API speech engine: {e}")
            return None

    def init_sapi5(self):
        """Initialize SAPI5 speech engine"""
        try:
            import win32com.client
            return win32com.client.Dispatch("SAPI.SpVoice")
        except Exception as e:
            logger.error(f"Failed to initialize SAPI5 engine: {e}")
            return None

    def init_espeak(self):
        """Initialize espeak speech engine"""
        try:
            import espeakng
            return espeakng
        except Exception as e:
            logger.error(f"Failed to initialize espeak engine: {e}")
            return None

    def init_pytt3(self):
        """Initialize pyttsx3 speech engine"""
        try:
            import pyttsx3
            return pyttsx3.init()
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")
            return None

    def init_worker_thread(self):
        """Initialize the speech worker thread"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.name = "TTSWorkerThread"
        self.worker_thread.start()
        logger.info("TTS worker thread started")

    def set_active_engine(self, engine_type):
        """Set the active TTS engine"""
        engine = None

        # Try to use Windows API/SAPI5 first
        if engine_type == TTS_ENGINE.WINAPI:
            if self.engines[TTS_ENGINE.WINAPI]:
                engine = self.engines[TTS_ENGINE.WINAPI]
        # Then try SAPI5
        elif engine_type == TTS_ENGINE.SAPI5:
            if self.engines[TTS_ENGINE.SAPI5]:
                engine = self.engines[TTS_ENGINE.SAPI5]
        # Then try ESpeak
        elif engine_type == TTS_ENGINE.ESPEAK:
            if self.engines[TTS_ENGINE.ESPEAK]:
                engine = self.engines[TTS_ENGINE.ESPEAK]
        # Finally try pyttsx3
        elif engine_type == TTS_ENGINE.PYTTS3:
            if self.engines[TTS_ENGINE.PYTTS3]:
                engine = self.engines[TTS_ENGINE.PYTTS3]

        if engine:
            self.active_engine = engine
            self.engine_name = str(engine_type).split('.')[1]

            # Configure engine for Cantonese/English
            self.set_tts_lan("Chinese")  # Default to Cantonese

            # Save engine info for reference
            logger.info(f"Using {self.engine_name} engine for TTS")
            return True
        else:
            logger.error("No suitable TTS engine found")
            return False

    def get_available_voices(self):
        """Get available voices from active engine"""
        if not self.active_engine:
            return []

        try:
            if isinstance(self.active_engine, win32com.client.CDispatch):
                # SAPI5 voice selection
                voices = self.active_engine.GetVoices()
                return [voice.GetDescription() for voice in voices]
            elif isinstance(self.active_engine, pyttsx3.Engine):
                # pytts3 voice selection (simplified)
                voices = self.active_engine.getProperty('voices')
                return [voice.name for voice in voices]
            else:
                return []
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    def set_tts_lan(self, language):
        """Set the language for the TTS engine"""
        if not self.active_engine:
            return False

        voices = self.get_available_voices()
        if not voices:
            logger.warning("No voices available")
            return False

        try:
            if language == "Chinese":
                # Select a Cantonese voice
                for voice in voices:
                    if "Cantonese" in voice or "Hong Kong" in voice or "Traditional" in voice:
                        self.voice_id = voice
                        self.set_engine_voice(voice)
                        self.cantonese_rate = self.get_rate_value(language)
                        self.tts.setProperty('rate', self.cantonese_rate)
                        logger.info(f"Switched to Cantonese voice: {voice}")
                        return True
                # If no Cantonese voice, select the first available voice
                self.voice_id = voices[0]
                self.set_engine_voice(voices[0])
                self.cantonese_rate = self.get_rate_value(language)
                self.tts.setProperty('rate', self.cantonese_rate)
                logger.info(f"Using default voice: {voices[0]} (Cantonese not found)")
            elif language == "English":
                # Select an English voice
                for voice in voices:
                    if "English" in voice or "US" in voice or "UK" in voice:
                        self.voice_id = voice
                        self.set_engine_voice(voice)
                        self.english_rate = self.get_rate_value(language)
                        self.tts.setProperty('rate', self.english_rate)
                        logger.info(f"Switched to English voice: {voice}")
                        return True
                # If no English voice, select the first available voice
                self.voice_id = voices[0]
                self.set_engine_voice(voices[0])
                self.english_rate = self.get_rate_value(language)
                self.tts.setProperty('rate', self.english_rate)
                logger.info(f"Using default voice: {voices[0]} (English not found)")
            return True
        except Exception as e:
            logger.error(f"Error setting language: {e}")
            return False

    def set_engine_voice(self, voice_id):
        """Set the active voice for the engine"""
        try:
            if isinstance(self.active_engine, win32com.client.CDispatch):
                self.active_engine.Voice = self.get_sapi5_voice(voice_id)
            elif isinstance(self.active_engine, pyttsx3.Engine):
                self.active_engine.setProperty('voice', voice_id)
            return True
        except Exception as e:
            logger.error(f"Error setting voice: {e}")
            return False

    def get_sapi5_voice(self, voice_id):
        """Get a SAPI5 voice by description"""
        try:
            # This is simplified - in a real implementation, you'd need to properly
            # enumerate and select from available voices
            pass
        except:
            pass

    def get_rate_value(self, language):
        """Get appropriate rate value for language"""
        if language == "Chinese":
            return 150  # Slightly slower for Cantonese
        else:
            return 180  # Standard English rate

    def speak_line(self, text):
        """Enqueue a line to be spoken"""
        if not text.strip():
            logger.debug("Empty or whitespace-only text, skipping")
            return

        logger.info(f"Queuing speech: {text}")

        # Add to queue
        try:
            self.speech_queue.put_nowait({
                'text': text,
                'timestamp': time.time(),
                'unique_id': str(uuid.uuid4())
            })
        except queue.Full:
            logger.warning("Speech queue is full, dropping old item")

    def _speech_worker(self):
        """Worker thread for processing speech queue"""
        self.running = True

        while self.running:
            try:
                speech_item = self.speech_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            if not self.is_speaking or speech_item['unique_id'] != self.pending_speech:
                # Cancel current speech if any
                if self.is_speaking:
                    logger.info("Interrupting current speech")
                    self._cancel_current_speech()

                # Speak the text
                self.pending_speech = speech_item['unique_id']
                self.is_speaking = True
                self._speak_text(speech_item['text'])
            else:
                # Still speaking, just keep looping
                continue

    def _speak_text(self, text):
        """Actual speech implementation based on engine type"""
        try:
            if self.active_engine and isinstance(self.active_engine, win32com.client.CDispatch):
                # SAPI5
                self.active_engine.Speak(text, 0)  # Blocking=False
            elif self.active_engine and isinstance(self.active_engine, pyttsx3.Engine):
                # pyttsx3
                self.active_engine.say(text)
            else:
                logger.warning("No active TTS engine")
                return False
        except Exception as e:
            logger.error(f"Error during speech: {e}")
            self.is_speaking = False
            self.pending_speech = None
            return False

    def _cancel_current_speech(self):
        """Cancel the current speech"""
        try:
            if self.active_engine and isinstance(self.active_engine, win32com.client.CDispatch):
                self.active_engine.Speak("", 1)  # Flags=stop
                self.active_engine.Voice = None
            elif self.active_engine and isinstance(self.active_engine, pyttsx3.Engine):
                self.active_engine.stop()
            self.is_speaking = False
            self.pending_speech = None
            return True
        except Exception as e:
            logger.error(f"Error canceling speech: {e}")
            return False

    def stop(self):
        """Stop all TTS speech and clean up"""
        logger.info("Stopping TTS")
        self.running = False

        # Cancel any ongoing speech
        if self.is_speaking:
            self._cancel_current_speech()

        # Clean up engine
        self.active_engine = None

        # Stop worker thread
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)

        logger.info("TTS stopped")

    def is_speaking(self):
        """Check if TTS is currently speaking"""
        return self.is_speaking