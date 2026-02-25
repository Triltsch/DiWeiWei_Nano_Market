from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import pdfplumber


def extract_pdf_text(pdf_path: Path) -> Optional[str]:
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            text = ""
            for page_num, page in enumerate(pdf.pages):
                text += f"=== PAGE {page_num + 1} ===\n"
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text
                text += "\n\n"
            return text
    except FileNotFoundError:
        print(f"Error: The PDF file was not found at '{pdf_path}'.")
    except PermissionError:
        print(f"Error: Permission denied when trying to open the PDF file at '{pdf_path}'.")
    except Exception as exc:
        print(f"Error: Failed to read or parse the PDF file at '{pdf_path}': {exc}")

    return None


def write_output(text: str, output_path: Path) -> bool:
    if not output_path.parent.exists():
        print(f"Error: The directory for the output path does not exist: '{output_path.parent}'.")
        return False

    try:
        with output_path.open("w", encoding="utf-8") as output_file:
            output_file.write(text)
    except FileNotFoundError:
        print(f"Error: The output path does not exist: '{output_path}'.")
        return False
    except PermissionError:
        print(f"Error: Permission denied when trying to write to '{output_path}'.")
        return False
    except OSError as exc:
        print(f"Error: Failed to write the output file at '{output_path}': {exc}")
        return False

    print(f"PDF converted successfully to {output_path}")
    return True


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    default_pdf = base_dir / "doc" / "seed" / "SA2_70476607.pdf"
    default_output = base_dir / "doc" / "seed" / "SA2_70476607.txt"

    parser = argparse.ArgumentParser(description="Convert a PDF to a text file.")
    parser.add_argument("--pdf-path", type=Path, default=default_pdf)
    parser.add_argument("--output-path", type=Path, default=default_output)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    text = extract_pdf_text(args.pdf_path)
    if text is None:
        print("PDF conversion aborted due to previous errors.")
        return 1

    return 0 if write_output(text, args.output_path) else 1


if __name__ == "__main__":
    raise SystemExit(main())
