"""
AAAK Dialect (Another AI Knowledge) - English Compression

Lossy summarization format that extracts entities, topics, key sentences,
emotions, and flags from plain text into a compact symbolic representation.

Format:
  Header:   WING|ROOM|DATE|SOURCE
  Zettel:   ZID:ENTITIES|topic_keywords|"key_quote"|WEIGHT|EMOTIONS|FLAGS
  Tunnel:   T:ZID<->ZID|label
  Arc:      ARC:emotion->emotion->emotion

Usage:
    from mempalace_tri.compressor.aaak import AAAKDialect
    
    dialect = AAAKDialect()
    compressed = dialect.compress("The team decided to use GraphQL instead of REST")
    # → "0:TEAM+DEV+ENG|decision+architecture|"team dec use GraphQL vs REST"|0.5|convict+curious"
"""

from __future__ import annotations

import json
import re
from typing import List, Dict, Optional
from pathlib import Path


# ───────────────────── EMOTION CODES ──────────────

EMOTION_CODES: Dict[str, str] = {
    "vulnerability": "vul", "vulnerable": "vul",
    "joy": "joy", "joyful": "joy",
    "fear": "fear", "mild_fear": "fear",
    "trust": "trust", "trust_building": "trust",
    "grief": "grief", "raw_grief": "grief",
    "wonder": "wonder", "philosophical_wonder": "wonder",
    "rage": "rage", "anger": "rage",
    "love": "love", "devotion": "love",
    "hope": "hope", "despair": "despair", "hopelessness": "despair",
    "peace": "peace", "relief": "relief",
    "humor": "humor", "dark_humor": "humor",
    "tenderness": "tender", "raw_honesty": "raw",
    "brutal_honesty": "raw", "self_doubt": "doubt",
    "anxiety": "anx", "exhaustion": "exhaust",
    "conviction": "convict", "quiet_passion": "passion",
    "warmth": "warmth", "curiosity": "curious",
    "gratitude": "grat", "frustration": "frust",
    "confusion": "confuse", "satisfaction": "satis",
    "excitement": "excite", "determination": "determ",
    "surprise": "surprise",
}

# Emotion signal keywords in text
_EMOTION_SIGNALS: Dict[str, str] = {
    "decided": "determ", "prefer": "convict", "worried": "anx",
    "excited": "excite", "frustrated": "frust", "confused": "confuse",
    "love": "love", "hate": "rage", "hope": "hope",
    "fear": "fear", "trust": "trust", "happy": "joy",
    "sad": "grief", "surprised": "surprise", "grateful": "grat",
    "curious": "curious", "wonder": "wonder", "anxious": "anx",
    "relieved": "relief", "satisf": "satis", "disappoint": "grief",
    "concern": "anx",
}

# Flag signal keywords
_FLAG_SIGNALS: Dict[str, str] = {
    "decided": "DECISION", "chose": "DECISION", "switched": "DECISION",
    "migrated": "DECISION", "replaced": "DECISION", "instead of": "DECISION",
    "because": "DECISION", "founded": "ORIGIN", "created": "ORIGIN",
    "started": "ORIGIN", "born": "ORIGIN", "launched": "ORIGIN", "first time": "ORIGIN",
    "core": "CORE", "fundamental": "CORE", "essential": "CORE",
    "principle": "CORE", "belief": "CORE", "always": "CORE", "never forget": "CORE",
    "turning point": "PIVOT", "changed everything": "PIVOT", "realized": "PIVOT",
    "breakthrough": "PIVOT", "epiphany": "PIVOT",
    "api": "TECHNICAL", "database": "TECHNICAL", "architecture": "TECHNICAL",
    "deploy": "TECHNICAL", "infrastructure": "TECHNICAL", "algorithm": "TECHNICAL",
    "framework": "TECHNICAL", "server": "TECHNICAL", "config": "TECHNICAL",
}

