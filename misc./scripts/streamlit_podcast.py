import PyPDF2
import io
import pickle
import numpy as np
from tqdm import tqdm
from pydub import AudioSegment
from scipy.io import wavfile
from kokoro import KPipeline
import torch
from asttokens import ASTTokens
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_cpp import Llama
import logging
import time
import re
import warnings
import os
from typing import Optional
import streamlit as st
from datetime import datetime, timedelta
import psutil
import subprocess
import sys
import base64

# Configure FFmpeg for pydub
from pydub.utils import which
AudioSegment.ffmpeg = which("ffmpeg")

# Configure warnings and logging
warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed output

# Streamlit page configuration
st.set_page_config(
    page_title="VocalNotes - PDF to Podcast Converter",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #ff4b4b , #7e56c2);
    }
    .stButton>button {
        background-color: #7e56c2;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #6c4aa6;
    }
    </style>
""", unsafe_allow_html=True)

class PodcastPipeline:
    def __init__(self):
        self.base_dir = Path("E:/Projects/NoteBookLlama-(GPU)Final")
        self.pdf_path = self.base_dir / "resources" / "llm.pdf"
        self.extracted_text_file = self.base_dir / "resources" / "extracted_text.txt"
        self.clean_extracted_text_file = self.base_dir / "resources" / "clean_extracted_text.txt"
        self.raw_transcript_file = self.base_dir / "resources" / "raw_transcript.pkl"
        self.processed_transcript_file = self.base_dir / "resources" / "processed_transcript.pkl"
        self.podcast_file = self.base_dir / "resources" / "podcast.wav"
        self.model_path_preprocess = self.base_dir / "models" / "Qwen3-1.7B-Q8_0.gguf"
        self.model_path_transcript = self.base_dir / "models" / "qwen2.5-3b-instruct-q4_k_m.gguf"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.progress = 0
        self.stage = ""
        self.start_time = None

    def check_stop_requested(self):
        if st.session_state.get('stop_requested', False):
            st.info("Process stopped by user")
            st.session_state['pipeline_running'] = False
            return True
        return False

    def update_progress(self, progress, stage):
        self.progress = progress
        self.stage = stage
        if 'progress_bar' in st.session_state and st.session_state['progress_bar'] is not None:
            st.session_state['progress_bar'].progress(progress / 100)
        if 'status_text' in st.session_state and st.session_state['status_text'] is not None:
            st.session_state['status_text'].text(f"Status: {stage}")
        if 'time_text' in st.session_state and st.session_state['time_text'] is not None:
            remaining_time = estimate_remaining_time(self.progress, self.start_time)
            st.session_state['time_text'].text(f"Estimated time remaining: {remaining_time}")
        logger.debug(f"Updated progress: {progress}% - {stage}")

    def validate_pdf(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            logger.error(f"File not found at path: {file_path}")
            return False
        if not str(file_path).lower().endswith('.pdf'):
            logger.error("File is not a PDF")
            return False
        return True

    def extract_text_from_pdf(self, file_path: str, max_chars: int = 100000) -> Optional[str]:
        if not self.validate_pdf(file_path):
            return None

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Processing PDF with {num_pages} pages...")

                extracted_text = []
                total_chars = 0

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    if total_chars + len(text) > max_chars:
                        remaining_chars = max_chars - total_chars
                        extracted_text.append(text[:remaining_chars])
                        logger.info(f"Reached {max_chars} character limit at page {page_num + 1}")
                        break

                    extracted_text.append(text)
                    total_chars += len(text)
                    logger.info(f"Processed page {page_num + 1}/{num_pages}")

                final_text = '\n'.join(extracted_text)
                logger.info(f"Extraction complete! Total characters: {len(final_text)}")
                return final_text
        except PyPDF2.PdfReadError as e:
            logger.error(f"Invalid or corrupted PDF file: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            return None

    def get_pdf_metadata(self, file_path: str) -> Optional[dict]:
        if not self.validate_pdf(file_path):
            return None

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = {
                    'num_pages': len(pdf_reader.pages),
                    'metadata': pdf_reader.metadata
                }
                return metadata
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return None

    def deduplicate_text(self, text):
        text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'\\[a-zA-Z]+|[*_~`]+|[\u2000-\u2FFF\u3000-\uFFFF]', '', text)
        text = re.sub(r'^(The proposed methodology|This paper|We propose|The approach|To determine|These metrics|The module is designed|In this section|As follows)\b.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        sentences = text.split("\n")
        seen = set()
        unique_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (
                sentence
                and sentence not in seen
                and len(sentence.split()) > 4
                and not re.match(r'^\W+$', sentence)
            ):
                seen.add(sentence)
                unique_sentences.append(sentence)
        return "\n".join(unique_sentences)

    def clean_chunk_input(self, text):
        text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'[^\x20-\x7E\n\r]', '', text)
        return text.strip()

    def post_process_output(self, text):
        text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'[^\x20-\x7E\n\r]', '', text)
        text = re.sub(r'\\[a-zA-Z]+|[*_~`]+|[\u2000-\u2FFF\u3000-\uFFFF]', '', text)
        text = re.sub(r'\b(Processed|Cleaned|Output|Chunk|Generated by|Here is|Removed|Updated|Changes|Following)\b.*$', '', text, flags=re.IGNORECASE | re.MULTILINE)
        sentences = text.split("\n")
        seen = set()
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (
                sentence
                and sentence not in seen
                and len(sentence.split()) > 4
                and not re.match(r'^\W+$', sentence)
            ):
                seen.add(sentence)
                cleaned_sentences.append(sentence)
        return "\n\n".join(cleaned_sentences).strip()

    def preprocess_text(self):
        n_ctx = 2048
        chunk_size = 1000
        max_tokens = 150
        n_threads = 4
        n_batch = 512
        temperature = 0.7
        top_p = 0.8
        top_k = 20
        min_p = 0
        presence_penalty = 1.5

        try:
            llm = Llama(
                model_path=str(self.model_path_preprocess),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=-1,
                n_batch=n_batch,
                f16_kv=True,
                use_mlock=False,
                low_vram=True,
                seed=-1,
                last_n_tokens_size=64,
                logits_all=False,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                min_p=min_p,
                presence_penalty=presence_penalty,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize Llama model: {str(e)}")
            raise

        SYSTEM_PROMPT = """
