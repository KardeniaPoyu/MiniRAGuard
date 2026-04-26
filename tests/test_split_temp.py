import sys, os
sys.path.insert(0, os.path.abspath('backend'))
import re
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.semantic_chunking import split_by_article, _ARTICLE_START_RE

def test_split():
    text = Path("data/civil_code.txt").read_text(encoding="utf-8")
    chunks = split_by_article(text)
    
    print(f"Total chunks found: {len(chunks)}")
    
    # Check if all chunks start with "�? and some numbers and "�?
    bad_chunks = []
    for i, c in enumerate(chunks):
        if not re.match(r"^第[一二三四五六七八九十百千万零〇\d]+�?, c):
            bad_chunks.append((i, c[:50]))
            
    if bad_chunks:
        print("\n�?Found chunks that don't start with Article title:")
        for i, snippet in bad_chunks:
            print(f"  Chunk {i}: {repr(snippet)}")
    else:
        print("\n�?All chunks start with Article title correctly.")

    # Now let's try a regex WITHOUT \b to see if we missed any
    relaxed_re = re.compile(r"^第[一二三四五六七八九十百千万零〇\d]+�?*", re.M)
    relaxed_matches = list(relaxed_re.finditer(text))
    strict_matches = list(_ARTICLE_START_RE.finditer(text))
    
    print(f"\nStrict matches (\b): {len(strict_matches)}")
    print(f"Relaxed matches (no \b): {len(relaxed_matches)}")
    
    if len(strict_matches) != len(relaxed_matches):
        print("\n⚠️ MISMATCH between strict and relaxed regex!")
        strict_set = {m.group(0).split()[0] for m in strict_matches}
        relaxed_set = {m.group(0).split()[0] for m in relaxed_matches}
        
        missed = relaxed_set - strict_set
        extra = strict_set - relaxed_set
        
        if missed:
            print(f"  Missed with \b: {missed}")
        if extra:
            print(f"  Extra with \b (should not happen): {extra}")
    else:
        print("\n�?Strict and relaxed regex match count is identical. \b is safe.")

if __name__ == "__main__":
    test_split()