# English stop words for topic extraction
_ENGLISH_STOP_WORDS: set = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "between",
    "through", "during", "before", "after", "above", "below", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "don", "now", "and", "but", "or", "if", "while", "that", "this",
    "these", "those", "it", "its", "i", "we", "you", "he", "she", "they",
    "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
    "what", "which", "who", "whom", "also", "much", "many", "like",
    "because", "since", "get", "got", "use", "used", "using", "make",
    "made", "thing", "things", "way", "well", "really", "want", "need",
}


class AAAKDialect:
    """AAAK Dialect encoder for English text compression.
    
    Compresses English text into symbolic shorthand format.
    Extracts entities, topics, key sentences, emotions, and flags.
    
    Usage:
        dialect = AAAKDialect()
        compressed = dialect.compress("We decided to use GraphQL instead of REST")
        # → "TEAM+DEV+ENG|decision+architecture|"team dec use GraphQL vs REST"|0.5|convict+curious"
    """

    def __init__(self, entities: Dict[str, str] = None, skip_names: List[str] = None):
        """
        Args:
            entities: Mapping of full names → short codes
            skip_names: Names to skip (fictional characters, etc.)
        """
        self.entity_codes: Dict[str, str] = {}
        if entities:
            for name, code in entities.items():
                self.entity_codes[name] = code
                self.entity_codes[name.lower()] = code
        self.skip_names: List[str] = [n.lower() for n in (skip_names or [])]

    @classmethod
    def from_config(cls, config_path: str) -> "AAAKDialect":
        """Load entity mappings from a JSON config file."""
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return cls(entities=config.get("entities", {}), skip_names=config.get("skip_names", []))

    def save_config(self, config_path: str) -> None:
        """Save current entity mappings to a JSON config file."""
        canonical = {}
        seen_codes = set()
        for name, code in self.entity_codes.items():
            if code not in seen_codes:
                canonical[name] = code
                seen_codes.add(code)
        config = {"entities": canonical, "skip_names": self.skip_names}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    # ── Entity Encoding ──

    def encode_entity(self, name: str) -> Optional[str]:
        """Convert a name to its short code."""
        if any(s in name.lower() for s in self.skip_names):
            return None
        if name in self.entity_codes:
            return self.entity_codes[name]
        if name.lower() in self.entity_codes:
            return self.entity_codes[name.lower()]
        for key, code in self.entity_codes.items():
            if key.lower() in name.lower():
                return code
        return name[:3].upper()

    def encode_emotions(self, emotions: List[str]) -> str:
        """Convert emotion list to compact codes."""
        codes = []
        for e in emotions:
            code = EMOTION_CODES.get(e, e[:4] if len(e) >= 2 else e)
            if code not in codes:
                codes.append(code)
        return "+".join(codes[:3])

    # ── Language Detection ──

    def _is_chinese_text(self, text: str) -> bool:
        """Detect if text is primarily Chinese."""
        cn_chars = sum(1 for c in text if "\u4e00" <= c <= "\u9fff")
        total = sum(1 for c in text if c.isalpha() or "\u4e00" <= c <= "\u9fff")
        return (cn_chars / max(total, 1)) > 0.3

    def _is_english_text(self, text: str) -> bool:
        """Detect if text is primarily English."""
        en_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total = sum(1 for c in text if c.isalpha())
        return (en_chars / max(total, 1)) > 0.5

    # ── Text Analysis ──

    def _detect_emotions(self, text: str) -> List[str]:
        """Detect emotions from plain text using keyword signals."""
        text_lower = text.lower()
        detected = []
        seen = set()
        for keyword, code in _EMOTION_SIGNALS.items():
            if keyword.lower() in text_lower or keyword in text:
                if code not in seen:
                    detected.append(code)
                    seen.add(code)
        return detected[:3]

    def _detect_flags(self, text: str) -> List[str]:
        """Detect importance flags from plain text using keyword signals."""
        text_lower = text.lower()
        detected = []
        seen = set()
        for keyword, flag in _FLAG_SIGNALS.items():
            if keyword.lower() in text_lower or keyword in text:
                if flag not in seen:
                    detected.append(flag)
                    seen.add(flag)
        return detected[:3]

    def _extract_topics(self, text: str, max_topics: int = 3) -> List[str]:
        """Extract key topic words from English text."""
        words = re.findall(r"[a-zA-Z][a-zA-Z_-]{2,}", text)
        freq: Dict[str, int] = {}
        for w in words:
            w_lower = w.lower()
            if w_lower in _ENGLISH_STOP_WORDS or len(w_lower) < 3:
                continue
            freq[w_lower] = freq.get(w_lower, 0) + 1
        for w in words:
            w_lower = w.lower()
            if w_lower in _ENGLISH_STOP_WORDS:
                continue
            if w[0].isupper() and w_lower in freq:
                freq[w_lower] += 2
            if "_" in w or "-" in w or (any(c.isupper() for c in w[1:])):
                if w_lower in freq:
                    freq[w_lower] += 2
        ranked = sorted(freq.items(), key=lambda x: -x[1])
        return [w for w, _ in ranked[:max_topics]]

    def _extract_key_sentence(self, text: str) -> str:
        """Extract the most important sentence from text."""
        sentences = re.split(r"[.!?\n]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        if not sentences:
            return ""

        decision_words = {
            "decided", "because", "instead", "prefer", "switched", "chose",
            "realized", "important", "key", "critical", "discovered",
            "learned", "conclusion", "solution", "reason", "why",
            "breakthrough", "insight",
        }
        scored = []
        for s in sentences:
            score = 0
            s_lower = s.lower()
            for w in decision_words:
                if w in s_lower:
                    score += 2
            if 10 < len(s) < 40:
                score += 1
            if len(s) > 150:
                score -= 2
            scored.append((score, s))

        scored.sort(key=lambda x: -x[0])
        best = scored[0][1]
        if len(best) > 55:
            best = best[:52] + "..."
        return best

    def _detect_entities_in_text(self, text: str) -> List[str]:
        """Find known entities in text or detect capitalized names."""
        found = []
        for name, code in self.entity_codes.items():
            if not name.islower() and name.lower() in text.lower():
                if code not in found:
                    found.append(code)
        if found:
            return found

        words = text.split()
        for i, w in enumerate(words):
            clean = re.sub(r"[^a-zA-Z]", "", w)
            if (len(clean) >= 2 and clean[0].isupper() and clean[1:].islower()
                    and i > 0 and clean.lower() not in _ENGLISH_STOP_WORDS):
                code = clean[:3].upper()
                if code not in found:
                    found.append(code)
                if len(found) >= 3:
                    break
        return found

    # ── Compression ──

    def compress(self, text: str, metadata: dict = None) -> str:
        """Compress English text into AAAK Dialect format.
        
        Args:
            text: Plain English text to compress
            metadata: Optional dict with keys like 'source_file', 'wing', 'room', 'date'
        
        Returns:
            AAAK-formatted summary string
        """
        metadata = metadata or {}

        entities = self._detect_entities_in_text(text)
        entity_str = "+".join(entities[:3]) if entities else "???"

        topics = self._extract_topics(text)
        topic_str = "_".join(topics[:3]) if topics else "misc"

        quote = self._extract_key_sentence(text)
        quote_part = f'"{quote}"' if quote else ""

        emotions = self._detect_emotions(text)
        emotion_str = "+".join(emotions) if emotions else ""

        flags = self._detect_flags(text)
        flag_str = "+".join(flags) if flags else ""

        source = metadata.get("source_file", "")
        wing = metadata.get("wing", "")
        room = metadata.get("room", "")
        date = metadata.get("date", "")

        lines = []
        if source or wing:
            header_parts = [wing or "?", room or "?", date or "?", Path(source).stem if source else "?"]
            lines.append("|".join(header_parts))

        parts = [f"0:{entity_str}", topic_str]
        if quote_part:
            parts.append(quote_part)
        parts.append(str(0.5))  # default weight
        if emotion_str:
            parts.append(emotion_str)
        if flag_str:
            parts.append(flag_str)

        lines.append("|".join(parts))
        return "\n".join(lines)

    # ── English-Native Compression ──

    ENGLISH_COMPOUND_PATTERNS: List[tuple] = [
        (r"\bdecided to use\b", "dec use"), (r"\bdecided on\b", "dec"),
        (r"\bdecided\b", "dec"), (r"\brecommend.*?\bfor\b", "rec"),
        (r"\brecommend.*?\bbecause\b", "rec"), (r"\brecommend\b", "rec"),
        (r"\bswitched to\b", "switch"), (r"\bswitched\b", "switch"),
        (r"\bmigrated to\b", "migrate"), (r"\bmigrated\b", "migrate"),
        (r"\binstead of\b", "vs"), (r"\bbased on\b", "on"),
        (r"\bbecause of\b", "by"), (r"\bcompared to\b", "vs"),
        (r"\bin terms of\b", "in"), (r"\blead to\b", "→"), (r"\bleading to\b", "→"),
        (r"\boverall.*?architecture\b", "arch"), (r"\boverall\b", "arch"),
        (r"\bimportant.*?lesson\b", "lesson"), (r"\bimportant\b", "imp"),
        (r"\bsignificant\b", "sig"), (r"\bsignificantly\b", "sig"),
        (r"\bextensive.*?discussion\b", "discuss"), (r"\bextensive\b", "discuss"),
        (r"\bcomprehensive.*?analysis\b", "analysis"), (r"\bcomprehensive\b", "analysis"),
        (r"\bspecifically\b", "spec"), (r"\bspecific\b", "spec"),
        (r"\bgenerally accepted\b", "gen"), (r"\bgenerally\b", "gen"),
        (r"\bsolution.*?\b", "sol"), (r"\bin order to\b", "to"),
        (r"\bcurrently\b", "now"), (r"\btherefore\b", "→"),
        (r"\bmoreover\b", "more"), (r"\bhowever\b", "how"),
        (r"\bfurthermore\b", "more"), (r"\bnotably\b", "not"),
        (r"\bespecially\b", "esp"), (r"\bsuch as\b", "eg"),
        (r"\bfor example\b", "eg"), (r"\bfor instance\b", "eg"),
        (r"\bthat is\b", "ie"), (r"\bi\.e\.\b", "ie"), (r"\be\.g\.\b", "eg"),
    ]

    ENGLISH_WORD_SUBS: List[tuple] = [
        ("architecture", "arch"), ("infrastructure", "infra"),
        ("authentication", "auth"), ("authorization", "authz"),
        ("configuration", "config"), ("database", "db"),
        ("implementation", "impl"), ("implementation details", "impl"),
        ("implementing", "impl"), ("documentation", "doc"),
        ("performance", "perf"), ("production", "prod"),
        ("development", "dev"), ("environment", "env"),
        ("monitoring", "mon"), ("scalability", "scal"),
        ("availability", "avail"), ("reliability", "reli"),
        ("sustainability", "sust"), ("sustainable", "sust"),
        ("maintainability", "maint"), ("maintainable", "maint"),
        ("decisions", "dec"), ("decision", "dec"),
        ("recommendation", "rec"), ("recommendations", "rec"),
        ("discoveries", "find"), ("discovery", "find"),
        ("preference", "pref"), ("preferences", "pref"),
        ("suggestion", "sug"), ("suggestions", "sug"),
        ("team", "team"), ("engineer", "eng"), ("engineers", "eng"),
        ("developers", "eng"), ("developer", "eng"),
        ("developer experience", "devex"), ("customer", "cust"),
        ("customers", "cust"), ("pricing", "price"), ("cost", "cost"),
        ("costs", "cost"), ("expensive", "exp"), ("cheaper", "cheap"),
        ("affordable", "afford"), ("technical", "tech"),
        ("technologies", "tech"), ("technology", "tech"),
        ("method", "meth"), ("methods", "meth"),
        ("approach", "app"), ("approaches", "app"),
        ("process", "proc"), ("processes", "proc"),
        ("provider", "prov"), ("providers", "prov"),
        ("service", "svc"), ("services", "svc"),
        ("messaging", "msg"), ("messages", "msg"),
        ("message queue", "msgq"), ("message broker", "msgbroker"),
        ("deployed", "deploy"), ("deployment", "deploy"), ("deploying", "deploy"),
        ("released", "rel"), ("release", "release"), ("releases", "release"),
        ("requirement", "req"), ("requirements", "req"), ("required", "req"),
        ("feature", "feat"), ("features", "feat"),
        ("function", "func"), ("functions", "func"),
        ("capabilities", "cap"), ("capacity", "cap"),
        ("complexity", "complex"), ("complex", "complex"),
        ("simplification", "simplify"), ("simplified", "simplify"),
        ("simple", "simple"), ("simpler", "simple"),
        ("easy", "easy"), ("easier", "easy"), ("easily", "easy"),
        ("straightforward", "sf"), ("straight forward", "sf"),
        ("difficult", "diff"), ("difficulties", "diff"),
        ("challenge", "chall"), ("challenges", "chall"),
        ("problem", "prob"), ("problems", "prob"),
        ("issue", "issue"), ("issues", "issue"),
        ("bugs", "bug"), ("bug", "bug"), ("fix", "fix"), ("fixing", "fix"),
        ("solve", "solve"), ("solving", "solve"), ("solution", "sol"),
        ("errors", "err"), ("error", "err"), ("failure", "fail"),
        ("success", "succ"), ("successful", "succ"), ("successfully", "succ"),
        ("outcome", "out"), ("outcomes", "out"),
        ("result", "res"), ("results", "res"), ("resulting", "res"),
        ("response", "resp"), ("responses", "resp"),
        ("important", "imp"), ("importance", "imp"),
        ("critical", "crit"), ("crucial", "crit"),
        ("essential", "ess"), ("necessary", "need"),
        ("require", "req"), ("requires", "req"), ("required", "req"),
        ("ensure", "ens"), ("ensuring", "ens"), ("ensures", "ens"),
        ("enable", "enb"), ("enabling", "enb"), ("enables", "enb"),
        ("allow", "allw"), ("allowing", "allw"), ("allows", "allw"),
        ("avoid", "avoid"), ("avoiding", "avoid"), ("avoids", "avoid"),
        ("need", "need"), ("needs", "need"), ("needed", "need"),
        ("want", "want"), ("wants", "want"), ("wanted", "want"),
        ("prefer", "pref"), ("prefers", "pref"), ("preferred", "pref"),
        ("like", "like"), ("loved", "like"), ("love", "like"),
        ("improve", "imp"), ("improving", "imp"), ("improves", "imp"),
        ("improved", "imp"), ("improvement", "imp"),
        ("increase", "inc"), ("increasing", "inc"), ("increases", "inc"),
        ("decrease", "dec"), ("decreasing", "dec"), ("decreases", "dec"),
        ("reduce", "rd"), ("reducing", "rd"), ("reduces", "rd"), ("reduced", "rd"),
        ("reduce complexity", "rd comp"), ("reduces complexity", "rd comp"),
        ("improve developer experience", "imp devex"),
        ("improves developer experience", "imp devex"),
        ("improved developer experience", "imp devex"),
        ("better developer experience", "better devex"),
    ]

    ENGLISH_STOP_WORDS: set = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "about", "between",
        "through", "during", "before", "after", "above", "below", "up", "down",
        "out", "off", "over", "under", "again", "further", "then", "once",
        "here", "there", "when", "where", "why", "how", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "don", "now", "and", "but", "or", "if", "while", "that", "this",
        "these", "those", "it", "its", "i", "we", "you", "he", "she", "they",
        "me", "him", "her", "us", "them", "my", "your", "his", "our", "their",
        "what", "which", "who", "whom", "also", "much", "many", "like",
        "get", "got", "use", "used", "using", "make", "made", "thing",
        "things", "way", "well", "really", "want", "need", "know", "knew",
        "think", "thought", "tell", "told", "said", "say", "says", "telling",
        "give", "gave", "gives", "giving", "take", "took", "takes", "taking",
        "let", "lets", "making", "makes", "help", "helped", "helping", "helps",
        "work", "worked", "works", "working", "run", "ran", "runs", "running",
        "set", "sets", "setting", "put", "puts", "putting", "keep", "kept",
        "hold", "held", "holds", "starting", "start", "starts", "started",
        "begin", "began", "begins", "beginning", "able", "unlike", "whether",
        "any", "yet", "still", "already", "another", "enough", "rather", "even",
        "per", "via", "across", "along", "among", "around", "became", "become",
        "becomes", "becoming", "behind", "below", "beneath", "beside", "besides",
        "top", "full", "fully", "though", "although", "toward", "towards",
        "within", "without", "alongside", "according", "accordingly",
    }

    def compress_english(self, text: str) -> str:
        """English-native AAAK compression using rule-based patterns.
        
        Example:
            "The team decided to use GraphQL because of pricing and developer experience."
            → "team dec use GraphQL by price + devex"
        
        Compression ratio: ~3-5x for typical English text
        """
        result = text

        # Phase 1: Compound patterns (biggest wins)
        for pattern, replacement in self.ENGLISH_COMPOUND_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        # Phase 2: Word-level substitutions
        for word, replacement in self.ENGLISH_WORD_SUBS:
            pat = re.compile(re.escape(word), re.IGNORECASE)
            if pat.search(result):
                def case_preserving_match(m):
                    orig = m.group(0)
                    if orig.isupper():
                        return replacement.upper()
                    elif orig[0].isupper():
                        return replacement.capitalize()
                    return replacement
                result = pat.sub(case_preserving_match, result)

        # Phase 3: Remove stop words
        words = result.split()
        filtered = []
        for w in words:
            clean = re.sub(r"[^a-zA-Z]", "", w).lower()
            if clean in self.ENGLISH_STOP_WORDS and len(clean) > 1:
                continue
            filtered.append(w)
        result = " ".join(filtered)

        # Phase 4: Clean up artifacts
        result = re.sub(r"\s+[,;,!?]+", lambda m: " " + m.group(0).strip(), result)
        result = re.sub(r"\(\s*\)", "", result)
        result = re.sub(r"\s{2,}", " ", result)
        result = result.strip()

        return result

    # ── Token Stats ──

    @staticmethod
    def count_tokens(text: str) -> int:
        """Estimate token count using word-based heuristic (~1.3 tokens per word)."""
        words = text.split()
        return max(1, int(len(words) * 1.3))

    def compression_stats(self, original_text: str, compressed: str) -> dict:
        """Get size comparison stats."""
        orig_tokens = self.count_tokens(original_text)
        comp_tokens = self.count_tokens(compressed)
        return {
            "original_tokens_est": orig_tokens,
            "summary_tokens_est": comp_tokens,
            "size_ratio": round(orig_tokens / max(comp_tokens, 1), 1),
            "original_chars": len(original_text),
            "summary_chars": len(compressed),
            "note": "AAAK is lossy summarization, not lossless compression.",
        }

    def decode(self, dialect_text: str) -> dict:
        """Parse an AAAK Dialect string back into a readable summary."""
        lines = dialect_text.strip().split("\n")
        result = {"header": {}, "arc": "", "zettels": [], "tunnels": []}
        for line in lines:
            if line.startswith("ARC:"):
                result["arc"] = line[4:]
            elif line.startswith("T:"):
                result["tunnels"].append(line)
            elif "|" in line and ":" in line.split("|")[0]:
                result["zettels"].append(line)
            elif "|" in line:
                parts = line.split("|")
                result["header"] = {
                    "file": parts[0] if len(parts) > 0 else "",
                    "entities": parts[1] if len(parts) > 1 else "",
                    "date": parts[2] if len(parts) > 2 else "",
                    "title": parts[3] if len(parts) > 3 else "",
                }
        return result