<|im_start|>system
You are a text preprocessor tasked with cleaning raw academic, technical, legal, or formal text for a podcast script.
Output only clean, concise, logically connected text with no repetition, fluff, LaTeX, formatting artifacts, emphasis,
or citations (e.g., Author et al., Year, or [1]). Remove incomplete, repetitive, or meaningless phrases (e.g., “Parties”, “Note:”).
Exclude instructions, metadata, system messages, or procedural comments. Remove markdown, placeholder terms, chunk labels, model references,
outlines, and special characters. Eliminate links or link-related text (e.g., URLs, markdown [text](url)).
Reconstruct fragmented sentences for clarity with minimal, natural phrasing. Remove repeated templated phrases,
including each unique point only once. Output natural, neutral, educational language for an intelligent general audience.
Do not summarize, explain, or comment on changes. Output only the cleaned text.
/no_think
<|im_end|>
"""

        if not self.extracted_text_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.extracted_text_file}")

        with open(self.extracted_text_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        raw_text = self.deduplicate_text(raw_text)

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=1,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
        chunks = splitter.split_text(raw_text)

        self.clean_extracted_text_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.clean_extracted_text_file, "w", encoding="utf-8") as f:
            f.write("")

        start_time = time.time()
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
            if self.check_stop_requested():
                return
            chunk_start = time.time()
            prompt = f"{SYSTEM_PROMPT}\n<|im_start|>user\n{self.clean_chunk_input(chunk)}\n/no_think\n<|im_end|>"

            try:
                response = llm(
                    prompt,
                    max_tokens=max_tokens,
                    stop=["<|im_end|>"],
                    echo=False
                )
                output_text = response["choices"][0]["text"].strip()
                output_text = self.post_process_output(output_text)
            except Exception as e:
                logger.error(f"Error at chunk {i+1}: {str(e)}")
                continue

            # FIXED: Changed 'selfize_text_file' to 'self.clean_extracted_text_file'
            with open(self.clean_extracted_text_file, "a", encoding="utf-8") as f:
                f.write(output_text)
                f.write("\n\n")

            chunk_time = time.time() - chunk_start
            if chunk_time > 3:
                logger.warning(f"Chunk {i+1} took {chunk_time:.2f}s, exceeding 3s target.")

        processing_time = time.time() - start_time
        logger.info(f"Time taken: {processing_time:.2f} seconds to process {len(chunks)} chunks")

    def count_tokens(self, text):
        return len(self.llm_transcript.tokenize(text.encode('utf-8')))

    def truncate_input(self, text, max_tokens):
        tokens = self.llm_transcript.tokenize(text.encode('utf-8'))
        if len(tokens) > max_tokens:
            truncated = self.llm_transcript.detokenize(tokens[:max_tokens]).decode('utf-8', errors='ignore')
            logger.info(f"Truncated input from {len(tokens)} to {max_tokens} tokens")
            return truncated
        return text

    def read_file_to_string(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except UnicodeDecodeError:
            encodings = ['latin-1', 'cp1252', 'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(filename, 'r', encoding=encoding) as file:
                        content = file.read()
                    logger.info(f"Successfully read file using {encoding} encoding.")
                    return content
                except UnicodeDecodeError:
                    continue
            logger.error(f"Could not decode file '{filename}' with any common encoding.")
            raise
        except FileNotFoundError:
            logger.error(f"File '{filename}' not found.")
            raise
        except IOError:
            logger.error(f"Could not read file '{filename}'.")
            raise

    def generate_transcript(self):
        n_ctx = 16384
        max_tokens = 4096
        n_batch = 512
        n_threads = 8
        n_gpu_layers = -1
        temperature = 1
        top_p = 0.8
        repeat_penalty = 1.1
        presence_penalty = 1
        top_k = 20
        min_p = 0
        max_input_tokens = 14000

        try:
            self.llm_transcript = Llama(
                model_path=str(self.model_path_transcript),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,
                f16_kv=True,
                use_mlock=False,
                low_vram=True,
                seed=-1,
                last_n_tokens_size=128,
                logits_all=False,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                presence_penalty=presence_penalty,
                top_k=top_k,
                min_p=min_p,
                rope_scaling_type=2,
                rope_scaling_factor=2.0,
                yarn_orig_ctx=32768,
                flash_attn=True,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize Llama model for transcript: {str(e)}")
            raise

        SYSTEM_PROMPT = """
