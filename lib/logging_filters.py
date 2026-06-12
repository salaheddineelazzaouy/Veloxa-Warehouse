import re
import logging


class PIIScrubber(logging.Filter):
    PII_PATTERNS = [
        (r"\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b", "[EMAIL REDACTED]"),
        (r"\b(?:212|0)[6-7]\d{8}\b", "[PHONE REDACTED]"),
        (r"\b\d{16}\b", "[CARD REDACTED]"),
        (r'"password":\s*"[^"]+"', '"password":"[REDACTED]"'),
        (r'"token":\s*"[^"]+"', '"token":"[TOKEN REDACTED]"'),
        (r'"refresh":\s*"[^"]+"', '"refresh":"[TOKEN REDACTED]"'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PII_PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(
                self._scrub(str(a)) if isinstance(a, str) else a
                for a in record.args
            )
        return True

    @classmethod
    def _scrub(cls, text: str) -> str:
        for pattern, replacement in cls.PII_PATTERNS:
            text = re.sub(pattern, replacement, text)
        return text
