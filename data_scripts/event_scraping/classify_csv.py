import csv
import sys
from pathlib import Path

# Adjust this import if your function/module name differs
from classification.pure_classifier import classify_caption

def classify_file(input_csv: Path, output_csv: Path,
                  text_col_candidates=("text", "description", "caption")):
    with input_csv.open(newline="", encoding="utf-8") as infile, \
         output_csv.open("w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        cols = reader.fieldnames or []
        text_col = next((c for c in text_col_candidates if c in cols), None)
        if not text_col:
            raise SystemExit(
                f"Could not find a text column in {text_col_candidates}. "
                f"Found columns: {cols}"
            )

        fieldnames = list(cols)
        for extra in ("tags", "score"):
            if extra not in fieldnames:
                fieldnames.append(extra)

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            text = " ".join([
            row.get(text_col, "") or "",
            row.get("event_title", "") or row.get("title", "") or "",
            row.get("category", "") or ""
        ])
            tags, score = classify_caption(text)
            row["tags"] = ", ".join(tags)
            row["score"] = score
            writer.writerow(row)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: classify_csv.py <input.csv> [output.csv]")

    input_csv = Path(sys.argv[1]).resolve()
    default_out = input_csv.with_name(input_csv.stem + "_classified.csv")
    output_csv = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else default_out

    classify_file(input_csv, output_csv)
    print(f"✅ Wrote {output_csv}")
