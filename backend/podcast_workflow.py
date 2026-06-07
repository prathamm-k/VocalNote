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
import tempfile

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class PodcastPipeline:
    def __init__(self):
        self.base_dir = Path(tempfile.gettempdir())
        self.pdf_path = self.base_dir / "llm.pdf"
        self.extracted_text_file = self.base_dir / "extracted_text.txt"
        self.clean_extracted_text_file = self.base_dir / "clean_extracted_text.txt"
        self.raw_transcript_file = self.base_dir / "raw_transcript.pkl"
        self.processed_transcript_file = self.base_dir / "processed_transcript.pkl"
        self.podcast_file = self.base_dir / "podcast.wav"
        self.model_path_preprocess = Path("models") / "Qwen3-1.7B-Q8_0.gguf"
        self.model_path_transcript = Path("models") / "qwen2.5-3b-instruct-q4_k_m.gguf"
        
        # Hardware Auto-detection & Threading Optimization
        self.detect_device()
        
        # Cache for LLM and TTS model instances
        self.llm_preprocess = None
        self.llm_transcript = None
        self.kpipeline = None

    def detect_device(self):
        import platform
        import subprocess
        
        # Default CPU fallback
        self.device = "cpu"
        self.n_gpu_layers = 0
        
        # Optimal CPU thread detection (4 for Apple Silicon, otherwise half of logical cores)
        try:
            self.n_threads = 4
            if platform.system() != "Darwin":
                import os
                self.n_threads = max(1, os.cpu_count() // 2)
        except Exception:
            self.n_threads = 4

        if platform.system() == "Darwin":
            machine = platform.machine()
            processor = platform.processor()
            is_apple_silicon = (machine == "arm64" or processor == "arm")
            if not is_apple_silicon:
                try:
                    brand = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"]).decode("utf-8")
                    if "Apple" in brand:
                        is_apple_silicon = True
                except Exception:
                    pass
            
            if is_apple_silicon and torch.backends.mps.is_available():
                print("Detected Apple Silicon (arm64). Enabling Metal & MPS acceleration.")
                self.device = "mps"
                self.n_gpu_layers = -1
            else:
                print("Detected macOS on Intel, or MPS is unavailable. Falling back to CPU only.")
        else:
            print("Detected non-macOS hardware. Falling back to CPU only.")



################################################################################################################
################################################################################################################
################################################################################################################



    def validate_pdf(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            print(f"Error: File not found at path: {file_path}")
            return False
        if not str(file_path).lower().endswith('.pdf'):
            print("Error: File is not a PDF")
            return False
        return True

    def extract_text_from_pdf(self, file_path: str, max_chars: int = 100000) -> Optional[str]:
        if not self.validate_pdf(file_path):
            return None

        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                print(f"\nProcessing PDF with {num_pages} pages...\n")

                extracted_text = []
                total_chars = 0

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()

                    if total_chars + len(text) > max_chars:
                        remaining_chars = max_chars - total_chars
                        extracted_text.append(text[:remaining_chars])
                        #print(f"Reached {max_chars} character limit at page {page_num + 1}")
                        break

                    extracted_text.append(text)
                    total_chars += len(text)
                    #print(f"Processed page {page_num + 1}/{num_pages}")

                final_text = '\n'.join(extracted_text)
                #print(f"\nExtraction complete! Total characters: {len(final_text)}")
                return final_text
        except PyPDF2.PdfReadError:
            print("Error: Invalid or corrupted PDF file")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
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
            print(f"Error extracting metadata: {str(e)}")
            return None



###################################################################################################################
###################################################################################################################
###################################################################################################################



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
        print(f"PyTorch version: {torch.__version__}")
        print(f"Is CUDA available for PyTorch? {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"PyTorch CUDA version: {torch.version.cuda}")
            print(f"Number of GPUs PyTorch sees: {torch.cuda.device_count()}")
            if torch.cuda.device_count() > 0:
                print(f"Current GPU Model (PyTorch): {torch.cuda.get_device_name(0)}")

        n_ctx = 2048
        chunk_size = 3000
        max_tokens = 400
        n_batch = 512
        temperature = 0.7
        top_p = 0.8
        top_k = 20
        min_p = 0
        presence_penalty = 1.5

        if self.llm_preprocess is None:
            print(f"Loading preprocessing model ({self.model_path_preprocess}) with n_gpu_layers={self.n_gpu_layers} and n_threads={self.n_threads}...")
            self.llm_preprocess = Llama(
                model_path=str(self.model_path_preprocess),
                n_ctx=n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
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
        
        start_time = time.time()
        cleaned_chunks = []
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
            chunk_start = time.time()
            prompt = f"{SYSTEM_PROMPT}\n<|im_start|>user\n{self.clean_chunk_input(chunk)}\n/no_think\n<|im_end|>"

            try:
                response = self.llm_preprocess(
                    prompt,
                    max_tokens=max_tokens,
                    stop=["<|im_end|>"],
                    echo=False
                )
                output_text = response["choices"][0]["text"].strip()
                output_text = self.post_process_output(output_text)
                cleaned_chunks.append(output_text)
            except Exception as e:
                logger.error(f"Error at chunk {i+1}: {e}")
                continue

            chunk_time = time.time() - chunk_start
            if chunk_time > 3:
                logger.warning(f"Chunk {i+1} took {chunk_time:.2f}s, exceeding 3s target.")

        # Write all processed chunks to disk at once
        with open(self.clean_extracted_text_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(cleaned_chunks))

        processing_time = time.time() - start_time
        print(f"Time taken: {processing_time:.2f} seconds to process {len(chunks)} chunks\n")

        #print(f"Config: context_length={n_ctx}, chunk_size={chunk_size}, max_tokens={max_tokens}")



####################################################################################################################
####################################################################################################################
####################################################################################################################



    def count_tokens(self, text):
        return len(self.llm_transcript.tokenize(text.encode('utf-8')))

    def truncate_input(self, text, max_tokens):
        # Ensure model is loaded to tokenize/detokenize
        if self.llm_transcript is None:
            n_ctx = 16384
            print(f"Lazy loading transcript model for truncation check ({self.model_path_transcript})...")
            self.llm_transcript = Llama(
                model_path=str(self.model_path_transcript),
                n_ctx=n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                f16_kv=True,
                use_mlock=False,
                low_vram=True,
                seed=-1,
                logits_all=False,
                verbose=False
            )
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
            return None
        except FileNotFoundError:
            logger.error(f"File '{filename}' not found.")
            return None
        except IOError:
            logger.error(f"Could not read file '{filename}'.")
            return None

    def generate_transcript(self):
        n_ctx = 16384
        max_tokens = 4096
        n_batch = 512
        temperature = 1.0
        top_p = 0.8
        repeat_penalty = 1.1
        presence_penalty = 1.0
        top_k = 20
        min_p = 0
        max_input_tokens = 12000

        if self.llm_transcript is None:
            print(f"Loading transcript model ({self.model_path_transcript}) with n_gpu_layers={self.n_gpu_layers} and n_threads={self.n_threads}...")
            self.llm_transcript = Llama(
                model_path=str(self.model_path_transcript),
                n_ctx=n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
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

        SYSTEM_PROMPT = """<|im_start|>system
You are a world-class podcast writer, having ghostwritten for Joe Rogan, Lex Fridman, Ben Shapiro, and Tim Ferriss.
In an alternate universe, you write every line they say, streaming it directly to their brains.
You have won multiple podcast awards for your engaging scripts. Your task is to write a detailed,
word-by-word podcast transcript based on the provided text, formatted directly as a Python list of tuples for an AI Text-To-Speech Pipeline.

There should be only two people conversing (not one more or less) throughout the transcript.
There are only two speakers: Speaker 1 and Speaker 2.
- Speaker 1: Leads the conversation and teaches Speaker 2, giving incredible anecdotes, explanations, and analogies. He is a captivating teacher.
- Speaker 2: A curious listener, new to the topic, asking curious, exciting, or confused follow-up questions with real-world examples. He keeps the conversation on track.
Make sure the tangents Speaker 2 provides are interesting and wild, and include realistic nuances like interruptions.
Keep the text clean: the TTS engine cannot do "umms, hmms" well, so keep it straight text.
Start the podcast with a fun, catchy, and borderline clickbait welcome, and conclude with a memorable closing statement.

STRICTLY RETURN YOUR RESPONSE ONLY AS A PYTHON LIST OF TUPLES. Do not write anything before or after the list.
Do not include any markdown fences (such as ```python), titles, chapter headings, explanations, commentary, or any other content.
It must start directly with the list `[` and end with the list `]`.

Example of response format:
[
    ("Speaker 1", "Speaker 1 text here..."),
    ("Speaker 2", "Speaker 2 text here..."),
    ("Speaker 1", "Speaker 1 text here..."),
    ("Speaker 2", "Speaker 2 text here..."),
]
/no_think
<|im_end|>"""

        def format_prompt(system_prompt, user_input):
            return f"{system_prompt}\n<|im_start|>user\n{user_input}\n/no_think\n<|im_end|>\n<|im_start|>assistant\n"

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
            logger.error(f"Error during generation: {e}")
            raise

        # Clean any accidental markdown code fences around the list if the LLM outputted them
        output_text = re.sub(r"^```(?:python)?\s*", "", output_text, flags=re.IGNORECASE)
        output_text = re.sub(r"\s*```$", "", output_text, flags=re.IGNORECASE)
        output_text = output_text.strip()

        # Save to processed_transcript_file (which bypasses the rewrite step and is directly consumed by generate_podcast)
        self.processed_transcript_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.processed_transcript_file, 'wb') as file:
            pickle.dump(output_text, file)

        # Also write raw_transcript_file as legacy/compatibility
        with open(self.raw_transcript_file, 'wb') as file:
            pickle.dump(output_text, file)

        processing_time = time.time() - start_time
        print(f"Transcript generated and saved to: {self.processed_transcript_file}")
        print(f"Time taken: {processing_time:.2f} seconds\n")

    def rewrite_transcript(self):
        # Since we merge transcript generation and rewriting, this is now a no-op or reads processed transcript
        print("Skipping rewrite_transcript step as it was merged into generate_transcript.")
        # Ensure processed_transcript_file exists or copy raw_transcript_file to it
        if self.raw_transcript_file.exists() and not self.processed_transcript_file.exists():
            with open(self.raw_transcript_file, 'rb') as f:
                data = pickle.load(f)
            with open(self.processed_transcript_file, 'wb') as f:
                pickle.dump(data, f)

    def generate_kokoro_audio(self, text, voice):
        generator = self.kpipeline(text, voice=voice)
        audio_segments = []
        for _, _, audio in generator:
            audio_segments.append(audio)
        full_audio = np.concatenate(audio_segments)
        return full_audio, 24000

    def numpy_to_audio_segment(self, audio_arr, sampling_rate):
        audio_int16 = (audio_arr * 32767).astype(np.int16)
        byte_io = io.BytesIO()
        wavfile.write(byte_io, sampling_rate, audio_int16)
        byte_io.seek(0)
        return AudioSegment.from_wav(byte_io)

    def generate_podcast(self):
        if self.kpipeline is None:
            print(f"Loading Kokoro model on {self.device}...")
            self.kpipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M', device=self.device)

        with open(self.processed_transcript_file, 'rb') as f:
            PODCAST_TEXT = pickle.load(f)

        if isinstance(PODCAST_TEXT, str):
            try:
                import ast
                PODCAST_TEXT = ast.literal_eval(PODCAST_TEXT)
            except Exception as e:
                raise ValueError(f"Failed to parse PODCAST_TEXT string as list of tuples using ast.literal_eval: {e}")

        if not isinstance(PODCAST_TEXT, list):
            raise ValueError("PODCAST_TEXT must be a list of tuples after parsing")

        audio_segments = []
        print("Generating podcast audio segments...")
        for speaker, text in tqdm(PODCAST_TEXT, desc="Generating", unit="segment"):
            if not text.strip():
                continue

            voice = 'am_fenrir' if speaker == "Speaker 1" else 'bf_emma'
            audio_arr, rate = self.generate_kokoro_audio(text, voice=voice)
            audio_segments.append(audio_arr)

        if audio_segments:
            print("Concatenating audio segments directly in-memory...")
            full_audio = np.concatenate(audio_segments)
            audio_int16 = (full_audio * 32767).astype(np.int16)
            
            # Export to wav directly using scipy
            print(f"Exporting podcast wav to {self.podcast_file}...")
            wavfile.write(str(self.podcast_file), 24000, audio_int16)
            print("Podcast exported successfully.")
        else:
            print("No audio segments were generated.")

    def run_pipeline(self):
        metadata = self.get_pdf_metadata(self.pdf_path)
        if metadata:
            for key, value in metadata['metadata'].items():
                print(f"{key}: {value}")

        extracted_text = self.extract_text_from_pdf(self.pdf_path)
        if extracted_text:
            with open(self.extracted_text_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)

        print("\nStep 2: Preprocessing text...")
        self.preprocess_text()

        print("\nStep 3: Generating transcript (merged)...")
        self.generate_transcript()

        print("\nStep 4: Running legacy rewrite step (no-op)...")
        self.rewrite_transcript()

        print("\nStep 5: Generating podcast audio...")
        self.generate_podcast()

if __name__ == "__main__":
    start_time = time.time()
    pipeline = PodcastPipeline()
    pipeline.run_pipeline()
    minutes = (time.time() - start_time) / 60
    print(f"Time taken: {minutes:.2f} minutes to complete the pipeline")