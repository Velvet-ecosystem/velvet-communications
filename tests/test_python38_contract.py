import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_communications_sources_parse_with_python38_grammar():
    for path in sorted((ROOT / "src").rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path), feature_version=(3, 8))
