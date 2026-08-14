import os
from pathlib import Path


def move_babeldoc_output(event, target_file):
    """Move BabelDOC's real monolingual output to the task target path."""
    result = event.get('translate_result') if event else None
    if result is None:
        return None

    source_path = None
    for attribute in ('no_watermark_mono_pdf_path', 'mono_pdf_path'):
        candidate = getattr(result, attribute, None)
        if candidate and Path(candidate).is_file():
            source_path = Path(candidate)
            break

    if source_path is None:
        return None

    target_path = Path(target_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.resolve() != target_path.resolve():
        os.replace(str(source_path), str(target_path))

    return target_path if target_path.is_file() else None
