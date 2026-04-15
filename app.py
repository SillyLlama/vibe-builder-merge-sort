"""
Playlist Vibe Builder — CISC 121 Project
An interactive Merge Sort visualizer that sorts playlists by vibe or duration. Watch the algorithm work step by step with colour-coded cards and auto-play.
"""

import gradio as gr
import random
import time

# ---------------------------------------------------------------------------
# Sample Data
# ---------------------------------------------------------------------------

SAMPLE_SONGS = [
    {"title": "Blinding Lights",  "artist": "The Weeknd",      "vibe": 73, "duration": 200},
    {"title": "As It Was",        "artist": "Harry Styles",     "vibe": 55, "duration": 167},
    {"title": "Levitating",       "artist": "Dua Lipa",         "vibe": 83, "duration": 203},
    {"title": "Heat Waves",       "artist": "Glass Animals",    "vibe": 48, "duration": 238},
    {"title": "Stay",             "artist": "The Kid LAROI",    "vibe": 80, "duration": 141},
    {"title": "Peaches",          "artist": "Justin Bieber",    "vibe": 55, "duration": 198},
    {"title": "Good 4 U",         "artist": "Olivia Rodrigo",   "vibe": 66, "duration": 178},
    {"title": "INDUSTRY BABY",    "artist": "Lil Nas X",        "vibe": 76, "duration": 212},
]

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_songs(text):
    """
Converts a list of songs into data that the app can use. It checks that each line follows the format Title | Artist | Vibe | Duration
    """
    songs = []
    for i, line in enumerate(text.strip().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 4:
            return f" Line {i}: expected 4 fields separated by '|', got {len(parts)}."
        try:
            songs.append({
                "title": parts[0],
                "artist": parts[1],
                "vibe": int(parts[2]),
                "duration": int(parts[3]),
            })
        except ValueError:
            return f" Line {i}: Vibe and Duration must be whole numbers."
    return songs if len(songs) >= 2 else " Please enter at least 2 songs."


def songs_to_text(songs):
    """Convert a list of song dicts back to editable pipe-separated text."""
    return "\n".join(
        f"{s['title']} | {s['artist']} | {s['vibe']} | {s['duration']}"
        for s in songs
    )


# ---------------------------------------------------------------------------
# Merge Sort — records comparison + merge steps for visualization
# ---------------------------------------------------------------------------

def merge_sort_trace(arr, key):
    """
Sorts the list and saves every step of the process. This lets the UI animate the comparisons and merges.
    """
    steps = []

    def merge(left, right):
        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            # Record the comparison
            steps.append({
                "left": left[:],
                "right": right[:],
                "merged": result[:],
                "desc": (
                    f" Comparing <b>{left[i]['title']}</b> "
                    f"({key}={left[i][key]}) vs "
                    f"<b>{right[j]['title']}</b> ({key}={right[j][key]})"
                ),
            })

            if left[i][key] <= right[j][key]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1

        result.extend(left[i:])
        result.extend(right[j:])

        # Record the completed merge
        steps.append({
            "left": left[:],
            "right": right[:],
            "merged": result[:],
            "desc": " Merged into sorted group",
        })
        return result

    def sort(sub):
        if len(sub) <= 1:
            return sub
        mid = len(sub) // 2
        return merge(sort(sub[:mid]), sort(sub[mid:]))

    final = sort(arr)
    return steps, final


# ---------------------------------------------------------------------------
# HTML rendering helpers
# ---------------------------------------------------------------------------

def song_box(song, key, color):
    """Render a single song as a styled HTML card."""
    return (
        f'<div style="display:inline-block;background:{color};color:#fff;'
        f'padding:8px 12px;margin:4px;border-radius:8px;min-width:120px;'
        f'text-align:center;font-size:0.9em;">'
        f'<b>{song["title"]}</b><br>'
        f'<span style="opacity:0.85">{song["artist"]}</span><br>'
        f'{key}: {song[key]}'
        f'</div>'
    )


def render_step(step, i, total, key):
    """Render one algorithm step as an HTML panel."""
    left_html  = "".join(song_box(s, key, "#4c6ef5") for s in step["left"])
    right_html = "".join(song_box(s, key, "#ae3ec9") for s in step["right"])
    merge_html = "".join(song_box(s, key, "#2b8a3e") for s in step["merged"])

    return f"""
    <div style="padding:18px;background:#1a1a2e;color:#fff;border-radius:12px;
                margin-top:8px;font-family:sans-serif;">
        <div style="margin-bottom:10px;font-size:1.05em;">
            <b>Step {i + 1} / {total}</b> &nbsp;—&nbsp; {step['desc']}
        </div>
        <div style="margin-bottom:6px;">
            <span style="color:#a5b4fc;font-weight:600;">LEFT:</span><br>{left_html}
        </div>
        <div style="margin-bottom:6px;">
            <span style="color:#d8b4fe;font-weight:600;">RIGHT:</span><br>{right_html}
        </div>
        <div>
            <span style="color:#86efac;font-weight:600;">MERGED:</span><br>{merge_html}
        </div>
    </div>
    """


def render_final(songs, key):
    """The fully sorted playlist then becomes styled as an HTML table."""

    rows = "".join(
        f'<tr style="border-bottom:1px solid #e5e7eb;">'
        f'<td style="padding:8px;text-align:center;">{i + 1}</td>'
        f'<td style="padding:8px;">{s["title"]}</td>'
        f'<td style="padding:8px;">{s["artist"]}</td>'
        f'<td style="padding:8px;text-align:center;">{s[key]}</td>'
        f'</tr>'
        for i, s in enumerate(songs)
    )
    return (
        f'<table style="width:100%;border-collapse:collapse;font-family:sans-serif;'
        f'margin-top:8px;">'
        f'<thead><tr style="background:#4c6ef5;color:#fff;">'
        f'<th style="padding:10px;">#</th>'
        f'<th style="padding:10px;text-align:left;">Title</th>'
        f'<th style="padding:10px;text-align:left;">Artist</th>'
        f'<th style="padding:10px;">{key.capitalize()}</th>'
        f'</tr></thead>'
        f'<tbody>{rows}</tbody></table>'
    )


# ---------------------------------------------------------------------------
# Shared state (single-user / demo scope)
# ---------------------------------------------------------------------------

_state = {
    "steps": [],
    "index": 0,
    "key": "vibe",
    "final": [],
    "playing": False,
}

# ---------------------------------------------------------------------------
# Core callback functions
# ---------------------------------------------------------------------------

def run_sort(text, sort_key):
    """Reads the data, sort the songs, and show the starting step and final results."""

    songs = parse_songs(text)
    if isinstance(songs, str):
        return songs, "", "", gr.update(interactive=False), gr.update(interactive=False)

    key = "vibe" if "Vibe" in sort_key else "duration"
    steps, final = merge_sort_trace(songs, key)

    _state.update({"steps": steps, "index": 0, "key": key, "final": final})

    progress = f"Step 1 of {len(steps)}"
    return (
        f" Sorted {len(songs)} songs — {len(steps)} merge steps recorded. ({progress})",
        render_step(steps[0], 0, len(steps), key),
        render_final(final, key),
        gr.update(interactive=True),
        gr.update(interactive=True),
    )


def next_step():
    """Next step forward in the visualization."""
    if not _state["steps"]:
        return "", ""
    _state["index"] = min(len(_state["steps"]) - 1, _state["index"] + 1)
    i = _state["index"]
    return (
        render_step(_state["steps"][i], i, len(_state["steps"]), _state["key"]),
        render_final(_state["final"], _state["key"]),
    )


def prev_step():
    """Go back one step in the visualization."""
    if not _state["steps"]:
        return "", ""
    _state["index"] = max(0, _state["index"] - 1)
    i = _state["index"]
    return (
        render_step(_state["steps"][i], i, len(_state["steps"]), _state["key"]),
        render_final(_state["final"], _state["key"]),
    )


def autoplay(speed):
    """Handles the step-by-step playback for the auto-play mode."""
    if not _state["steps"]:
        yield "", ""
        return

    _state["playing"] = True

    while _state["index"] < len(_state["steps"]) and _state["playing"]:
        i = _state["index"]
        yield (
            render_step(_state["steps"][i], i, len(_state["steps"]), _state["key"]),
            render_final(_state["final"], _state["key"]),
        )
        time.sleep(speed)
        _state["index"] += 1

    _state["playing"] = False


def stop():
    """Stop auto-play."""
    _state["playing"] = False
    return "⏸ Stopped"


# ---------------------------------------------------------------------------
# Gradio UI — with theme + Row layout
# ---------------------------------------------------------------------------

with gr.Blocks(
    title="🎵 Playlist Vibe Builder",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(
        "# 🎵 Playlist Vibe Builder\n"
        "Sort your playlist by **Vibe** or **Duration** using Merge Sort, "
        "with a step-by-step visual simulation of every comparison and merge."
    )

    # ── Input section ───────────────────────────────────────────────────────
    with gr.Row():
        with gr.Column(scale=2):
            text = gr.Textbox(
                lines=10,
                label="Songs  (Title | Artist | Vibe | Duration)",
                placeholder="Paste songs or click Load Sample…",
            )
            with gr.Row():
                load_btn    = gr.Button("📂 Load Sample")
                shuffle_btn = gr.Button("🔀 Shuffle")

        with gr.Column(scale=1):
            key_radio = gr.Radio(
                ["Vibe ⚡", "Duration ⏱"],
                value="Vibe ⚡",
                label="Sort by",
            )
            sort_btn = gr.Button("▶️ Sort", variant="primary")
            speed_slider = gr.Slider(
                0.2, 2.0, value=0.8, step=0.1,
                label="Auto-play speed (seconds)",
            )
            status = gr.Textbox(label="Status", interactive=False)

    # ── Visualization section ───────────────────────────────────────────────
    gr.Markdown("---")
    gr.Markdown("### Step-by-Step Simulation")

    step_html  = gr.HTML()
    final_html = gr.HTML(label="Sorted Playlist")

    with gr.Row():
        prev_btn = gr.Button("⬅ Prev",     interactive=False)
        next_btn = gr.Button("Next ➡",      interactive=False)
        auto_btn = gr.Button("⏩ Auto Play")
        stop_btn = gr.Button("⏹ Stop")

    # ── Wiring ──────────────────────────────────────────────────────────────
    load_btn.click(
        lambda: songs_to_text(SAMPLE_SONGS),
        outputs=text,
    )
    shuffle_btn.click(
        lambda: songs_to_text(random.sample(SAMPLE_SONGS, len(SAMPLE_SONGS))),
        outputs=text,
    )

    sort_btn.click(
        run_sort,
        inputs=[text, key_radio],
        outputs=[status, step_html, final_html, prev_btn, next_btn],
    )

    prev_btn.click(prev_step, outputs=[step_html, final_html])
    next_btn.click(next_step, outputs=[step_html, final_html])

    auto_btn.click(autoplay, inputs=speed_slider, outputs=[step_html, final_html])
    stop_btn.click(stop, outputs=status)


# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch()
