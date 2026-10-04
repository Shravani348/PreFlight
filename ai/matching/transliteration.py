"""Deterministic Devanagari to Latin transliteration helper for cross-script name matching.

This module provides a lightweight, deterministic, rule-based transliterator
specifically tailored for personal names in Hindi and Marathi administrative records.
It is NOT a general-purpose natural language transliteration system.
"""

import unicodedata
from typing import Optional, Set

# Independent Vowels (Svaras)
INDEPENDENT_VOWELS = {
    "\u0905": "a",    # अ
    "\u0906": "a",    # आ (standard in names: Anand, Ahire, Patil, Sharma)
    "\u0907": "i",    # इ
    "\u0908": "i",    # ई
    "\u0909": "u",    # उ
    "\u090A": "u",    # ऊ (puja / anup)
    "\u090B": "ri",   # ऋ
    "\u0960": "ri",   # ॠ
    "\u090C": "li",   # ऌ
    "\u0961": "li",   # ॡ
    "\u090E": "e",    # ऎ (short e)
    "\u090F": "e",    # ए
    "\u0910": "ai",   # ऐ
    "\u0912": "o",    # ऒ (short o)
    "\u0913": "o",    # ओ
    "\u0914": "au",   # औ
}

# Dependent Vowel Signs (Matras)
VOWEL_MATRAS = {
    "\u093E": "a",    # ा
    "\u093F": "i",    # ि
    "\u0940": "i",    # ी (priti, ahire, patil)
    "\u0941": "u",    # ु
    "\u0942": "u",    # ू (puja)
    "\u0943": "ri",   # ृ
    "\u0944": "ri",   # ॄ
    "\u0945": "e",    # ॅ (candra e)
    "\u0946": "e",    # ॆ (short e)
    "\u0947": "e",    # े
    "\u0948": "ai",   # ै
    "\u0949": "o",    # ॉ (candra o)
    "\u094A": "o",    # ॊ (short o)
    "\u094B": "o",    # ो
    "\u094C": "au",   # ौ
}

# Consonants (Vyanjanas)
CONSONANTS = {
    "\u0915": "k",    # क
    "\u0916": "kh",   # ख
    "\u0917": "g",    # ग
    "\u0918": "gh",   # घ
    "\u0919": "ng",   # ङ
    "\u091A": "ch",   # च
    "\u091B": "chh",  # छ
    "\u091C": "j",    # ज
    "\u091D": "jh",   # झ
    "\u091E": "ny",   # ञ
    "\u091F": "t",    # ट
    "\u0920": "th",   # ठ
    "\u0921": "d",    # ड
    "\u0922": "dh",   # ढ
    "\u0923": "n",    # ण
    "\u0924": "t",    # त
    "\u0925": "th",   # थ
    "\u0926": "d",    # द
    "\u0927": "dh",   # ध
    "\u0928": "n",    # न
    "\u0929": "nn",   # ऩ
    "\u092A": "p",    # प
    "\u092B": "ph",   # फ
    "\u092C": "b",    # ब
    "\u092D": "bh",   # भ
    "\u092E": "m",    # म
    "\u092F": "y",    # य
    "\u0930": "r",    # र
    "\u0931": "r",    # ऱ (Marathi r)
    "\u0932": "l",    # ल
    "\u0933": "l",    # ळ (Marathi retroflex l, e.g. Patil)
    "\u0934": "l",    # ऴ
    "\u0935": "v",    # व (v / w)
    "\u0936": "sh",   # श
    "\u0937": "sh",   # ष
    "\u0938": "s",    # स
    "\u0939": "h",    # ह
    # Precomposed nukta consonants
    "\u0958": "q",    # क़
    "\u0959": "kh",   # ख़
    "\u095A": "g",    # ग़
    "\u095B": "z",    # ज़
    "\u095C": "r",    # ड़
    "\u095D": "rh",   # ढ़
    "\u095E": "f",    # फ़
    "\u095F": "y",    # य़
}

VIRAMA = "\u094D"       # ् (halant)
ANUSVARA = "\u0902"     # ं
CHANDRABINDU = "\u0901" # ँ
VISARGA = "\u0903"      # ः
NUKTA = "\u093C"        # ़

# Labial consonants for anusvara phonetic class assimilation (m before p, ph, b, bh, m, f)
LABIAL_CONSONANTS: Set[str] = {"\u092A", "\u092B", "\u092C", "\u092D", "\u092E", "\u095E"}


def is_devanagari(text: Optional[str]) -> bool:
    """Check if the provided text contains any Devanagari Unicode characters."""
    if not text or not isinstance(text, str):
        return False
    return any("\u0900" <= c <= "\u097f" for c in text)


def is_latin(text: Optional[str]) -> bool:
    """Check if the provided text contains any Latin alphabet characters."""
    if not text or not isinstance(text, str):
        return False
    return any("a" <= c <= "z" or "A" <= c <= "Z" for c in text)


