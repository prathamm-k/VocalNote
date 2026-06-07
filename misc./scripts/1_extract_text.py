#3 seconds

import PyPDF2
from typing import Optional
import os
import warnings

warnings.filterwarnings('ignore')
pdf_path = 'resources/test.pdf'

def validate_pdf(file_path: str) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found at path: {file_path}")
        return False
    if not file_path.lower().endswith('.pdf'):
        print("Error: File is not a PDF")
        return False
    return True

def extract_text_from_pdf(file_path: str, max_chars: int = 100000) -> Optional[str]:
    if not validate_pdf(file_path):
        return None

    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)

            num_pages = len(pdf_reader.pages)
            print(f"Processing PDF with {num_pages} pages...")

            extracted_text = []
            total_chars = 0

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                if total_chars + len(text) > max_chars:
                    remaining_chars = max_chars - total_chars
                    extracted_text.append(text[:remaining_chars])
                    print(f"Reached {max_chars} character limit at page {page_num + 1}")
                    break

                extracted_text.append(text)
                total_chars += len(text)
                print(f"Processed page {page_num + 1}/{num_pages}")

            final_text = '\n'.join(extracted_text)
            print(f"\nExtraction complete! Total characters: {len(final_text)}")
            return final_text

    except PyPDF2.PdfReadError:
        print("Error: Invalid or corrupted PDF file")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        return None

def get_pdf_metadata(file_path: str) -> Optional[dict]:
    if not validate_pdf(file_path):
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

print("Extracting metadata...")
metadata = get_pdf_metadata(pdf_path)
if metadata:
    print("\nPDF Metadata:")
    print(f"Number of pages: {metadata['num_pages']}")
    print("Document info:")
    for key, value in metadata['metadata'].items():
        print(f"{key}: {value}")

print("\nExtracting text...")
extracted_text = extract_text_from_pdf(pdf_path)

if extracted_text:
    print("\nPreview of extracted text (first 500 characters):")
    print("-" * 50)
    print(extracted_text[:500])
    print("-" * 50)
    print(f"\nTotal characters extracted: {len(extracted_text)}")

if extracted_text:
    output_file = './resources/extracted_text.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(extracted_text)
    print(f"\nExtracted text has been saved to {output_file}")