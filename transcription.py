# transcription.py
import os
import whisper
from groq import Groq
from moviepy.editor import VideoFileClip


class Transcriber:
    def __init__(self, use_api=False, api_key=None, model_size="base", callback=None):
        self.use_api = use_api
        self.api_key = api_key
        self.model_size = model_size
        self.callback = callback

    def log(self, message):
        if self.callback:
            self.callback(message)
        else:
            print(message)

    def extract_audio(self, video_path, temp_audio_path="temp_audio.mp3"):
        self.log("Extracting audio from video...")
        try:
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(temp_audio_path, codec='mp3', verbose=False, logger=None, ffmpeg_params=["-loglevel", "error"])
            video.close()
            return temp_audio_path
        except Exception as e:
            self.log(f"Error extracting audio: {e}")
            raise

    def transcribe_api(self, audio_path):
        self.log("Connecting to Groq API...")
        client = Groq(api_key=self.api_key)
        try:
            with open(audio_path, "rb") as file:
                self.log("Sending audio to Groq (Whisper Large V3)...")
                transcription = client.audio.transcriptions.create(
                    file=(audio_path, file.read()),
                    model="whisper-large-v3",
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
            raw_words = []
            if hasattr(transcription, 'words'):
                raw_words = transcription.words
            elif hasattr(transcription, 'segments'):
                for segment in transcription.segments:
                    if 'words' in segment: raw_words.extend(segment['words'])
            elif isinstance(transcription, dict):
                raw_words = transcription.get('words', [])

            self.log(f"API Transcription complete. Found {len(raw_words)} words.")
            return self._format_words(raw_words, api_mode=True)
        except Exception as e:
            self.log(f"API Error: {e}")
            return []

    def transcribe_local(self, video_path):
        self.log(f"Loading Local Whisper model ({self.model_size})...")

        try:
            model = whisper.load_model(self.model_size)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Whisper model '{self.model_size}'.\n"
                f"This is usually caused by an unsupported CPU (AVX issue).\n\n"
                f"Details: {e}"
            )

        self.log("Transcribing locally (this may take time)...")
        result = model.transcribe(video_path, word_timestamps=True, fp16=False)
        all_words = []
        for segment in result.get("segments", []):
            for word in segment.get("words", []):
                all_words.append(word)
        return self._format_words(all_words, api_mode=False)

    def _format_words(self, raw_words, api_mode=False):
        formatted = []
        for w in raw_words:
            if api_mode:
                word_text = w.word if hasattr(w, 'word') else w.get('word', '')
                start = w.start if hasattr(w, 'start') else w.get('start', 0.0)
                end = w.end if hasattr(w, 'end') else w.get('end', 0.0)
            else:
                word_text = w.get("word", "")
                start = float(w.get("start", 0.0))
                end = float(w.get("end", 0.0))
            formatted.append({"word": word_text.strip(), "start": float(start), "end": float(end)})
        return formatted

    def run(self, video_path):
        if self.use_api:
            temp_audio = self.extract_audio(video_path)
            try:
                words = self.transcribe_api(temp_audio)
            finally:
                if os.path.exists(temp_audio): os.remove(temp_audio)
            return words
        else:
            return self.transcribe_local(video_path)