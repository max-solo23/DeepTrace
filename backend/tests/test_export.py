"""
Test script for markdown export functionality.
"""
from datetime import datetime
from pathlib import Path

# Simulate the last_report structure
last_report = {
    "content": """# Research Report: Test Python Export

## Summary
This is a test export of a research report.

## Findings
- Export functionality works
- Files are saved with timestamps
- Markdown formatting preserved

## Confidence Score
0.85
""",
    "query": "Test Python Export"
}

def export_report() -> str:
    """Export the last generated report as a markdown file."""
    if not last_report["content"]:
        return None

    # Create exports directory if it doesn't exist
    exports_dir = Path("exports")
    exports_dir.mkdir(exist_ok=True)

    # Generate filename with timestamp and sanitized query
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    query_slug = last_report["query"][:50].replace(" ", "_").replace("/", "_") if last_report["query"] else "report"
    # Remove invalid filename characters
    query_slug = "".join(c for c in query_slug if c.isalnum() or c in ('_', '-'))
    filename = f"research_{query_slug}_{timestamp}.md"
    filepath = exports_dir / filename

    # Write the report to file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(last_report["content"])
        print(f"[OK] Report exported to: {filepath}")
        return str(filepath)
    except Exception as e:
        print(f"[FAIL] Export failed: {e}")
        return None


if __name__ == "__main__":
    print("Testing markdown export...")
    result = export_report()

    if result:
        print(f"[SUCCESS] Export test passed!")
        print(f"File created: {result}")

        # Verify file exists and has content
        filepath = Path(result)
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"File size: {size} bytes")

            # Read and display first few lines
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                print("\nFirst 5 lines of exported file:")
                for line in lines:
                    print(f"  {line.rstrip()}")
        else:
            print("[FAIL] File not found after export")
    else:
        print("[FAIL] Export returned None")
