"""
stream_transcribe.py — Wake-word activated transcription via NVIDIA NIM (gRPC)

Wake word : "jarvis"
End       : 1 seconds of silence after activation
Display   : live interim results shown in terminal while listening
Output    : ../ipc_data/user_goal.txt  (only final confirmed text saved)

Usage:
    python stream_transcribe.py
    python stream_transcribe.py --device_index 0
    python stream_transcribe.py --list_devices
    python stream_transcribe.py --chunk_ms 1120

Press Ctrl+C to quit.
"""

import argparse
import os
import queue
import sys
import threading
from dotenv import load_dotenv

# Enable ANSI escape codes on Windows PowerShell
if sys.platform == "win32":
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

import pyaudio
import riva.client

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

NIM_API_KEY = os.environ["NVIDIA_API_KEY"]
NIM_GRPC_ENDPOINT    = "grpc.nvcf.nvidia.com:443"
NEMOTRON_FUNCTION_ID = "1598d209-5e27-4d3c-8079-4751568b1081"

SAMPLE_RATE     = 16000
CHANNELS        = 1
VALID_CHUNK_MS  = [80, 160, 560, 1120]

WAKE_WORD       = "nemo"
SILENCE_TIMEOUT = 1.0
OUTPUT_DIR      = "ipc_data_one"
OUTPUT_FILE     = os.path.join(OUTPUT_DIR, "transcript.txt")


# ---------------------------------------------------------------------------
# Microphone capture
# ---------------------------------------------------------------------------

