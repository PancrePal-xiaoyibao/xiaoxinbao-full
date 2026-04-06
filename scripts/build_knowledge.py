from __future__ import annotations

import json
from pathlib import Path

from xiaoxinbao.modules.knowledge.retriever import KnowledgeRetriever


def main() -> None:
    knowledge_dir = Path("config/knowledge")
    retriever = KnowledgeRetriever(knowledge_dir)
    hits = retriever.search("心情不好 压力大", limit=10)
    manifest = [hit.model_dump() for hit in hits]
    output_path = knowledge_dir / "manifest.json"
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(manifest)} knowledge preview entries to {output_path}")


if __name__ == "__main__":
    main()
