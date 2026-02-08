import openai
import deepl
import os
import threading
import uuid
import time
import re
from dotenv import load_dotenv
from app.services.file_service import FileService, ProviderRateLimitError
from deep_translator import MyMemoryTranslator, GoogleTranslator
import requests
import urllib.parse

# Load .env từ thư mục backend (app/services -> app -> backend)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# override=True so changes to backend/.env take effect even if variables exist in OS env
load_dotenv(os.path.join(_backend_dir, '.env'), override=True)

# Bản đồ mã ISO 639-1 sang mã ngôn ngữ đích của DeepL (chỉ các ngôn ngữ DeepL hỗ trợ)
# Nguồn: https://developers.deepl.com/docs/resources/supported-languages
DEEPL_TARGET_MAP = {
    'ar': 'AR', 'bg': 'BG', 'cs': 'CS', 'da': 'DA', 'de': 'DE', 'el': 'EL',
    'en': 'EN-US', 'en-us': 'EN-US', 'en-gb': 'EN-GB',
    'es': 'ES', 'et': 'ET', 'fi': 'FI', 'fr': 'FR',
    'he': 'HE', 'iw': 'HE',  # iw là mã cũ của Hebrew
    'hu': 'HU', 'id': 'ID', 'it': 'IT', 'ja': 'JA', 'ko': 'KO',
    'lt': 'LT', 'lv': 'LV', 'nb': 'NB', 'no': 'NB',  # Norwegian -> Bokmål
    'nl': 'NL', 'pl': 'PL',
    'pt': 'PT-BR', 'pt-br': 'PT-BR', 'pt-pt': 'PT-PT',
    'ro': 'RO', 'ru': 'RU', 'sk': 'SK', 'sl': 'SL', 'sv': 'SV',
    'th': 'TH', 'tr': 'TR', 'uk': 'UK', 'vi': 'VI',
    'zh': 'ZH', 'zh-cn': 'ZH', 'zh-hans': 'ZH', 'zh-tw': 'ZH-HANT', 'zh-hant': 'ZH-HANT',
}

# Tên ngôn ngữ cho prompt OpenAI (các ngôn ngữ DeepL không hỗ trợ dùng OpenAI)
# Giúp model hiểu rõ hơn so với chỉ dùng mã (vd: "Thai" thay vì "th")
CODE_TO_NAME = {
    'af': 'Afrikaans', 'sq': 'Albanian', 'am': 'Amharic', 'ar': 'Arabic',
    'hy': 'Armenian', 'az': 'Azerbaijani', 'eu': 'Basque', 'be': 'Belarusian',
    'bn': 'Bengali', 'bs': 'Bosnian', 'bg': 'Bulgarian', 'ca': 'Catalan',
    'zh': 'Chinese (Simplified)', 'zh-cn': 'Chinese (Simplified)', 'zh-hans': 'Chinese (Simplified)',
    'zh-tw': 'Chinese (Traditional)', 'zh-hant': 'Chinese (Traditional)',
    'hr': 'Croatian', 'cs': 'Czech', 'da': 'Danish', 'nl': 'Dutch',
    'en': 'English', 'et': 'Estonian', 'fi': 'Finnish', 'fr': 'French',
    'de': 'German', 'el': 'Greek', 'he': 'Hebrew', 'iw': 'Hebrew',
    'hi': 'Hindi', 'hu': 'Hungarian', 'id': 'Indonesian', 'it': 'Italian',
    'ja': 'Japanese', 'ko': 'Korean', 'lv': 'Latvian', 'lt': 'Lithuanian',
    'ms': 'Malay', 'no': 'Norwegian', 'nb': 'Norwegian Bokmål',
    'fa': 'Persian', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian',
    'ru': 'Russian', 'sr': 'Serbian', 'sk': 'Slovak', 'sl': 'Slovenian',
    'es': 'Spanish', 'sw': 'Swahili', 'sv': 'Swedish', 'th': 'Thai',
    'tr': 'Turkish', 'uk': 'Ukrainian', 'ur': 'Urdu', 'vi': 'Vietnamese',
    'gu': 'Gujarati', 'kn': 'Kannada', 'ml': 'Malayalam',
    'mr': 'Marathi', 'ta': 'Tamil', 'te': 'Telugu', 'pa': 'Punjabi', 'ne': 'Nepali',
    'my': 'Myanmar (Burmese)', 'km': 'Khmer', 'lo': 'Lao', 'tl': 'Filipino',
}