class MicrophoneCapture:
    """Captures mic audio via PyAudio callback and feeds into a queue."""

    def __init__(self, chunk_ms: int = 160, device_index=None):
        self.chunk_ms     = chunk_ms
        self.chunk_frames = int(SAMPLE_RATE * chunk_ms / 1000)
        self.device_index = device_index
        self._queue   = queue.Queue()
        self._pa      = pyaudio.PyAudio()
        self._stream  = None
        self._stopped = False

    def list_devices(self):
        print("\nAvailable input devices:")
        for i in range(self._pa.get_device_count()):
            info = self._pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"  [{i}] {info['name']}")
        print()

    def start(self):
        self._stream = self._pa.open(
            format=pyaudio.paInt16,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            input_device_index=self.device_index,
            frames_per_buffer=self.chunk_frames,
            stream_callback=self._callback,
        )
        self._stream.start_stream()
        print(
            f"Mic open — {self.chunk_ms}ms chunks "
            f"({self.chunk_frames} frames). Ctrl+C to quit.\n"
        )

    def _callback(self, in_data, frame_count, time_info, status):
        if not self._stopped:
            self._queue.put(in_data)
        return (None, pyaudio.paContinue)

    def __iter__(self):
        while True:
            try:
                chunk = self._queue.get(timeout=0.5)
                if chunk is None:
                    break
                yield chunk
            except queue.Empty:
                if self._stopped:
                    break

    def stop(self):
        self._stopped = True
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        self._pa.terminate()
        self._queue.put(None)
        print("\nMic stopped.")


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_goal(text: str):
    """Write only the final confirmed transcript to ipc_data/user_goal.txt."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")
    print(f'\nSaved to {OUTPUT_FILE}:\n   "{text.strip()}"')

    trigger_path = os.path.join(OUTPUT_DIR, "trigger1.txt")
    open(trigger_path, 'a').close() 
    print(f"Created trigger file at {trigger_path}")
    # ------------------------------------------

    print(f'\n💤 Waiting for wake word: "{WAKE_WORD}"\n')


# ---------------------------------------------------------------------------
# Streaming transcription
# ---------------------------------------------------------------------------

def run_streaming(api_key: str, mic: MicrophoneCapture):
    auth = riva.client.Auth(
        uri=NIM_GRPC_ENDPOINT,
        use_ssl=True,
        metadata_args=[
            ["authorization", f"Bearer {api_key}"],
            ["function-id", NEMOTRON_FUNCTION_ID],
        ],
    )

    asr_service = riva.client.ASRService(auth)
    config = riva.client.StreamingRecognitionConfig(
        config=riva.client.RecognitionConfig(
            encoding=riva.client.AudioEncoding.LINEAR_PCM,
            language_code="en-US",
            max_alternatives=1,
            enable_automatic_punctuation=True,
            verbatim_transcripts=False,
            sample_rate_hertz=SAMPLE_RATE,
            audio_channel_count=CHANNELS,
        ),
        interim_results=True,
    )

    print("Connecting to NVIDIA NIM (gRPC)…")
    responses = asr_service.streaming_response_generator(
        audio_chunks=mic,
        streaming_config=config,
    )
    print(f'Connected.\n\n💤 Waiting for wake word: "{WAKE_WORD}"\n')

    # State
    active         = False
    captured_parts = []       # accumulates final segments after wake word
    silence_timer  = [None]

    def commit():
        """Triggered by 3s silence — save finals and return to idle."""
        nonlocal active, captured_parts
        if not active:
            return
        active = False
        full_text = " ".join(captured_parts).strip()
        captured_parts = []
        print(f"\r\033[K3s silence — ending capture.")
        if full_text:
            save_goal(full_text)
        else:
            print("   (nothing captured)")
        print(f'\n💤 Waiting for wake word: "{WAKE_WORD}"\n')
        mic.stop()


    def reset_silence_timer():
        if silence_timer[0]:
            silence_timer[0].cancel()
        t = threading.Timer(SILENCE_TIMEOUT, commit)
        t.daemon = True
        t.start()
        silence_timer[0] = t

    try:
        for response in responses:
            for result in response.results:
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                is_final   = result.is_final
                lower      = transcript.lower()

                if not active:
                    # --- IDLE: only check for wake word on final results ---
                    if is_final and WAKE_WORD in lower:
                        active = True
                        captured_parts = []
                        # Strip wake word from the beginning of this segment
                        idx = lower.find(WAKE_WORD)
                        remainder = transcript[idx + len(WAKE_WORD):].strip(" ,.!?")
                        if remainder:
                            captured_parts.append(remainder)
                        print(f"\r\033[KJarvis activated! Listening…\n")
                        reset_silence_timer()

                else:
                    # --- ACTIVE: show live text, accumulate finals only ---
                    if is_final:
                        captured_parts.append(transcript.strip())
                        print(f"\r\033[K{transcript}")   # confirmed line
                        reset_silence_timer()
                    else:
                        # Live interim — shown in terminal, NOT saved
                        print(f"\r\033[K{transcript}", end="", flush=True)

    except KeyboardInterrupt:
        # Save whatever was captured if interrupted mid-session
        if silence_timer[0]:
            silence_timer[0].cancel()
        if active and captured_parts:
            save_goal(" ".join(captured_parts))
    except Exception as e:
        print(f"\nError: {e}")
        raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Jarvis wake-word ASR → saves goal to ../ipc_data/user_goal.txt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Say "{WAKE_WORD}" to activate, then speak your goal.
After {SILENCE_TIMEOUT:.0f} seconds of silence the transcript is saved.

Live lines are shown in the terminal but NOT written to the file.
Only confirmed final lines are saved.

Chunk size tradeoffs:
  80ms   — Lowest latency
  160ms  — Good balance (default)
  1120ms — Best accuracy
        """,
    )
    parser.add_argument("--chunk_ms",     type=int, default=160, choices=VALID_CHUNK_MS,
                        help="Audio chunk size in ms (default: 160)")
    parser.add_argument("--device_index", type=int, default=None,
                        help="PyAudio input device index")
    parser.add_argument("--list_devices", action="store_true",
                        help="List available mic devices and exit")
    parser.add_argument("--api_key",      type=str, default=NIM_API_KEY,
                        help="NVIDIA NIM API key")
    args = parser.parse_args()

    mic = MicrophoneCapture(chunk_ms=args.chunk_ms, device_index=args.device_index)

    if args.list_devices:
        mic.list_devices()
        return

    mic.start()
    try:
        run_streaming(args.api_key, mic)
    finally:
        mic.stop()


if __name__ == "__main__":
    main()