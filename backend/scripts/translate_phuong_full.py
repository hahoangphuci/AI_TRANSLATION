"""
Run full translation for the sample file uploads/phuong_orig.docx -> downloads/translated_phuong_orig.docx
Usage (PowerShell):
& "C:/Users/HA HOANG PHUC/AppData/Local/Programs/Python/Python313/python.exe" scripts/translate_phuong_full.py
"""
from app.services.translation_service import TranslationService
from docx import Document
from pathlib import Path

svc = TranslationService()
src = Path('uploads/phuong_orig.docx')
if not src.exists():
    print('Source file not found:', src)
    raise SystemExit(1)

print('Starting translation... this may take a few minutes depending on file size and API limits')
out = svc.translate_document(str(src), 'en')
print('Output path:', out)
print('Exists:', Path(out).exists())
try:
    d = Document(out)
    print('First paragraph preview:')
    print(d.paragraphs[0].text[:400])
except Exception as e:
    print('Could not open translated DOCX:', e)

print('Done')
