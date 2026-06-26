"""知识库子包：文档加载、切片、检索。

数据目录：poster-web/kb_data/
  ├── global/<doc_id>/{meta.json, original.<ext>, text.txt, chunks.json}
  └── projects/<pid>/<doc_id>/(同上)
  └── functions/<pid>/<function_id>/<kb_type>/<doc_id>/(同上)
"""
from app_paths import KB_DATA_DIR

KB_DATA_DIR.mkdir(exist_ok=True)
(KB_DATA_DIR / "global").mkdir(exist_ok=True)
(KB_DATA_DIR / "projects").mkdir(exist_ok=True)
(KB_DATA_DIR / "functions").mkdir(exist_ok=True)
