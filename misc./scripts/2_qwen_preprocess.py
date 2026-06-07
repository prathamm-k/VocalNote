#300-330 seconds

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tqdm import tqdm
from pathlib import Path
import warnings
import time
import re
from llama_cpp import Llama
import torch

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

print(f"PyTorch version: {torch.__version__}")
print(f"Is CUDA available for PyTorch? {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"PyTorch CUDA version: {torch.version.cuda}")
    print(f"Number of GPUs PyTorch sees: {torch.cuda.device_count()}")
    if torch.cuda.device_count() > 0:
        print(f"Current GPU Model (PyTorch): {torch.cuda.get_device_name(0)}")

BASE_DIR = Path("E:/Projects/NoteBookLlama-(GPU)Final")
INPUT_FILE = BASE_DIR / "resources" / "extracted_text.txt"
OUTPUT_FILE = BASE_DIR / "resources" / "clean_extracted_text.txt"
MODEL_PATH = Path("models/Qwen3-1.7B-Q8_0.gguf")

n_ctx = 2048  #input context length
chunk_size = 1000  # input chunk size
max_tokens = 150  # Output token limit per chunk
n_threads = 4  # Number of threads for processing, adjust based on your CPU
n_batch = 512  # Batch size for processing
temperature = 0.7  # increase for more creative output, decrease for more deterministic output
top_p = 0.8  # controls diversity of output, lower values make output more focused
top_k = 20  # considers only the top k tokens for sampling, lower values make output more focused
min_p = 0  # Minimum probability for token selection, set to 0 for no minimum
presence_penalty = 1.5  # Penalty for new tokens based on their presence in the text, higher values discourage repetition

llm = Llama(
    model_path=str(MODEL_PATH),
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

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    raw_text = f.read()

def deduplicate_text(text):
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

raw_text = deduplicate_text(raw_text)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=1,
    separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
)
chunks = splitter.split_text(raw_text)

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("")

def clean_chunk_input(text):
    text = re.sub(r'https?://\S+|www\.\S+|\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'[^\x20-\x7E\n\r]', '', text)
    return text.strip()

def post_process_output(text):
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

start_time = time.time()

for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
    chunk_start = time.time()
    prompt = f"{SYSTEM_PROMPT}\n<|im_start|>user\n{clean_chunk_input(chunk)}\n/no_think\n<|im_end|>"

    try:
        response = llm(
            prompt,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            echo=False
        )
        output_text = response["choices"][0]["text"].strip()
        output_text = post_process_output(output_text)
    except Exception as e:
        logger.error(f"Error at chunk {i+1}: {e}")
        continue

    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(output_text)
        f.write("\n\n")

    chunk_time = time.time() - chunk_start
    if chunk_time > 3:
        logger.warning(f"Chunk {i+1} took {chunk_time:.2f}s, exceeding 3s target.")

minutes = (time.time() - start_time) / 60

print(f"\nAll chunks processed and saved to: {OUTPUT_FILE}")
print(f"Time taken: {minutes:.2f} minutes to process {len(chunks)} chunks")
print(f"Config: context_length={n_ctx}, chunk_size={chunk_size}, max_tokens={max_tokens}")