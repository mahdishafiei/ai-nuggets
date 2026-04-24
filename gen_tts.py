#!/usr/bin/env python3
"""Generate TTS audio for an AI Nuggets episode.

Usage:
    python3 gen_tts.py <script.md> <output.mp3>

Reads MISTRAL_API_KEY and ELEVENLABS_API_KEY from .env (or environment).
Primary: Mistral voxtral-mini-tts-2603 (voice en_paul_neutral).
Fallback: ElevenLabs Bella (hpp4J3VqNfWAUOO0d1Us) with eleven_flash_v2_5.

Includes a duration sanity check: if the rendered audio is shorter than
script_chars / 18 (a conservative floor), regenerate once. Aborts with a
nonzero exit if the second attempt is still short.
"""
import argparse, base64, json, os, subprocess, sys, tempfile
import requests

MISTRAL_URL = "https://api.mistral.ai/v1/audio/speech"
MISTRAL_MODEL = "voxtral-mini-tts-2603"
MISTRAL_VOICE = "en_paul_neutral"
# Keep chunks small: reduces per-call truncation risk and makes per-chunk
# duration sanity check tighter. Mistral can handle much more, but we gain
# nothing by pushing it.
MISTRAL_CHUNK_MAX = 3000
MISTRAL_CHUNK_RETRIES = 2

ELEVENLABS_VOICE = "hpp4J3VqNfWAUOO0d1Us"
ELEVENLABS_MODEL = "eleven_flash_v2_5"
ELEVENLABS_CHUNK_MAX = 3000

# Paul Neutral typically runs 14-21 chars/sec depending on chunk size and
# punctuation density. A healthy chunk should take at least chars /
# MAX_CHARS_PER_SECOND seconds. 25 tolerates natural speed variance
# (including the faster end observed on small chunks) while still catching
# truncation that drops >~35% of a chunk.
MAX_CHARS_PER_SECOND = 25

def load_env():
    env = dict(os.environ)
    repo_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(repo_env):
        for line in open(repo_env):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return env

def extract_script_body(path):
    text = open(path).read()
    if "## Script" in text:
        text = text.split("## Script", 1)[1]
    lines = [l for l in text.strip().split("\n") if not l.strip().startswith("Paper link:")]
    return "\n".join(lines).strip()

def chunk_text(text, max_chars):
    if len(text) <= max_chars:
        return [text]
    chunks, current = [], ""
    for para in text.split("\n\n"):
        if len(current) + len(para) > max_chars and current:
            chunks.append(current.strip())
            current = para
        else:
            current = current + "\n\n" + para if current else para
    if current.strip():
        chunks.append(current.strip())
    return chunks

def stitch(parts, output):
    if len(parts) == 1:
        open(output, "wb").write(parts[0])
        return
    with tempfile.TemporaryDirectory() as tmp:
        manifest = os.path.join(tmp, "list.txt")
        with open(manifest, "w") as mf:
            for j, part in enumerate(parts):
                pp = os.path.join(tmp, f"part{j}.mp3")
                open(pp, "wb").write(part)
                mf.write(f"file '{pp}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", manifest, "-c", "copy", output],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )

def mp3_bytes_duration(audio_bytes):
    """Probe duration of mp3 bytes via ffprobe on a tempfile."""
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tf:
        tf.write(audio_bytes)
        path = tf.name
    try:
        return duration_seconds(path)
    finally:
        os.unlink(path)

def mistral_synthesize(chunk, api_key):
    r = requests.post(
        MISTRAL_URL,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": MISTRAL_MODEL, "input": chunk, "voice_id": MISTRAL_VOICE, "response_format": "mp3"},
        timeout=300,
    )
    r.raise_for_status()
    data = r.json()
    audio_b64 = data.get("audio_data") or data.get("data")
    if not audio_b64:
        raise RuntimeError(f"Mistral response missing audio_data; keys={list(data.keys())}")
    return base64.b64decode(audio_b64)

def elevenlabs_synthesize(chunk, api_key):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE}",
        headers={"xi-api-key": api_key, "Content-Type": "application/json"},
        json={
            "text": chunk,
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": 1.1},
        },
        timeout=300,
    )
    r.raise_for_status()
    return r.content

def synthesize_chunks(chunks, synth_fn, label):
    """Synthesize each chunk, validating duration and retrying on truncation.

    synth_fn(chunk) -> mp3 bytes. Raises on unrecoverable failure.
    """
    parts = []
    for i, chunk in enumerate(chunks):
        min_dur = len(chunk) / MAX_CHARS_PER_SECOND
        last_err = None
        for attempt in range(1, MISTRAL_CHUNK_RETRIES + 2):
            try:
                audio = synth_fn(chunk)
                dur = mp3_bytes_duration(audio)
                if dur < min_dur:
                    last_err = f"chunk duration {dur:.1f}s < floor {min_dur:.1f}s (likely truncated)"
                    print(f"  [{label}] chunk {i+1}/{len(chunks)} attempt {attempt} FAILED: {last_err}")
                    continue
                print(f"  [{label}] chunk {i+1}/{len(chunks)} ({len(chunk)} chars) -> {dur:.1f}s ✓")
                parts.append(audio)
                break
            except Exception as e:
                last_err = str(e)
                print(f"  [{label}] chunk {i+1}/{len(chunks)} attempt {attempt} error: {e}")
        else:
            raise RuntimeError(f"{label} chunk {i+1} failed after retries: {last_err}")
    return parts

def mistral_tts(text, api_key, output):
    chunks = chunk_text(text, MISTRAL_CHUNK_MAX)
    parts = synthesize_chunks(chunks, lambda c: mistral_synthesize(c, api_key), "mistral")
    stitch(parts, output)

def elevenlabs_tts(text, api_key, output):
    chunks = chunk_text(text, ELEVENLABS_CHUNK_MAX)
    parts = synthesize_chunks(chunks, lambda c: elevenlabs_synthesize(c, api_key), "elevenlabs")
    stitch(parts, output)

def duration_seconds(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path]
    ).decode().strip()
    return float(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("script")
    ap.add_argument("output")
    args = ap.parse_args()

    env = load_env()
    if "MISTRAL_API_KEY" not in env and "ELEVENLABS_API_KEY" not in env:
        print("ERROR: no MISTRAL_API_KEY or ELEVENLABS_API_KEY in .env or environment", file=sys.stderr)
        sys.exit(2)

    text = extract_script_body(args.script)
    print(f"Script body: {len(text)} chars, chunk cap {MISTRAL_CHUNK_MAX}")

    try:
        mistral_tts(text, env["MISTRAL_API_KEY"], args.output)
        used = "mistral"
    except Exception as e:
        print(f"Mistral path failed: {e}. Falling back to ElevenLabs.")
        if "ELEVENLABS_API_KEY" not in env:
            print("ERROR: no ELEVENLABS_API_KEY available for fallback", file=sys.stderr)
            sys.exit(4)
        try:
            elevenlabs_tts(text, env["ELEVENLABS_API_KEY"], args.output)
            used = "elevenlabs"
        except Exception as e2:
            print(f"ERROR: both Mistral and ElevenLabs failed: {e2}", file=sys.stderr)
            sys.exit(3)

    dur = duration_seconds(args.output)
    size = os.path.getsize(args.output)
    print(f"Done: {args.output} [{used}] {size:,} bytes, {dur:.1f}s")

if __name__ == "__main__":
    main()
