import sys
import getpass
from pathlib import Path
try:
    import pypdf
except ImportError:
    pypdf = None

class PDFLabManager:
    def __init__(self):
        if not pypdf:
            raise ImportError("pypdf is required for PDF Lab. Please install it with 'pip install pypdf'.")

    def get_info(self, file_path):
        """Returns metadata from a PDF file."""
        reader = pypdf.PdfReader(file_path)
        return reader.metadata

    def extract_text(self, file_path, page_start=None, page_end=None):
        """Extracts text from a PDF file."""
        reader = pypdf.PdfReader(file_path)
        text = []
        start = page_start if page_start is not None else 0
        end = page_end if page_end is not None else len(reader.pages)

        # Ensure indices are within bounds
        start = max(0, start)
        end = min(len(reader.pages), end)

        for i in range(start, end):
            page_text = reader.pages[i].extract_text()
            if page_text:
                text.append(page_text)
        return "\n".join(text)

    def merge_pdfs(self, output_path, input_paths):
        """Merges multiple PDF files into one."""
        writer = pypdf.PdfWriter()
        for path in input_paths:
            writer.append(path)
        writer.write(output_path)
        writer.close()

    def split_pdf(self, input_path, output_dir):
        """Splits a PDF into individual pages."""
        reader = pypdf.PdfReader(input_path)
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []
        for i, page in enumerate(reader.pages):
            writer = pypdf.PdfWriter()
            writer.add_page(page)
            output_filename = out_dir / f"page_{i+1}.pdf"
            with open(output_filename, "wb") as f:
                writer.write(f)
            generated_files.append(str(output_filename))
        return generated_files

    def encrypt(self, input_path, output_path, password):
        """Encrypts a PDF file with a password."""
        reader = pypdf.PdfReader(input_path)
        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(password)
        with open(output_path, "wb") as f:
            writer.write(f)
        writer.close()

    def decrypt(self, input_path, output_path, password):
        """Decrypts a PDF file with a password."""
        reader = pypdf.PdfReader(input_path)
        if not reader.is_encrypted:
            raise ValueError(f"PDF {input_path} is not encrypted.")
        if not reader.decrypt(password):
            raise ValueError(f"Incorrect password for PDF {input_path}.")

        writer = pypdf.PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        with open(output_path, "wb") as f:
            writer.write(f)
        writer.close()


def run_pdf_lab_logic(args):
    try:
        manager = PDFLabManager()
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

    try:
        if args.action == "info":
            info = manager.get_info(args.file)
            print(f"--- Metadata for {args.file} ---")
            if info:
                for k, v in info.items():
                    # cleanup key names if they start with /
                    key = k[1:] if k.startswith('/') else k
                    print(f"{key}: {v}")
            else:
                print("No metadata found.")

        elif args.action == "text":
            text = manager.extract_text(args.file, args.start, args.end)
            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"✅ Text extracted to {args.output}")
            else:
                print(text)

        elif args.action == "merge":
            manager.merge_pdfs(args.output, args.inputs)
            print(f"✅ Merged {len(args.inputs)} files to {args.output}")

        elif args.action == "split":
            files = manager.split_pdf(args.file, args.output_dir)
            print(f"✅ Split {args.file} into {len(files)} pages in '{args.output_dir}'")

        elif args.action == "encrypt":
            password = args.password
            if not password:
                password = getpass.getpass("Enter password for encryption: ")
            manager.encrypt(args.file, args.output, password)
            print(f"✅ Encrypted {args.file} to {args.output}")

        elif args.action == "decrypt":
            password = args.password
            if not password:
                password = getpass.getpass("Enter password for decryption: ")
            manager.decrypt(args.file, args.output, password)
            print(f"✅ Decrypted {args.file} to {args.output}")

        return True

    except Exception as e:
        print(f"❌ Error during PDF operation: {e}", file=sys.stderr)
        return False
