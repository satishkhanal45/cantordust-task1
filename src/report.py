from datetime import datetime
from pathlib import Path


HEADER = """# SunBridge Trading — Nepal Import Compliance Draft
## China → Nepal | Solar Grid-Tied Inverter
Generated: {ts}
---

"""


def write_all(outputs: dict[str, str], output_dir: str | Path = "output") -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Intermediate files including cover note
    for key, label in [
        ("cover_note", "cover_note_to_ramesh"),
        ("facts_pdf1", "facts_manufacturer_pdf1"),
        ("facts_pdf2", "facts_manufacturer_pdf2"),
        ("reconciliation", "reconciliation_report"),
    ]:
        p = out / f"{label}.md"
        p.write_text(
            f"# {label.replace('_', ' ').title()}\nGenerated: {ts}\n\n---\n\n{outputs[key]}\n"
        )

    # Final draft — the main deliverable
    draft_path = out / "nepal_compliance_draft.md"
    draft_path.write_text(HEADER.format(ts=ts) + outputs["draft"] + "\n")

    return draft_path