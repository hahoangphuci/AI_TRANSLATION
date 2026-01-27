import openai
import deepl
import os
import threading
import uuid
import time
from dotenv import load_dotenv
from app.services.file_service import FileService

# Load .env từ thư mục backend (app/services -> app -> backend)
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_backend_dir, '.env'))

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
        self.file_service = FileService(translator=self.translate_text)
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
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=4096,
            temperature=0
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def translate_text(self, text, source_lang, target_lang):
        if target_lang is None or not str(target_lang).strip():
            raise ValueError("target_lang is required")
        if text is None:
            return ""
        target_lang = str(target_lang).strip()
        source_lang = (str(source_lang).strip() if source_lang is not None else 'auto') or 'auto'
        t = target_lang.lower()

        # 1) Thử DeepL CHỈ KHI ngôn ngữ đích nằm trong danh sách DeepL hỗ trợ
        if self.deepl_translator and t in DEEPL_TARGET_MAP:
            try:
                dl_target = DEEPL_TARGET_MAP[t]
                result = self.deepl_translator.translate_text(text, target_lang=dl_target)
                return result.text
            except Exception as e:
                print(f"DeepL failed for {t}: {e}, falling back to AI")

        # 2) Dùng OpenAI/OpenRouter: cho ngôn ngữ DeepL không hỗ trợ HOẶC khi DeepL lỗi
        last_error = None
        try:
            out = self._openai_translate(text, source_lang, target_lang, t)
            if out is not None:
                return out
        except Exception as e:
            last_error = e
            import traceback
            traceback.print_exc()
            print(f"AI translation failed: {e}")

        msg = (
            "Không thể dịch: cấu hình DEEPL_API_KEY và/hoặc (OPENAI_API_KEY hoặc OPENROUTER_API_KEY) trong backend/.env. "
            "Với ngôn ngữ DeepL không hỗ trợ, cần OPENAI hoặc OPENROUTER. "
        )
        if last_error:
            msg += f" Lỗi API: {last_error}"
        raise RuntimeError(msg)
    
    def translate_document(self, file_path, target_lang):
        # Synchronous translation (kept for compatibility)
        return self.file_service.process_document(file_path, target_lang)

    def translate_document_background(self, file_path, target_lang, user_id=None):
        job_id = str(uuid.uuid4())
        self.jobs[job_id] = {
            'status': 'pending',
            'progress': 0,
            'message': 'Queued',
            'download_path': None,
            'error': None,
            'user_id': user_id
        }

        def _worker(job_id, file_path, target_lang):
            try:
                self.jobs[job_id]['status'] = 'in_progress'
                self.jobs[job_id]['progress'] = 5
                self.jobs[job_id]['message'] = 'Starting'

                def progress_cb(percent, msg=''):
                    self.jobs[job_id]['progress'] = max(0, min(100, int(percent)))
                    self.jobs[job_id]['message'] = msg

                # Let FileService update progress via callback
                output_path = self.file_service.process_document(file_path, target_lang, progress_callback=progress_cb)
                self.jobs[job_id]['download_path'] = output_path
                # Detect fallback: if output extension != original extension -> it's a fallback
                try:
                    orig_ext = os.path.splitext(file_path)[1].lower()
                    out_ext = os.path.splitext(output_path)[1].lower()
                    if out_ext and orig_ext and out_ext != orig_ext:
                        self.jobs[job_id]['fallback'] = True
                        self.jobs[job_id]['fallback_reason'] = f"Output changed from {orig_ext} to {out_ext}"
                        self.jobs[job_id]['message'] = 'Completed with fallback'
                    else:
                        self.jobs[job_id]['fallback'] = False
                        self.jobs[job_id]['message'] = 'Completed'
                except Exception:
                    self.jobs[job_id]['fallback'] = False
                    self.jobs[job_id]['message'] = 'Completed'

                self.jobs[job_id]['progress'] = 100
                self.jobs[job_id]['status'] = 'completed'
            except Exception as e:
                self.jobs[job_id]['status'] = 'failed'
                self.jobs[job_id]['error'] = str(e)
                self.jobs[job_id]['message'] = 'Failed'

        thread = threading.Thread(target=_worker, args=(job_id, file_path, target_lang), daemon=True)
        thread.start()
        return job_id

    def get_job(self, job_id):
        return self.jobs.get(job_id)