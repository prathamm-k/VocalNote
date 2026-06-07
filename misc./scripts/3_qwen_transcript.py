#180-200 seconds

import logging
import time
import pickle
from pathlib import Path
import warnings
from llama_cpp import Llama

warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BASE_DIR = Path("E:/Projects/NoteBookLlama-(GPU)Final")
INPUT_FILE = BASE_DIR / "resources" / "clean_extracted_text.txt"
PICKLE_FILE = BASE_DIR / "resources" / "raw_transcript.pkl"
MODEL_PATH = Path("models/qwen2.5-3b-instruct-q4_k_m.gguf") #(great balance between speed and quality)

n_ctx = 16384  # Context length
max_tokens = 1024  # Output token limit per chunk
n_batch = 512  # Batch size for processing
n_threads = 8  # Number of threads for processing, adjust based on your CPU
n_gpu_layers = -1  # Balance GPU/CPU load
temperature = 0.5  # Tighter for on-topic output
top_p = 0.8  # Controls diversity of output, lower values make output more focused
repeat_penalty = 1.1  # Avoid repetition
presence_penalty = 1.5  # Penalty for new tokens based on their presence in the text, higher values discourage repetition
top_k = 20  # Considers only the top k tokens for sampling, lower values make output more focused
min_p = 0  # Minimum probability for token selection, set to 0 for no minimum
max_input_tokens = 14000  # Limit input to fit n_ctx

llm = Llama(
    model_path=str(MODEL_PATH),
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

def count_tokens(text):
    """Estimate token count using model's tokenizer."""
    return len(llm.tokenize(text.encode('utf-8')))

def truncate_input(text, max_tokens):
    """Truncate input text to fit max_tokens."""
    tokens = llm.tokenize(text.encode('utf-8'))
    if len(tokens) > max_tokens:
        truncated = llm.detokenize(tokens[:max_tokens]).decode('utf-8', errors='ignore')
        logger.info(f"Truncated input from {len(tokens)} to {max_tokens} tokens")
        return truncated
    return text

def format_prompt(system_prompt, user_input):
    return f"{system_prompt}\n<|im_start|>user\n{user_input}\n/no_think\n<|im_end|>\n<|im_start|>assistant\n"

def read_file_to_string(filename):
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

INPUT_PROMPT = read_file_to_string(INPUT_FILE)
if INPUT_PROMPT is None:
    raise FileNotFoundError(f"Input file could not be read: {INPUT_FILE}")

INPUT_PROMPT = truncate_input(INPUT_PROMPT, max_input_tokens)

prompt = format_prompt(SYSTEM_PROMPT, INPUT_PROMPT)

total_tokens = count_tokens(prompt) + max_tokens
if total_tokens > n_ctx:
    raise ValueError(f"Total tokens ({total_tokens}) exceed context window ({n_ctx})")

start_time = time.time()
try:
    response = llm(
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

PICKLE_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(PICKLE_FILE, 'wb') as file:
    pickle.dump(output_text, file)

processing_time = time.time() - start_time
print(f"\nTranscript generated and saved to: {PICKLE_FILE}")
print(f"Time taken: {processing_time:.2f} seconds")
print(f"Config: context_length={n_ctx}, max_tokens={max_tokens}")