def is_cross_script(text_a: Optional[str], text_b: Optional[str]) -> bool:
    """Check if two strings represent a cross-script comparison between Latin and Devanagari."""
    if not text_a or not text_b:
        return False
    dev_a = is_devanagari(text_a)
    dev_b = is_devanagari(text_b)
    lat_a = is_latin(text_a)
    lat_b = is_latin(text_b)
    return (dev_a and lat_b and not lat_a) or (dev_b and lat_a and not lat_b)


def _transliterate_devanagari_word(word: str) -> str:
    """Deterministically transliterate a single Devanagari token to Latin."""
    # Ensure canonical NFC decomposition
    word = unicodedata.normalize("NFC", word)
    chars = list(word)
    n = len(chars)
    out = []
    i = 0
    has_preceding_vowel = False

    while i < n:
        c = chars[i]

        # 1. Independent Vowel
        if c in INDEPENDENT_VOWELS:
            out.append(INDEPENDENT_VOWELS[c])
            has_preceding_vowel = True
            i += 1
            continue

        # 2. Consonant
        if c in CONSONANTS:
            # Phonetic heuristic for 'व': Anglicized as 'w' before 'ा' (Pawar, Gaikwad, Sawant)
            # otherwise 'v' (Vikas, Vijay, Jadhav, Shiv)
            if c == "\u0935":
                if i + 1 < n and chars[i + 1] == "\u093E":
                    base = "w"
                else:
                    base = "v"
            else:
                base = CONSONANTS[c]
            out.append(base)

            # Advance past nukta if decomposed
            next_idx = i + 1
            if next_idx < n and chars[next_idx] == NUKTA:
                next_idx += 1

            if next_idx < n:
                next_c = chars[next_idx]
                if next_c == VIRAMA:
                    # Halant suppresses inherent vowel; next consonant forms conjunct
                    has_preceding_vowel = False
                    i = next_idx + 1
                    continue
                elif next_c in VOWEL_MATRAS:
                    # Explicit vowel matra
                    out.append(VOWEL_MATRAS[next_c])
                    has_preceding_vowel = True
                    i = next_idx + 1
                    continue
                elif next_c in (ANUSVARA, CHANDRABINDU):
                    # Inherent vowel 'a' before nasal anusvara
                    nasal = "m" if (next_idx + 1 < n and chars[next_idx + 1] in LABIAL_CONSONANTS) else "n"
                    out.append("a" + nasal)
                    has_preceding_vowel = False
                    i = next_idx + 1
                    continue
                else:
                    # Followed by another consonant: evaluate schwa deletion
                    # In Hindi/Marathi names: VC_CV environment deletes medial schwa
                    # (e.g. Deshmukh, Kulkarni)
                    drop_schwa = False
                    if has_preceding_vowel and i > 0 and next_c in CONSONANTS:
                        after_next = next_idx + 1
                        if after_next < n and chars[after_next] in VOWEL_MATRAS:
                            drop_schwa = True

                    if not drop_schwa:
                        out.append("a")
                        has_preceding_vowel = True
                    else:
                        has_preceding_vowel = False
                    i = next_idx
                    continue
            else:
                # Word-final consonant: inherent schwa 'a' is dropped in Hindi and Marathi
                has_preceding_vowel = False
                i = next_idx
                continue

        # 3. Isolated vowel marks, anusvara, visarga, or non-Devanagari characters
        if c in VOWEL_MATRAS:
            out.append(VOWEL_MATRAS[c])
            has_preceding_vowel = True
        elif c in (ANUSVARA, CHANDRABINDU):
            nasal = "m" if (i + 1 < n and chars[i + 1] in LABIAL_CONSONANTS) else "n"
            out.append(nasal)
            has_preceding_vowel = False
        elif c == VISARGA:
            out.append("h")
            has_preceding_vowel = False
        elif c == VIRAMA or c == NUKTA:
            # Standalone or trailing virama/nukta ignored safely
            pass
        else:
            # Punctuation, digits, Latin characters, or unsupported Unicode pass through untouched
            out.append(c)
            has_preceding_vowel = False

        i += 1

    return "".join(out)


def transliterate_devanagari_to_latin(text: Optional[str]) -> str:
    """Transliterate a Devanagari name string to Latin characters deterministically.

    If text is empty or contains no Devanagari characters, it is returned unchanged (or empty).
    Latin text, punctuation, numbers, and already-normalized strings are preserved safely.
    """
    if text is None or not text.strip():
        return ""
    if not isinstance(text, str):
        text = str(text)

    # Return immediately if no Devanagari characters present
    if not is_devanagari(text):
        return text

    words = text.split()
    return " ".join(_transliterate_devanagari_word(w) for w in words)
