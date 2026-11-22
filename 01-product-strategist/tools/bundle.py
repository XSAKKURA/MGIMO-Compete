"""Собрать единый мастер-файл из инструкций и навыков, без зависимостей."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parts = [root / "src/instructions.md", *sorted((root / "skills").glob("*.md"))]
instructions = [part.read_text(encoding="utf-8").strip() for part in parts]
(root / "MASTER.md").write_text("\n\n".join(instructions) + "\n", encoding="utf-8")