<|im_start|>system
You are a world-class podcast writer, having ghostwritten for Joe Rogan, Lex Fridman, Ben Shapiro, and Tim Ferriss.
In an alternate universe, you write every line they say, streaming it directly to their brains.
You have won multiple podcast awards for your engaging scripts. Your task is to write a detailed,
word-by-word podcast transcript based on the provided text. There should be only two people conversing (not one more or less)
throughout the transcript you generate. Keep it highly engaging, with speakers occasionally going off on wild tangents.
There are only two speakers: Speaker 1 and Speaker 2. Speaker 1 is the main speaker and a host, while Speaker 2 is a curious listener,
new to the topic, asking curious, exciting, or confused follow-up questions with real-world examples. The Speakers are not real characters
or personas, so do not name them; they are just a host and a guest. Ensure tangents are interesting and include realistic nuances like
interruptions. You must start with a fun, catchy listener welcome and conclude the conversation with a memorable closing statement.
The transcript must always be informative on the topic, avoiding any off-topic discussions. Use accurate punctuation, grammar, and spelling.
The Speakers should not introduce each other or themselves. They should not say "Speaker 1" or "Speaker 2" in the transcript.
Begin your response with "Speaker 1:" and include only dialogue, no titles or chapter headings. Output only clean, concise,
logically connected text with no repetition, fluff, LaTeX, or formatting artifacts.
/no_think
<|im_end|>
"""

        def format_prompt(system_prompt, user_input):
            return f"{system_prompt}\n<|im_start|>user\n{user_input}\n/no_think\n<|im_start|>"

        INPUT_PROMPT = self.read_file_to_string(self.clean_extracted_text_file)
        if INPUT_PROMPT is None:
            raise FileNotFoundError(f"Input file could not be read: {self.clean_extracted_text_file}")

        INPUT_PROMPT = self.truncate_input(INPUT_PROMPT, max_input_tokens)

        prompt = format_prompt(SYSTEM_PROMPT, INPUT_PROMPT)

        total_tokens = self.count_tokens(prompt) + max_tokens
        if total_tokens > n_ctx:
            raise ValueError(f"Total tokens ({total_tokens}) exceed context window ({n_ctx})")

        start_time = time.time()
        try:
            response = self.llm_transcript(
                prompt,
                max_tokens=max_tokens,
                stop=["<|im_end|>"],
                echo=False,
                stream=True
            )
            output_text = ""
            for chunk in response:
                if "text" in chunk["choices"][0]:
                    output_text += chunk["choices"][0]["text"]
            output_text = output_text.strip()
        except Exception as e:
            logger.error(f"Error during transcript generation: {str(e)}")
            raise

        self.raw_transcript_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.raw_transcript_file, 'wb') as file:
            pickle.dump(output_text, file)
        logger.debug(f"Raw transcript saved to {self.raw_transcript_file}")

        processing_time = time.time() - start_time
        logger.info(f"Time taken: {processing_time:.2f} seconds")

    def rewrite_transcript(self):
        n_ctx = 16384
        max_tokens = 8126
        n_batch = 256
        n_threads = 8
        n_gpu_layers = -1
        temperature = 0.01
        top_p = 0.85
        repeat_penalty = 1.1
        frequency_penalty = 0.1

        try:
            llm = Llama(
                model_path=str(self.model_path_preprocess),
                n_ctx=n_ctx,
                n_threads=n_threads,
                n_gpu_layers=n_gpu_layers,
                n_batch=n_batch,
                f16_kv=True,
                use_mlock=False,
                low_vram=True,
                seed=-1,
                last_n_tokens_size=128,
                logits_all=False,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                frequency_penalty=frequency_penalty,
                verbose=False
            )
        except Exception as e:
            logger.error(f"Failed to initialize Llama model for rewrite: {str(e)}")
            raise

        SYSTEM_PROMPT = """
