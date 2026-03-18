import re
import sys
from pathlib import Path

# Add core to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core.semantic_chunking import split_by_article, _ARTICLE_START_RE

def test_split():
    data_dir = Path("data")
    txt_files = sorted(data_dir.glob("*.txt"))
    
    results = []
    
    relaxed_re = re.compile(r"^第[一二三四五六七八九十百千万零〇\d]+条.*", re.M)

    for p in txt_files:
        text = p.read_text(encoding="utf-8")
        chunks = split_by_article(text)
        
        results.append(f"=== File: {p.name} ===")
        results.append(f"Total chunks found: {len(chunks)}")
        
        bad_chunks = []
        for i, c in enumerate(chunks):
            if not re.match(r"^第[一二三四五六七八九十百千万零〇\d]+条", c):
                bad_chunks.append((i, c[:50]))
                
        if bad_chunks:
            results.append("\n❌ Found chunks that don't start with Article title:")
            for i, snippet in bad_chunks:
                results.append(f"  Chunk {i}: {repr(snippet)}")
        else:
            results.append("\n✅ All chunks start with Article title correctly.")

        relaxed_matches = list(relaxed_re.finditer(text))
        strict_matches = list(_ARTICLE_START_RE.finditer(text))
        
        results.append(f"Strict matches (\\b): {len(strict_matches)}")
        results.append(f"Relaxed matches (no \\b): {len(relaxed_matches)}")
        
        if len(strict_matches) != len(relaxed_matches):
            results.append("⚠️ MISMATCH between strict and relaxed regex!")
        else:
            results.append("✅ Strict and relaxed regex match count is identical. \\b is safe.")
        results.append("")

    Path("split_test_result_all.txt").write_text("\n".join(results), encoding="utf-8")
    print("Done")

if __name__ == "__main__":
    test_split()
