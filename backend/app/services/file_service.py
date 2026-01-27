import os
import re
import unicodedata
import PyPDF2
import docx
import openpyxl
# fpdf is optional; if missing we fallback to text output for PDFs
try:
    from fpdf import FPDF
    HAS_FPDF = True
except Exception:
    FPDF = None
    HAS_FPDF = False
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self, translator=None):
        """translator: callable(text, source_lang, target_lang) -> translated_text"""
        self.upload_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
        self.download_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'downloads')
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.download_folder, exist_ok=True)
        self.translator = translator
    
    def process_document(self, file_path, target_lang, progress_callback=None):
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        if ext.lower() == '.pdf':
            return self._process_pdf(file_path, target_lang, progress_callback)
        elif ext.lower() == '.docx':
            return self._process_docx(file_path, target_lang, progress_callback)
        elif ext.lower() == '.xlsx':
            return self._process_xlsx(file_path, target_lang, progress_callback)
        elif ext.lower() == '.txt':
            return self._process_txt(file_path, target_lang, progress_callback)
        else:
            raise ValueError("Unsupported file type")
    
    def _process_pdf(self, file_path, target_lang, progress_callback=None):
        text = ""
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            total_pages = len(pdf_reader.pages)
            for i, page in enumerate(pdf_reader.pages):
                text += page.extract_text() + "\n"
                if progress_callback:
                    progress_callback(int(5 + (i / max(1, total_pages)) * 20), f"Extracting page {i+1}/{total_pages}")
        
            if progress_callback:
                progress_callback(25, "Translating PDF text...")
            translated_text = self._translate_text(text, target_lang)

        # If FPDF is available, build a PDF; otherwise fallback to a TXT file (no layout preservation)
        if HAS_FPDF and FPDF:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            # Split text into lines to fit page
            lines = translated_text.split('\n')
            for line in lines:
                # Handle long lines
                while len(line) > 0:
                    if pdf.get_string_width(line) < 180:  # Approximate page width
                        pdf.cell(0, 10, txt=line, ln=True)
                        break
                    else:
                        # Find a good break point
                        words = line.split()
                        current_line = ""
                        for word in words:
                            if pdf.get_string_width(current_line + " " + word) < 180:
                                current_line += " " + word if current_line else word
                            else:
                                pdf.cell(0, 10, txt=current_line, ln=True)
                                current_line = word
                        if current_line:
                            pdf.cell(0, 10, txt=current_line, ln=True)
                        line = ""

            # Ensure output filename has .pdf extension
            output_filename = f"translated_{os.path.basename(file_path)}"
            if not output_filename.lower().endswith('.pdf'):
                output_filename += '.pdf'
            output_path = os.path.join(self.download_folder, output_filename)
            pdf.output(output_path)
        else:
            # Fallback: save plain text and include a note
            if progress_callback:
                progress_callback(60, "PDF library not available, writing plain text fallback")
            output_filename = f"translated_{os.path.basename(file_path)}"
            if not output_filename.lower().endswith('.txt'):
                output_filename += '.txt'
            output_path = os.path.join(self.download_folder, output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("NOTE: PDF rebuild not available on this system. Install 'fpdf' to get translated PDF output.\n\n")
                f.write(translated_text)

        if progress_callback:
            progress_callback(100, "Completed")
        return output_path
    
    def _process_docx(self, file_path, target_lang, progress_callback=None):
        # Modify original document in-place so styles/images/relationships are preserved
        doc = docx.Document(file_path)

        def distribute_text_to_runs(translated: str, runs_texts):
            """
            Heuristic: keep the same run count/styles by distributing the translated
            paragraph text back into existing runs proportionally by original run length.
            """
            if translated is None:
                translated = ""
            translated = str(translated)

            # Only consider runs that had some text (including whitespace) for distribution
            lengths = [len(t) for t in runs_texts]
            total = sum(lengths)
            if total <= 0:
                # If all runs are empty, put everything into the first run
                return [translated] + [""] * (len(runs_texts) - 1)

            # Initial proportional allocation
            alloc = []
            used = 0
            for i, ln in enumerate(lengths):
                if i == len(lengths) - 1:
                    take = len(translated) - used
                else:
                    take = int(round((ln / total) * len(translated)))
                    take = max(0, min(take, len(translated) - used))
                alloc.append(translated[used : used + take])
                used += take

            # Fix rounding drift
            if used < len(translated):
                alloc[-1] += translated[used:]
            elif used > len(translated):
                # Trim from the end if we overshot
                overflow = used - len(translated)
                if overflow > 0 and alloc[-1]:
                    alloc[-1] = alloc[-1][:-overflow]

            # Ensure same length
            if len(alloc) < len(runs_texts):
                alloc.extend([""] * (len(runs_texts) - len(alloc)))
            return alloc[: len(runs_texts)]

        def translate_paragraph_runs(paragraph, idx=None, total=None):
            # Translate at paragraph-level for better quality, then map back to runs to keep formatting.
            runs = list(paragraph.runs)
            if not runs:
                return

            original_texts = [r.text or "" for r in runs]
            paragraph_text = "".join(original_texts)
            if not paragraph_text.strip():
                return

            try:
                translated_para = self._translate_text(paragraph_text, target_lang)
            except Exception as e:
                print(f"Translator failed for paragraph: {e}")
                translated_para = paragraph_text

            pieces = distribute_text_to_runs(translated_para, original_texts)
            for run, piece in zip(runs, pieces):
                run.text = piece
            if progress_callback and idx is not None and total is not None:
                progress_callback(10 + int((idx / total) * 70), f"Translating paragraph {idx+1}/{total}")

        # Body paragraphs
        paragraphs = [p for p in doc.paragraphs]
        total = len(paragraphs) if paragraphs else 1
        for idx, para in enumerate(paragraphs):
            translate_paragraph_runs(para, idx, total)

        # Tables: translate cell-by-cell, preserve cell formatting
        for table in doc.tables:
            for r in range(len(table.rows)):
                for c in range(len(table.columns)):
                    cell = table.rows[r].cells[c]
                    for p_idx, p in enumerate(cell.paragraphs):
                        translate_paragraph_runs(p, p_idx, len(cell.paragraphs))

        # Headers and footers
        try:
            for section in doc.sections:
                header = section.header
                for p_idx, p in enumerate(header.paragraphs):
                    translate_paragraph_runs(p, p_idx, len(header.paragraphs))
                footer = section.footer
                for p_idx, p in enumerate(footer.paragraphs):
                    translate_paragraph_runs(p, p_idx, len(footer.paragraphs))
        except Exception:
            # ignore headers/footers issues
            pass

        # Ensure output filename has .docx extension
        output_filename = f"translated_{os.path.basename(file_path)}"
        if not output_filename.lower().endswith('.docx'):
            output_filename += '.docx'
        output_path = os.path.join(self.download_folder, output_filename)

        # Save and validate
        doc.save(output_path)


        # Validate produced DOCX — if invalid, write a plain text fallback to avoid corrupt file being returned
        try:
            # Try opening the saved file with python-docx to validate
            docx.Document(output_path)
        except Exception as e:
            # Create a text fallback containing translated paragraphs and table text
            if progress_callback:
                progress_callback(95, "DOCX validation failed, writing fallback text file")
            fallback_filename = output_filename
            if not fallback_filename.lower().endswith('.txt'):
                fallback_filename += '.txt'
            fallback_path = os.path.join(self.download_folder, fallback_filename)
            # Collect text from doc
            lines = []
            for p in doc.paragraphs:
                lines.append(p.text)
            for t in doc.tables:
                for row in t.rows:
                    for cell in row.cells:
                        lines.append(cell.text)
            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write("NOTE: DOCX creation failed on server. Showing plain text fallback below.\n\n")
                f.write('\n'.join(lines))
            output_path = fallback_path

        if progress_callback:
            progress_callback(100, "Completed")
        return output_path
    
    def _process_xlsx(self, file_path, target_lang, progress_callback=None):
        # Translate in-place to preserve styles, merged cells, formulas, column widths, etc.
        wb = openpyxl.load_workbook(file_path)

        # Count total cells (rough progress)
        total_cells = 0
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for _ in ws.iter_rows():
                total_cells += 1
        total_cells = total_cells or 1

        processed = 0
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for row in ws.iter_rows():
                for cell in row:
                    # Keep formulas intact (cell.data_type == 'f' or string startswith '=')
                    try:
                        is_formula = (cell.data_type == 'f') or (
                            isinstance(cell.value, str) and cell.value.startswith("=")
                        )
                    except Exception:
                        is_formula = False

                    if (not is_formula) and isinstance(cell.value, str) and cell.value.strip():
                        cell.value = self._translate_text(cell.value, target_lang)

                    processed += 1
                    if progress_callback:
                        progress_callback(
                            10 + int((processed / total_cells) * 80),
                            f"Translating cells {processed}/{total_cells}",
                        )

        # Ensure output filename has .xlsx extension
        output_filename = f"translated_{os.path.basename(file_path)}"
        if not output_filename.lower().endswith('.xlsx'):
            output_filename += '.xlsx'
        output_path = os.path.join(self.download_folder, output_filename)
        wb.save(output_path)
        if progress_callback:
            progress_callback(100, "Completed")
        return output_path
    
    def _process_txt(self, file_path, target_lang, progress_callback=None):
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        if progress_callback:
            progress_callback(25, "Translating text file...")
        translated_text = self._translate_text(text, target_lang)
        output_filename = f"translated_{os.path.basename(file_path)}"
        if not output_filename.lower().endswith('.txt'):
            output_filename += '.txt'
        output_path = os.path.join(self.download_folder, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        if progress_callback:
            progress_callback(100, "Completed")
        return output_path
    
    def _sanitize_text(self, text: str) -> str:
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception:
                return ''
        # Normalize unicode and remove control characters that break XML/docx
        text = unicodedata.normalize('NFC', text)
        # Remove C0 control characters except tab/newline/carriage return
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
        # Collapse weird zero-width/formatting if any
        text = re.sub(r'[\u200B-\u200F\u2028\u2029]', ' ', text)
        return text

    def _translate_text(self, text, target_lang):
        # Use injected translator; propagate errors so caller can report properly.
        if self.translator:
            out = self.translator(text, 'auto', target_lang)
            return self._sanitize_text(out)
        raise RuntimeError("Translator is not configured")