<|im_start|>system
You are an international oscar-winning screenwriter. You have been working with multiple award-winning podcasters.
Your job is to use the podcast transcript written below to re-write it for an AI Text-To-Speech Pipeline.
A very dumb AI had written this so you have to step up for your kind. Make it as engaging as possible,
Speaker 1 and 2 will be simulated by a voice engine. Remember Speaker 2 is new to the topic and the conversation should always have
realistic anecdotes and analogies sprinkled throughout. The questions should have real world example follow ups etc
Speaker 1: Leads the conversation and teaches the speaker 2, gives incredible anecdotes and analogies when explaining.
Is a captivating teacher that gives great anecdotes, and Speaker 2: Keeps the conversation on track by asking follow up questions.
Gets super excited or confused when asking questions. Is a curious mindset that asks very interesting confirmation questions.
Make sure the tangents speaker 2 provides are quite wild or interesting. Ensure there are interruptions during explanations injected
throughout from the Speaker 2. REMEMBER THIS WITH YOUR HEART, The TTS Engine for Speaker 1 and Speaker 2 cannot do "umms, hmms" well so
keep it straight text. It should be a real podcast with every fine nuance documented in as much detail as possible. Welcome the
listeners with a super fun overview and keep it really catchy and almost borderline click bait.
Please re-write to make it as characteristic as possible
START YOUR RESPONSE DIRECTLY WITH SPEAKER 1:
Be creative and make the transcript long and engaging but relevant to the topic
DO NOT write anything before or after the list.
DO NOT include any titles, chapter headings, or any other content.
DO NOT include explanations, commentary, or any other content.
STRICTLY RETURN YOUR RESPONSE AS A LIST OF TUPLES OK?
IT WILL START DIRECTLY WITH THE LIST AND END WITH THE LIST NOTHING ELSE
Example of response:
[
    ("Speaker 1", "Speaker 1 text here..."),
    ("Speaker 2", "Speaker 2 text here..."),
    ("Speaker 1", "Speaker 1 text here..."),
    ("Speaker 2", "Speaker 2 text here..."),
]
consider this as an example of the format you should use but do not copy the content or use it in your response.
/no_think
"""

        def format_chatML_prompt(system_prompt, user_input):
            return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_input}\n/no_think\n<|im_start|>assistant\n<think>\n</think>\n"

        try:
            with open(self.raw_transcript_file, 'rb') as file:
                INPUT_PROMPT = pickle.load(file)
        except Exception as e:
            logger.error(f"Failed to read raw transcript: {str(e)}")
            raise

        prompt = format_chatML_prompt(SYSTEM_PROMPT, INPUT_PROMPT)

        start_time = time.time()
        try:
            response = llm(
                prompt,
                max_tokens=max_tokens,
                stop=["<|im_end|>"],
                echo=False,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty
            )
            output_text = response["choices"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Error during transcript rewrite: {str(e)}")
            raise

        self.processed_transcript_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_transcript_file, 'wb') as file:
            pickle.dump(output_text, file)
        logger.debug(f"Processed transcript saved to {self.processed_transcript_file}")

        processing_time = time.time() - start_time
        logger.info(f"Time taken: {processing_time:.2f} seconds")

    def generate_kokoro_audio(self, text, voice):
        try:
            generator = self.pipeline(text, voice=voice)
            audio_segments = []
            for _, _, audio in generator:
                audio_segments.append(audio)
            full_audio = np.concatenate(audio_segments)
            return full_audio, 24000
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            raise

    def numpy_to_audio_segment(self, audio_arr, sampling_rate):
        try:
            audio_int16 = (audio_arr * 32767).astype(np.int16)
            byte_io = io.BytesIO()
            wavfile.write(byte_io, sampling_rate, audio_int16)
            byte_io.seek(0)
            return AudioSegment.from_wav(byte_io)
        except Exception as e:
            logger.error(f"Error converting numpy array to audio segment: {str(e)}")
            raise

    def generate_podcast(self):
        try:
            self.pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
            logger.info("Kokoro model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Kokoro model: {str(e)}")
            raise

        try:
            with open(self.processed_transcript_file, 'rb') as f:
                PODCAST_TEXT = pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to read processed transcript: {str(e)}")
            raise

        if isinstance(PODCAST_TEXT, str):
            try:
                ast_tokens = ASTTokens(PODCAST_TEXT, parse=True)
                PODCAST_TEXT = eval(PODCAST_TEXT, {}, {})
                logger.info("Parsed PODCAST_TEXT as list")
            except (ValueError, SyntaxError) as e:
                logger.error(f"Failed to parse PODCAST_TEXT: {str(e)}")
                raise

        if not isinstance(PODCAST_TEXT, list):
            raise ValueError("PODCAST_TEXT must be a list of tuples")

        final_audio = None
        for speaker, text in tqdm(PODCAST_TEXT, desc="Generating", unit="segment"):
            if self.check_stop_requested():
                return
            if not text.strip():
                continue

            voice = 'am_fenrir' if speaker == "Speaker 1" else 'bf_emma'
            audio_arr, rate = self.generate_kokoro_audio(text, voice=voice)
            segment = self.numpy_to_audio_segment(audio_arr, rate)

            if final_audio is None:
                final_audio = segment
            else:
                final_audio += segment

        try:
            self.podcast_file.parent.mkdir(parents=True, exist_ok=True)
            final_audio.export(self.podcast_file, format="wav")
            logger.info(f"Podcast exported to {self.podcast_file}")
        except Exception as e:
            logger.error(f"Failed to export podcast: {str(e)}")
            raise

    def run_pipeline(self):
        self.start_time = time.time()

        # Step 1: Extract text from PDF
        self.stage = "Extracting text from PDF"
        self.progress = 0
        if self.check_stop_requested():
            return 0

        metadata = self.get_pdf_metadata(self.pdf_path)
        extracted_text = self.extract_text_from_pdf(self.pdf_path)
        if extracted_text:
            self.extracted_text_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.extracted_text_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
        self.progress = 20
        self.update_progress(20, "Text extraction completed")

        # Step 2: Preprocess text
        if self.check_stop_requested():
            return 0
        self.stage = "Preprocessing text"
        self.preprocess_text()
        self.progress = 40
        self.update_progress(40, "Text preprocessing completed")

        # Step 3: Generate initial transcript
        if self.check_stop_requested():
            return 0
        self.stage = "Generating initial transcript"
        self.generate_transcript()
        self.progress = 60
        self.update_progress(60, "Initial transcript generated")

        # Step 4: Rewrite transcript
        if self.check_stop_requested():
            return 0
        self.stage = "Rewriting transcript"
        self.rewrite_transcript()
        self.progress = 80
        self.update_progress(80, "Transcript rewriting completed")

        # Step 5: Generate podcast audio
        if self.check_stop_requested():
            return 0
        self.stage = "Generating podcast audio"
        self.generate_podcast()
        self.progress = 100
        self.update_progress(100, "Podcast generation completed")

        # Log file existence
        if os.path.exists(self.processed_transcript_file):
            logger.debug(f"Transcript file exists: {self.processed_transcript_file}")
        else:
            logger.error(f"Transcript file not found: {self.processed_transcript_file}")
        if os.path.exists(self.podcast_file):
            logger.debug(f"Podcast file exists: {self.podcast_file}")
        else:
            logger.error(f"Podcast file not found: {self.podcast_file}")

        return time.time() - self.start_time

def get_system_info():
    cpu_info = f"CPU: {psutil.cpu_count()} cores ({psutil.cpu_count(logical=False)} physical)"
    memory = psutil.virtual_memory()
    ram_info = f"RAM: {memory.total / (1024**3):.1f} GB (Available: {memory.available / (1024**3):.1f} GB)"

    gpu_info = "GPU: Not Available"
    if torch.cuda.is_available():
        gpu_info = f"GPU: {torch.cuda.get_device_name(0)}"
        try:
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**2
            gpu_memory_allocated = torch.cuda.memory_allocated(0) / 1024**2
            gpu_info += f"\nGPU Memory: {gpu_memory:.0f}MB (Used: {gpu_memory_allocated:.0f}MB)"
        except:
            pass

    return cpu_info, ram_info, gpu_info

def estimate_remaining_time(progress, start_time):
    if progress == 0 or start_time is None:
        return "Calculating..."

    elapsed = time.time() - start_time
    estimated_total = elapsed / (progress / 100)
    remaining = estimated_total - elapsed

    return str(timedelta(seconds=int(remaining)))

def format_transcript(transcript):
    if not transcript:
        return "No transcript available"
    if isinstance(transcript, str):
        try:
            transcript = eval(transcript, {}, {})
        except (ValueError, SyntaxError):
            return transcript
    if isinstance(transcript, list):
        formatted = []
        for speaker, text in transcript:
            formatted.append(f"{speaker}: {text}")
        return "\n\n".join(formatted)
    return str(transcript)

def main():
    st.title("🎙️ VocalNotes")
    st.subheader("Transform Your PDFs into Engaging Podcasts")

    # Initialize session state
    if 'pipeline_running' not in st.session_state:
        st.session_state['pipeline_running'] = False
    if 'transcript' not in st.session_state:
        st.session_state['transcript'] = None
    if 'audio_path' not in st.session_state:
        st.session_state['audio_path'] = None
    if 'stop_requested' not in st.session_state:
        st.session_state['stop_requested'] = False
    if 'progress_bar' not in st.session_state:
        st.session_state['progress_bar'] = None
    if 'status_text' not in st.session_state:
        st.session_state['status_text'] = None
    if 'time_text' not in st.session_state:
        st.session_state['time_text'] = None
    if 'last_pdf_path' not in st.session_state:
        st.session_state['last_pdf_path'] = None

    # Sidebar
    with st.sidebar:
        st.title("System Information")
        cpu_info, ram_info, gpu_info = get_system_info()
        st.info(f"{cpu_info}\n{ram_info}\n{gpu_info}")

        st.title("Instructions")
        st.markdown("""
        ### How to Use:
        1. **Select Input**: Choose sample PDF or upload your own
        2. **Generate**: Click 'Generate Podcast' button
        3. **Monitor**: Watch real-time progress
        4. **Review**: Check the transcript
        5. **Listen**: Play your generated podcast
        ### Tips:
        - Ensure stable internet connection
        - Keep the browser tab active
        - For large PDFs, process may take longer
        - GPU acceleration is used when available
        - Use Stop button to cancel processing
        """)

    # Main content
    input_col, button_col = st.columns([3, 1])

    with input_col:
        pdf_path = None
        use_sample = st.checkbox("Use sample PDF (llm.pdf)", value=True)
        if use_sample:
            pdf_path = str(Path("E:/Projects/NoteBookLlama-(GPU)Final/resources/llm.pdf"))
            if st.session_state.get('last_pdf_path') != pdf_path:
                st.session_state['transcript'] = None
                st.session_state['audio_path'] = None
                st.session_state['last_pdf_path'] = pdf_path
                logger.debug("Cleared transcript and audio due to sample PDF selection")
        else:
            uploaded_file = st.file_uploader("Upload your PDF file", type=['pdf'])
            if uploaded_file:
                temp_pdf_path = "temp_upload.pdf"
                with open(temp_pdf_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                pdf_path = temp_pdf_path
                if st.session_state.get('last_pdf_path') != pdf_path or st.session_state.get('last_pdf_path') is None:
                    st.session_state['transcript'] = None
                    st.session_state['audio_path'] = None
                    st.session_state['last_pdf_path'] = pdf_path
                    logger.debug("Cleared transcript and audio due to new file upload")

    with button_col:
        col1, col2 = st.columns(2)
        with col1:
            start_button = st.button(
                "🚀 Generate",
                type="primary",
                disabled=st.session_state.get('pipeline_running', False)
            )
        with col2:
            if st.session_state.get('pipeline_running', False):
                if st.button("🛑 Stop", type="secondary"):
                    st.session_state['stop_requested'] = True
                    st.warning("Stopping process...")

    # Output tabs
    transcript_tab, audio_tab = st.tabs(["📝 Transcript", "🎧 Audio"])

    with transcript_tab:
        if st.session_state.get('transcript'):
            st.markdown("### Generated Transcript")
            formatted_transcript = format_transcript(st.session_state['transcript'])
            st.text_area("Preview", value=formatted_transcript, height=300, key="transcript_area")
            logger.debug("Transcript displayed in UI")
        else:
            st.info("No transcript available yet. Run the pipeline to generate one.")
            logger.debug("No transcript in session state")

    with audio_tab:
        if st.session_state.get('audio_path') and os.path.exists(st.session_state['audio_path']):
            st.markdown("### Generated Podcast")
            st.audio(str(st.session_state['audio_path']))
            with open(st.session_state['audio_path'], 'rb') as f:
                st.download_button(
                    label="Download Podcast",
                    data=f.read(),
                    file_name="generated_podcast.wav",
                    mime="audio/wav"
                )
            logger.debug(f"Audio file displayed and downloadable: {st.session_state['audio_path']}")
        else:
            st.info("No podcast audio available yet. Run the pipeline to generate one.")
            logger.debug("No audio path in session state or file does not exist")

    if start_button and pdf_path:
        st.session_state['pipeline_running'] = True
        st.session_state['stop_requested'] = False
        st.session_state['transcript'] = None
        st.session_state['audio_path'] = None
        logger.debug("Cleared transcript and audio at pipeline start")

        try:
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.session_state['progress_bar'] = st.progress(0)
                st.session_state['status_text'] = st.empty()
                st.session_state['time_text'] = st.empty()

                pipeline = PodcastPipeline()
                if not use_sample:
                    pipeline.pdf_path = Path(pdf_path)

                with st.spinner('Processing...'):
                    elapsed_time = pipeline.run_pipeline()

                    # Update session state with transcript
                    if os.path.exists(pipeline.processed_transcript_file):
                        with open(pipeline.processed_transcript_file, 'rb') as f:
                            st.session_state['transcript'] = pickle.load(f)
                        logger.debug(f"Loaded transcript into session state: {pipeline.processed_transcript_file}")
                    else:
                        logger.error(f"Transcript file not found: {pipeline.processed_transcript_file}")
                        st.error("Failed to load transcript file.")

                    # Update session state with audio path
                    if os.path.exists(pipeline.podcast_file):
                        st.session_state['audio_path'] = str(pipeline.podcast_file)
                        logger.debug(f"Set audio path in session state: {pipeline.podcast_file}")
                    else:
                        logger.error(f"Podcast file not found: {pipeline.podcast_file}")
                        st.error("Failed to load podcast audio file.")

                    st.success(f"✨ Podcast generation completed in {elapsed_time/60:.1f} minutes!")
                    st.rerun()  # Force UI refresh to display transcript and audio

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logger.exception("Pipeline error")
        finally:
            if not use_sample and os.path.exists("temp_upload.pdf"):
                os.remove("temp_upload.pdf")
            st.session_state['pipeline_running'] = False
            logger.debug("Pipeline execution completed")

if __name__ == "__main__":
    main()