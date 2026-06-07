#25-30 seconds

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
INPUT_FILE = BASE_DIR / "resources" / "raw_transcript.pkl"
PICKLE_FILE = BASE_DIR / "resources" / "processed_transcript.pkl"
MODEL_PATH = Path("models/Qwen3-1.7B-Q8_0.gguf")

n_ctx = 16384  # Context length
max_tokens = 8126  # Output token limit
n_batch = 256  # Batch size for processing
n_threads = 8  # Number of threads for processing, adjust based on your CPU
n_gpu_layers = -1  # Balance GPU/CPU load
temperature = 0.01  # model creativity, lower for more deterministic output
top_p = 0.85  # Controls diversity of output, lower values make output more focused
repeat_penalty = 1.1  # Avoid repetition
frequency_penalty = 0.1  # Penalty for new tokens based on their frequency in the text, higher values discourage repetition

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
    stream=False,
    verbose=False
)

SYSTEM_PROMPT ="""
You are an international oscar winnning screenwriter. You have been working with multiple award winning podcasters.
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
    return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_input}<|im_end|>\n/no_think\n<|im_start|>assistant\n<think>\n</think>\n"

with open(INPUT_FILE, 'rb') as file:
    INPUT_PROMPT = pickle.load(file)

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
    logger.error(f"Error during generation: {e}")
    raise

with open(PICKLE_FILE, 'wb') as file:
    pickle.dump(output_text, file)

processing_time = time.time() - start_time
print(f"\nTranscript generated and saved to: {PICKLE_FILE}")
print(f"Time taken: {processing_time:.2f} seconds")
print(f"Config: context_length={n_ctx}, max_tokens={max_tokens}")