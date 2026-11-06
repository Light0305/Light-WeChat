"""Load pinned, locally vendored upstream validators without global installation."""
from pathlib import Path
import importlib.util

SKILL = Path(__file__).resolve().parents[1]


def module(relative):
    path = SKILL / "vendor" / relative
    spec = importlib.util.spec_from_file_location("chuanlab_" + path.stem, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def validate_body(content):
    return module("gzh-design/scripts/validate_gzh_html.py").validate(content)


def editorial_report(article):
    import yaml
    assessment = yaml.safe_load((article / "assessment.yaml").read_text(encoding="utf-8"))
    if not isinstance(assessment, dict):
        raise ValueError("assessment.yaml must contain an actual five-dimension editor assessment")
    text = (article / "draft.md").read_text(encoding="utf-8")
    return module("wewrite/src/wewrite/commands/content_eval.py").build_report(text, text, assessment)


def style_signals(text):
    return module("wewrite/src/wewrite/commands/humanness_score.py").score_article(text)