class TranslationService:
    def __init__(self):
        def _sanitize_key(val):
            if not val:
                return None
            v = val.strip()
            # Strip wrapping quotes if user put OPENAI_API_KEY="..." in .env
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1].strip()
            # Treat obvious placeholders or very-short values as absent
            if v.lower().startswith('your-') or v.lower() in ('changeme', 'replace-me', '') or len(v) < 20:
                return None
            return v

        openai_key = _sanitize_key(os.getenv('OPENAI_API_KEY'))
        deepl_key = _sanitize_key(os.getenv('DEEPL_API_KEY'))
        openrouter_key = _sanitize_key(os.getenv('OPENROUTER_API_KEY'))
        # Debug: show which keys are present (do not print values). placeholders are ignored.
        print(f"TranslationService keys - DEEPL: {bool(deepl_key)}, OPENAI: {bool(openai_key)}, OPENROUTER: {bool(openrouter_key)}")
        self.deepl_translator = deepl.Translator(deepl_key) if deepl_key else None
        
        # Initialize OpenAI client for direct OpenAI or OpenRouter
        if openrouter_key:
            extra = {}
            ref = os.getenv('AI_HEADER_HTTP_REFERER') or os.getenv('HTTP_REFERER')
            if ref:
                extra["default_headers"] = {"Referer": ref.strip()}
            self.openai_client = openai.OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                **extra
            )
        elif openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
        else:
            self.openai_client = None
            
        # Pass translator callback into FileService so document processing can call
        # Provide FileService both translation and OCR hooks (used for DOCX embedded images)
        self.file_service = FileService(
            translator=self.translate_text,
            ocr_image_to_text=self.ocr_image_to_text,
            ocr_translate_overlay=self.ocr_translate_overlay,
        )
        # Simple in-memory job store for background document processing
        self.jobs = {}  # job_id -> {status, progress, message, download_path, error}
    
    def _openai_translate(self, text, source_lang, target_lang, target_code):
        """Dịch bằng OpenAI/OpenRouter. Dùng cho mọi ngôn ngữ (kể cả DeepL không hỗ trợ)."""
        if not self.openai_client:
            return None
        target_name = CODE_TO_NAME.get(target_code, target_lang)
        model = os.getenv('AI_MODEL', 'gpt-3.5-turbo')
        system_prompt = f"You are a professional translator. Translate the following text to {target_name}. Only return the translated text, nothing else."
        if source_lang and source_lang != 'auto':
            src_name = CODE_TO_NAME.get(source_lang.lower(), source_lang)
            system_prompt = f"You are a professional translator. Translate the following text from {src_name} to {target_name}. Only return the translated text, nothing else."
        try:
            # Use a safe max_tokens to avoid exceeding account credit limits
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                max_tokens=2048,
                temperature=0
            )
            content = response.choices[0].message.content
            return (content or "").strip()
        except Exception as e:
            # Surface API errors with their message so the caller can detect credit or rate issues
            raise RuntimeError(f"AI translation failed: {e}") from e

    def translate_text(self, text, source_lang, target_lang):
        if target_lang is None or not str(target_lang).strip():
            raise ValueError("target_lang is required")
        if text is None:
            return ""
        target_lang = str(target_lang).strip()
        source = (str(source_lang).strip() if source_lang is not None else 'auto') or 'auto'
        t = target_lang.lower()
        s = source.lower()

        # Only use OpenAI/OpenRouter (ChatGPT gpt-4o) for translations — no public or DeepL fallbacks.
        if not self.openai_client:
            raise RuntimeError("AI provider not configured: set OPENAI_API_KEY or OPENROUTER_API_KEY in backend/.env")
        try:
            out = self._openai_translate(text, source, target_lang, t)
            if out is not None and out != "":
                return out
            else:
                raise RuntimeError("AI translation returned empty result")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"AI translation failed: {e}")
    
    def translate_document(self, file_path, target_lang):
        # Synchronous translation (kept for compatibility)
        return self.file_service.process_document(file_path, target_lang)

    def translate_html(self, html, source_lang, target_lang):
        """Translate an HTML string while preserving tags. We translate text nodes only."""
        try:
            from bs4 import BeautifulSoup
            from bs4.element import NavigableString
        except Exception as e:
            raise RuntimeError("BeautifulSoup is required for HTML translation. Install 'beautifulsoup4'.") from e

        soup = BeautifulSoup(html, "html.parser")
        # Collect text nodes to translate
        text_nodes = []
        for element in soup.find_all(string=True):
            parent_name = element.parent.name if element.parent else ''
            # Skip non-visible or script/style/code/pre content
            if parent_name in ('script', 'style', 'code', 'pre', 'noscript'):
                continue
            text = str(element).strip()
            if text:
                text_nodes.append(element)

        # Translate each text node individually (simple; can be optimized by batching)
        # IMPORTANT: preserve leading/trailing whitespace exactly to keep original formatting.
        for node in text_nodes:
            original = str(node)
            try:
                # Keep surrounding whitespace exactly as-is (including newlines)
                leading_ws = original[: len(original) - len(original.lstrip())]
                trailing_ws = original[len(original.rstrip()):]
                core = original[len(leading_ws): len(original) - len(trailing_ws)]

                # If core is empty after trimming, skip translation
                if not core or not core.strip():
                    continue

                translated_core = self.translate_text(core, source_lang, target_lang)
                # Do NOT collapse whitespace. Only trim accidental outer spaces/newlines.
                translated_core = (translated_core or "").strip()

                # Replace the node content with translated text (preserving tags)
                node.replace_with(f"{leading_ws}{translated_core}{trailing_ws}")
            except Exception as e:
                # On failure, keep original text to avoid corrupting HTML
                print(f"HTML node translation failed, keeping original: {e}")
                continue

        return str(soup)

    def ocr_image_to_text(self, image_path, ocr_langs=None):
        """Extract text from an image using Tesseract OCR.

        Requirements:
        - pip: Pillow, pytesseract
        - system: tesseract-ocr binary available on PATH, or provide TESSERACT_CMD in backend/.env
        """
        try:
            from PIL import Image
        except Exception as e:
            raise RuntimeError("Pillow is required for OCR. Install 'Pillow'.") from e

        try:
            import pytesseract
        except Exception as e:
            raise RuntimeError("pytesseract is required for OCR. Install 'pytesseract'.") from e

        import shutil

        def _resolve_tesseract_cmd():
            env_cmd = os.getenv('TESSERACT_CMD')
            if env_cmd and str(env_cmd).strip():
                env_cmd = str(env_cmd).strip().strip('"')

            candidates = []
            if env_cmd:
                candidates.append(env_cmd)

            try:
                existing = getattr(pytesseract.pytesseract, 'tesseract_cmd', None)
                if existing and str(existing).strip():
                    candidates.append(str(existing).strip())
            except Exception:
                pass

            found_on_path = shutil.which('tesseract')
            if found_on_path:
                candidates.append(found_on_path)

            if os.name == 'nt':
                candidates.extend([
                    r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
                    r"C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe",
                    r"C:\\Tesseract-OCR\\tesseract.exe",
                ])

            for cand in candidates:
                if not cand:
                    continue
                cand = str(cand).strip().strip('"')
                if os.path.isabs(cand) or cand.lower().endswith('.exe'):
                    if os.path.exists(cand):
                        return cand
                else:
                    resolved = shutil.which(cand)
                    if resolved:
                        return resolved
            return None

        resolved_cmd = _resolve_tesseract_cmd()
        if resolved_cmd:
            pytesseract.pytesseract.tesseract_cmd = resolved_cmd
        else:
            raise RuntimeError(
                "OCR failed: tesseract is not installed or it's not in your PATH. "
                "Install Tesseract OCR, then either add it to PATH or set TESSERACT_CMD in backend/.env. "
                "Windows example: TESSERACT_CMD=C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
            )

        langs = (ocr_langs or os.getenv('OCR_LANGS_DEFAULT') or 'eng').strip()
        if not langs:
            langs = 'eng'

        try:
            img = Image.open(image_path)
            # Normalize to a mode that OCR handles well
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            text = pytesseract.image_to_string(img, lang=langs)
            return text or ""
        except Exception as e:
            raise RuntimeError(f"OCR failed: {e}") from e

    def ocr_translate_overlay(self, image_path, source_lang, target_lang, ocr_langs=None):
        """OCR an image, translate detected text, and render translated text back onto the image.

        Returns: (ocr_text, translated_text, png_bytes)

        Notes:
        - This is a best-effort overlay approach (beta). It replaces each detected line region
          with a light background and draws the translation over it.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
        except Exception as e:
            raise RuntimeError("Pillow is required for OCR. Install 'Pillow'.") from e

        try:
            import pytesseract
            from pytesseract import Output
        except Exception as e:
            raise RuntimeError("pytesseract is required for OCR. Install 'pytesseract'.") from e

        # Reuse existing resolver logic by calling ocr_image_to_text once to validate tesseract availability.
        # This also sets pytesseract.pytesseract.tesseract_cmd if needed.
        _ = self.ocr_image_to_text(image_path, ocr_langs=ocr_langs)

        langs = (ocr_langs or os.getenv('OCR_LANGS_DEFAULT') or 'eng').strip() or 'eng'

        img = Image.open(image_path)
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        original_rgba = img.convert('RGBA')
        base_img = original_rgba.copy()

        # OCR pass: use multi-PSM + upscale to catch small/header text,
        # but keep Tesseract's own line grouping to avoid merging many lines into one.
        def _run_ocr_lines(psm, pil_rgb, scale):
            config = f"--oem 3 --psm {int(psm)} -c preserve_interword_spaces=1"
            d = pytesseract.image_to_data(
                pil_rgb,
                lang=langs,
                config=config,
                output_type=Output.DICT,
            )
            n_ = len(d.get('text', []) or [])
            lines = {}
            for i in range(n_):
                word = (d['text'][i] or '').strip()
                if not word:
                    continue
                try:
                    conf = float(d.get('conf', [])[i]) if d.get('conf') else -1
                except Exception:
                    conf = -1

                left = int(d.get('left', [0])[i] or 0)
                top = int(d.get('top', [0])[i] or 0)
                width = int(d.get('width', [0])[i] or 0)
                height = int(d.get('height', [0])[i] or 0)
                right = left + width
                bottom = top + height

                if scale and scale != 1.0:
                    left = int(left / scale)
                    top = int(top / scale)
                    right = int(right / scale)
                    bottom = int(bottom / scale)

                key = (
                    int(d.get('block_num', [0])[i] or 0),
                    int(d.get('par_num', [0])[i] or 0),
                    int(d.get('line_num', [0])[i] or 0),
                )
                entry = lines.get(key)
                if not entry:
                    lines[key] = {
                        'tokens': [(word, conf)],
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom,
                    }
                else:
                    entry['tokens'].append((word, conf))
                    entry['left'] = min(entry['left'], left)
                    entry['top'] = min(entry['top'], top)
                    entry['right'] = max(entry['right'], right)
                    entry['bottom'] = max(entry['bottom'], bottom)

            out_lines = []
            for _, entry in lines.items():
                tokens = entry.get('tokens') or []
                # Prefer higher-confidence tokens for translation text, but keep bbox regardless.
                hi = [w for (w, c) in tokens if c == -1 or c >= 30]
                mid = [w for (w, c) in tokens if c == -1 or c >= 15]
                words_for_text = hi or mid
                text_line = ' '.join(words_for_text).strip()
                if not text_line:
                    continue
                confs = [c for (_, c) in tokens if c != -1]
                mean_conf = (sum(confs) / len(confs)) if confs else 100.0
                out_lines.append({
                    'text': text_line,
                    'left': int(entry['left']),
                    'top': int(entry['top']),
                    'right': int(entry['right']),
                    'bottom': int(entry['bottom']),
                    'mean_conf': float(mean_conf),
                })
            return out_lines

        # Upscale for OCR if the image is not huge (helps catch small text)
        ocr_rgb = original_rgba.convert('RGB')
        w0, h0 = ocr_rgb.size
        scale = 1.0
        try:
            if max(w0, h0) < 1600:
                scale = 2.0
                ocr_rgb = ocr_rgb.resize((int(w0 * scale), int(h0 * scale)), resample=Image.BICUBIC)
        except Exception:
            scale = 1.0

        candidates = []
        for psm in (6, 11):
            try:
                candidates.extend(_run_ocr_lines(psm, ocr_rgb, scale))
            except Exception:
                continue

        # Deduplicate overlapping lines between PSM passes (keep higher mean_conf)
        def _iou(a, b):
            ax1, ay1, ax2, ay2 = a
            bx1, by1, bx2, by2 = b
            ix1 = max(ax1, bx1)
            iy1 = max(ay1, by1)
            ix2 = min(ax2, bx2)
            iy2 = min(ay2, by2)
            iw = max(0, ix2 - ix1)
            ih = max(0, iy2 - iy1)
            inter = iw * ih
            if inter <= 0:
                return 0.0
            area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
            area_b = max(1, (bx2 - bx1) * (by2 - by1))
            return inter / float(area_a + area_b - inter)

        w_img, h_img = base_img.size
        filtered = []
        candidates.sort(key=lambda x: (-(x.get('mean_conf') or 0.0), x['top'], x['left']))
        for it in candidates:
            l, t, r, b = it['left'], it['top'], it['right'], it['bottom']
            # Quality gates: avoid "giant merged blocks" that will destroy the image.
            bw = max(1, r - l)
            bh = max(1, b - t)
            if bh > int(h_img * 0.22):
                continue
            if len(it.get('text', '')) > 220:
                continue
            if (it.get('mean_conf') or 0.0) < 18.0 and len(it.get('text', '')) > 18:
                continue

            bbox = (l, t, r, b)
            dup = False
            for keep in filtered:
                kb = (keep['left'], keep['top'], keep['right'], keep['bottom'])
                if _iou(bbox, kb) >= 0.72:
                    dup = True
                    break
            if not dup:
                filtered.append(it)

        # Sort top-to-bottom, then left-to-right
        line_items = sorted(filtered, key=lambda x: (x['top'], x['left']))

        def _pick_font(font_size):
            font_path = (os.getenv('OCR_FONT_PATH') or '').strip() or None
            candidates = []
            if font_path:
                candidates.append(font_path)
            if os.name == 'nt':
                candidates.extend([
                    r"C:\\Windows\\Fonts\\arial.ttf",
                    r"C:\\Windows\\Fonts\\segoeui.ttf",
                ])
            candidates.extend([
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            ])
            for p in candidates:
                try:
                    if p and os.path.exists(p):
                        return ImageFont.truetype(p, font_size)
                except Exception:
                    continue
            return ImageFont.load_default()

        def _measure(draw, font, text):
            try:
                box = draw.textbbox((0, 0), text, font=font)
                return (box[2] - box[0], box[3] - box[1])
            except Exception:
                try:
                    return draw.textsize(text, font=font)
                except Exception:
                    return (len(text) * font.size, font.size)

        def _fit_font(draw, text, max_w, max_h):
            size = max(10, int(max_h * 0.85))
            for s in range(size, 9, -2):
                font = _pick_font(s)
                w, h = _measure(draw, font, text)
                if w <= max_w and h <= max_h:
                    return font
            return _pick_font(10)

        draw = ImageDraw.Draw(base_img)
        ocr_lines = []
        translated_lines = []

        def _clamp(v, lo, hi):
            return max(lo, min(hi, v))

        def _sample_bg_color(img_rgba, l, t, r, b):
            """Sample background color around a text box.

            We sample a few pixels just outside the OCR box corners to approximate
            the surrounding background. This avoids painting white blocks on dark
            backgrounds.
            """
            try:
                w, h = img_rgba.size
                # sample points just outside the box
                pts = [
                    (_clamp(l - 2, 0, w - 1), _clamp(t - 2, 0, h - 1)),
                    (_clamp(r + 2, 0, w - 1), _clamp(t - 2, 0, h - 1)),
                    (_clamp(l - 2, 0, w - 1), _clamp(b + 2, 0, h - 1)),
                    (_clamp(r + 2, 0, w - 1), _clamp(b + 2, 0, h - 1)),
                ]
                cols = []
                for x, y in pts:
                    px = img_rgba.getpixel((x, y))
                    if isinstance(px, int):
                        cols.append((px, px, px))
                    else:
                        cols.append((int(px[0]), int(px[1]), int(px[2])))
                if not cols:
                    return (255, 255, 255)
                rr = sum(c[0] for c in cols) // len(cols)
                gg = sum(c[1] for c in cols) // len(cols)
                bb = sum(c[2] for c in cols) // len(cols)
                return (rr, gg, bb)
            except Exception:
                return (255, 255, 255)

        def _pick_text_colors(bg_rgb):
            # Choose text/stroke colors based on background luminance
            try:
                lum = (0.2126 * bg_rgb[0] + 0.7152 * bg_rgb[1] + 0.0722 * bg_rgb[2])
            except Exception:
                lum = 255
            if lum < 128:
                # dark bg -> light text with dark stroke
                return ((255, 255, 255, 255), (0, 0, 0, 255))
            # light bg -> dark text with light stroke
            return ((0, 0, 0, 255), (255, 255, 255, 255))
        def _wrap_text_to_width(draw_obj, font_obj, text, max_w):
            # Greedy wrap by spaces; if a single word is too long, keep it as-is.
            words = (text or '').split()
            if not words:
                return ['']
            lines_out = []
            cur = words[0]
            for w in words[1:]:
                cand = cur + ' ' + w
                cw, _ = _measure(draw_obj, font_obj, cand)
                if cw <= max_w:
                    cur = cand
                else:
                    lines_out.append(cur)
                    cur = w
            lines_out.append(cur)
            return lines_out

        def _fit_font_wrapped(draw_obj, text, max_w, max_h):
            # Find largest font where wrapped text fits within (max_w,max_h)
            size = max(10, int(max_h * 0.85))
            for s in range(size, 9, -2):
                font = _pick_font(s)
                lines_ = _wrap_text_to_width(draw_obj, font, text, max_w)
                # Measure total height
                widths = []
                heights = []
                for ln in lines_:
                    w, h = _measure(draw_obj, font, ln)
                    widths.append(w)
                    heights.append(h)
                total_h = (sum(heights) + max(0, (len(heights) - 1) * int(s * 0.18)))
                max_line_w = max(widths) if widths else 0
                if max_line_w <= max_w and total_h <= max_h:
                    return font, lines_, total_h
            font = _pick_font(10)
            lines_ = _wrap_text_to_width(draw_obj, font, text, max_w)
            # best-effort height
            heights = [_measure(draw_obj, font, ln)[1] for ln in lines_]
            total_h = (sum(heights) + max(0, (len(heights) - 1) * int(font.size * 0.18)))
            return font, lines_, total_h

        # 1) Remove original text as naturally as possible.
        # Prefer OpenCV inpainting (keeps background texture), fallback to soft rectangle fill.
        use_inpaint = False
        inpainted_rgb = None
        try:
            import numpy as np  # type: ignore
            import cv2  # type: ignore

            if line_items:
                w_img, h_img = base_img.size
                mask = np.zeros((h_img, w_img), dtype=np.uint8)
                # Larger pad helps avoid leaving edge artifacts (especially for the first/header line)
                for item in line_items:
                    ih = max(1, int(item['bottom']) - int(item['top']))
                    pad = max(8, int(ih * 0.35))
                    l = max(0, int(item['left']) - pad)
                    t = max(0, int(item['top']) - pad)
                    r = min(w_img, int(item['right']) + pad)
                    b = min(h_img, int(item['bottom']) + pad)
                    if r > l and b > t:
                        mask[t:b, l:r] = 255

                # Dilate mask slightly to cover anti-aliased edges
                try:
                    kernel = np.ones((3, 3), np.uint8)
                    mask = cv2.dilate(mask, kernel, iterations=1)
                except Exception:
                    pass

                # Convert to BGR for OpenCV
                rgb = np.array(original_rgba.convert('RGB'))
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                # Inpaint to fill text regions from surrounding pixels
                inpainted = cv2.inpaint(bgr, mask, 4, cv2.INPAINT_TELEA)
                inpainted_rgb = cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)
                use_inpaint = True
        except Exception:
            use_inpaint = False

        if use_inpaint and inpainted_rgb is not None:
            try:
                base_img = Image.fromarray(inpainted_rgb).convert('RGBA')
                draw = ImageDraw.Draw(base_img)
            except Exception:
                base_img = original_rgba.copy()
                draw = ImageDraw.Draw(base_img)

        for item in line_items:
            src_text = item['text']
            # Translate per line to keep layout stable
            try:
                dst_text = self.translate_text(src_text, source_lang, target_lang)
            except Exception:
                dst_text = src_text

            ocr_lines.append(src_text)
            translated_lines.append(dst_text)

            l = max(0, item['left'])
            t = max(0, item['top'])
            r = min(base_img.size[0], item['right'])
            b = min(base_img.size[1], item['bottom'])
            box_w = max(1, r - l)
            box_h = max(1, b - t)

            # 2) If OpenCV isn't available, fallback: softly cover region with sampled bg
            if not use_inpaint:
                pad = 6
                rect = (
                    max(0, l - pad),
                    max(0, t - pad),
                    min(base_img.size[0], r + pad),
                    min(base_img.size[1], b + pad),
                )
                bg = _sample_bg_color(base_img, l, t, r, b)
                draw.rectangle(rect, fill=(bg[0], bg[1], bg[2], 245))

            bg = _sample_bg_color(base_img, l, t, r, b)
            fill, stroke = _pick_text_colors(bg)

            # 3) Fit + wrap translated text to the detected box
            font, lines_wrapped, total_h = _fit_font_wrapped(draw, dst_text, max_w=box_w, max_h=box_h)
            line_gap = int(max(1, font.size * 0.18))
            y = t + max(0, int((box_h - total_h) / 2))
            for ln in lines_wrapped:
                try:
                    draw.text((l, y), ln, fill=fill, font=font, stroke_width=2, stroke_fill=stroke)
                except TypeError:
                    draw.text((l, y), ln, fill=fill, font=font)
                y += _measure(draw, font, ln)[1] + line_gap

        out = base_img.convert('RGB')
        import io
        buf = io.BytesIO()
        out.save(buf, format='PNG')
        png_bytes = buf.getvalue()
        return ("\n".join(ocr_lines).strip(), "\n".join(translated_lines).strip(), png_bytes)

    def _check_provider_available(self):
        """Lightweight preflight check to see if the configured AI provider is available.

        Returns (True, None) if OK, otherwise (False, message) if rate-limited or clearly unavailable.
        """
        if not self.openai_client:
            return (False, 'No AI provider configured: set OPENAI_API_KEY or OPENROUTER_API_KEY')
        try:
            # Call models.list to surface rate-limit errors quickly
            _ = self.openai_client.models.list()
            return (True, None)
        except Exception as e:
            err = str(e).lower()
            if '429' in err or '402' in err or 'rate' in err or 'insufficient' in err or 'free-models' in err or 'credit' in err:
                # Rate-limited or insufficient credits — abort early so background job fails fast
                print(f"AI provider preflight check indicates rate limit/insufficient credits: {e}.")
                return (False, str(e))
            # Non-rate errors: report as unavailable
            print(f"AI provider preflight check returned non-rate error: {e}")
            return (False, str(e))
    def translate_document_background(self, file_path, target_lang, user_id=None, *, ocr_images=False, ocr_langs=None):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'message': 'Queued',
            'download_path': None,
            'error': None,
            'user_id': user_id
        }
        # Preflight provider availability: fail early for rate limit/insufficient credits
        available, message = self._check_provider_available()
        if not available:
            self.jobs[job_id]['status'] = 'failed'
            self.jobs[job_id]['progress'] = 0
            self.jobs[job_id]['message'] = 'Failed - AI provider rate-limited or unavailable'
            self.jobs[job_id]['error'] = str(message)
            return job_id

        def _worker(job_id, file_path, target_lang, ocr_images, ocr_langs):
            try:
                self.jobs[job_id]['status'] = 'in_progress'
                self.jobs[job_id]['progress'] = 5
                self.jobs[job_id]['message'] = 'Starting'

                ocr_done_message = None
                ocr_skip_message = None

                def progress_cb(percent, msg=''):
                    self.jobs[job_id]['progress'] = max(0, min(100, int(percent)))
                    self.jobs[job_id]['message'] = msg

                    nonlocal ocr_done_message, ocr_skip_message
                    try:
                        s = str(msg or '')
                    except Exception:
                        s = ''
                    if s.startswith('DOCX OCR done'):
                        ocr_done_message = s
                    if s.startswith('Skipping DOCX image OCR'):
                        ocr_skip_message = s

                # Let FileService update progress via callback
                output_path = self.file_service.process_document(
                    file_path,
                    target_lang,
                    progress_callback=progress_cb,
                    ocr_images=bool(ocr_images),
                    ocr_langs=ocr_langs,
                )
                self.jobs[job_id]['download_path'] = output_path

                # Persist OCR summary for status endpoint / debugging
                if ocr_images:
                    if ocr_done_message:
                        self.jobs[job_id]['ocr_summary'] = ocr_done_message
                    if ocr_skip_message:
                        self.jobs[job_id]['ocr_skipped'] = ocr_skip_message

                # Detect fallback: if output extension != original extension -> it's a fallback
                try:
                    orig_ext = os.path.splitext(file_path)[1].lower()
                    out_ext = os.path.splitext(output_path)[1].lower()
                    if out_ext and orig_ext and out_ext != orig_ext:
                        self.jobs[job_id]['fallback'] = True
                        self.jobs[job_id]['fallback_reason'] = f"Output changed from {orig_ext} to {out_ext}"
                        # Keep OCR summary visible if available
                        if ocr_images and self.jobs[job_id].get('ocr_summary'):
                            self.jobs[job_id]['message'] = f"Completed with fallback — {self.jobs[job_id]['ocr_summary']}"
                        elif ocr_images and self.jobs[job_id].get('ocr_skipped'):
                            self.jobs[job_id]['message'] = f"Completed with fallback — {self.jobs[job_id]['ocr_skipped']}"
                        else:
                            self.jobs[job_id]['message'] = 'Completed with fallback'
                    else:
                        self.jobs[job_id]['fallback'] = False
                        if ocr_images and self.jobs[job_id].get('ocr_summary'):
                            self.jobs[job_id]['message'] = f"Completed — {self.jobs[job_id]['ocr_summary']}"
                        elif ocr_images and self.jobs[job_id].get('ocr_skipped'):
                            self.jobs[job_id]['message'] = f"Completed — {self.jobs[job_id]['ocr_skipped']}"
                        else:
                            self.jobs[job_id]['message'] = 'Completed'
                except Exception:
                    self.jobs[job_id]['fallback'] = False
                    if ocr_images and self.jobs[job_id].get('ocr_summary'):
                        self.jobs[job_id]['message'] = f"Completed — {self.jobs[job_id]['ocr_summary']}"
                    elif ocr_images and self.jobs[job_id].get('ocr_skipped'):
                        self.jobs[job_id]['message'] = f"Completed — {self.jobs[job_id]['ocr_skipped']}"
                    else:
                        self.jobs[job_id]['message'] = 'Completed'

                self.jobs[job_id]['progress'] = 100
                self.jobs[job_id]['status'] = 'completed'
            except ProviderRateLimitError as e:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error'] = str(e)
                self.jobs[job_id]['message'] = 'Failed - Provider rate limit'
            except Exception as e:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error'] = str(e)
                self.jobs[job_id]['message'] = 'Failed'

        thread = threading.Thread(target=_worker, args=(job_id, file_path, target_lang, ocr_images, ocr_langs), daemon=True)
        thread.start()
        return job_id

    def get_job(self, job_id):
        return self.jobs.get(job_id)