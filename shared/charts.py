from typing import Dict, List, Optional
import shutil

def draw_ascii_bar_chart(data: Dict[str, float], title: str, width: int = 60) -> str:
    """
    Generates an ASCII bar chart from the provided data.

    Args:
        data: A dictionary where keys are labels and values are numeric.
        title: The title of the chart.
        width: The max width of the bars (excluding labels).

    Returns:
        A string representing the chart.
    """
    if not data:
        return f"{title}\n(No data)"

    # Determine max value for scaling
    max_val = max(data.values()) if data.values() else 0
    if max_val == 0:
        max_val = 1  # Avoid division by zero

    # Determine max label length for alignment
    max_label_len = max(len(str(k)) for k in data.keys())

    lines = [f"--- {title} ---"]

    for label, value in data.items():
        # Calculate bar length
        bar_len = int((value / max_val) * width)
        bar = "█" * bar_len

        # Format label
        label_str = str(label).ljust(max_label_len)

        # Add value label if space permits, otherwise put on next line?
        # Actually, let's put it after the bar.
        lines.append(f"{label_str} | {bar} {value}")

    return "\n".join(lines)
