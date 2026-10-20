
import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import threading
import queue
import time
from pathlib import Path
from typing import Optional


# ==================================================
# 1. PROJECT SETTINGS
# ==================================================

PROJECT_FOLDER = Path(__file__).parent
CONTROLLER_FILE = PROJECT_FOLDER / "hand_tracking.py"

IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # The controller is shipped beside the GUI executable.
    CONTROLLER_EXE = (
        Path(sys.executable).parent
        / "GesturePointController"
        / "GesturePointController.exe"
    )

    # Match the stop-signal location used by the packaged controller.
    STOP_FILE = (
        CONTROLLER_EXE.parent
        / "_internal"
        / "stop_controller.signal"
    )
else:
    CONTROLLER_EXE = None
    STOP_FILE = PROJECT_FOLDER / "stop_controller.signal"


controller_process = None
output_queue = queue.Queue()

stopping = False
closing_application = False
stop_requested_at = None
shutdown_timeout_stage = 0

controller_output_lines = []
error_reported_for = None

GRACEFUL_STOP_TIMEOUT = 5
FORCED_STOP_TIMEOUT = 2


# ==================================================
# 2. COLOURS
# ==================================================

BACKGROUND = "#F3F6FC"
WHITE = "#FFFFFF"
NAVY = "#172B4D"
BLUE = "#2563EB"
BLUE_HOVER = "#1D4ED8"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#D97706"
TEXT = "#25324B"
MUTED = "#64748B"
BORDER = "#E2E8F0"
LIGHT_BLUE = "#EFF6FF"
LIGHT_GREEN = "#F0FDF4"
LIGHT_RED = "#FEF2F2"


# ==================================================
# 3. MAIN WINDOW
# ==================================================

root = tk.Tk()
root.title("GesturePoint Desktop")
root.geometry("820x650")
root.minsize(680, 580)
root.configure(bg=BACKGROUND)


# ==================================================
# 4. APPLICATION STATE
# ==================================================

camera_status = tk.StringVar(value="Not started")
gesture_status = tk.StringVar(value="Waiting to start")
current_gesture = tk.StringVar(value="—")
activity_text = tk.StringVar(value="Controller is idle")

activity_running = False
activity_frame = 0

start_button: Optional[tk.Button] = None
stop_button: Optional[tk.Button] = None
activity_canvas: Optional[tk.Canvas] = None
activity_dot: Optional[int] = None
main_status_badge: Optional[tk.Label] = None

status_badge_text: Optional[tk.Label] = None
gesture_icon_label: Optional[tk.Label] = None


# ==================================================
# 5. BACKGROUND OUTPUT READER
# ==================================================

def read_controller_output(process):
    """Read controller output without freezing the GUI."""
    try:
        if process.stdout is not None:
            for line in process.stdout:
                output_queue.put((process, line.rstrip()))

    except (OSError, ValueError) as error:
        output_queue.put(
            (process, f"OUTPUT_READER_ERROR: {error}")
        )

    finally:
        if process.stdout is not None:
            try:
                process.stdout.close()
            except OSError:
                pass


# ==================================================
# 6. GUI HELPERS
# ==================================================

def set_badge(text, colour, background):
    """Update the main controller status badge."""
    if status_badge_text is None:
        return

    status_badge_text.configure(
        text=text,
        fg=colour,
        bg=background
    )


def set_buttons(start_enabled, stop_enabled):
    """Enable or disable the control buttons."""
    if start_button is not None:
        if start_enabled:
            start_button.configure(
                state="normal",
                bg=BLUE,
                cursor="hand2"
            )
        else:
            start_button.configure(
                state="disabled",
                bg="#94A3B8",
                cursor="arrow"
            )

    if stop_button is not None:
        if stop_enabled:
            stop_button.configure(
                state="normal",
                bg=RED,
                cursor="hand2"
            )
        else:
            stop_button.configure(
                state="disabled",
                bg="#CBD5E1",
                cursor="arrow"
            )


# ==================================================
# 7. LIVE ACTIVITY INDICATOR
# ==================================================

def animate_activity():
    """Animate the indicator while tracking is active."""
    global activity_frame

    if not root.winfo_exists() or not activity_running:
        return

    if activity_canvas is None or activity_dot is None:
        return

    activity_frame = (activity_frame + 1) % 2
    colour = GREEN if activity_frame == 0 else "#86EFAC"

    activity_canvas.itemconfigure(
        activity_dot,
        fill=colour
    )

    root.after(550, animate_activity)


def start_activity():
    """Start the live activity animation."""
    global activity_running

    if activity_running:
        return

    activity_running = True
    activity_text.set("Controller is active")
    animate_activity()


def stop_activity():
    """Stop the live activity animation."""
    global activity_running

    activity_running = False

    if activity_canvas is not None and activity_dot is not None:
        activity_canvas.itemconfigure(
            activity_dot,
            fill="#CBD5E1"
        )

    activity_text.set("Controller is idle")


# ==================================================
# 8. GESTURE DISPLAY
# ==================================================

def update_gesture(gesture):
    """Display a readable name for the detected gesture."""
    gesture_names = {
        "NO_HAND": ("No hand detected", "○"),
        "open_palm": ("Open palm", "✋"),
        "fist": ("Fist", "✊"),
        "pinch": ("Pinch", "👌")
    }

    readable_name, symbol = gesture_names.get(
        gesture,
        (gesture.replace("_", " ").title(), "○")
    )

    current_gesture.set(readable_name)

    if gesture_icon_label is not None:
        gesture_icon_label.configure(text=symbol)

    if gesture == "NO_HAND":
        gesture_status.set("Waiting for a hand")
    else:
        gesture_status.set("Gesture recognised")


# ==================================================
# 9. ERROR REPORTING
# ==================================================

def show_controller_error(process):
    """Show controller output after an unexpected failure."""
    global error_reported_for

    if error_reported_for is process:
        return

    error_reported_for = process

    exit_code = process.returncode

    useful_lines = [
        line for line in controller_output_lines
        if line
        and line != "CONTROLLER_STOPPED"
        and not line.startswith("GESTURE:")
        and not line.startswith("OUTPUT_READER_ERROR:")
    ]

    recent_output = "\n".join(useful_lines[-12:])

    if not recent_output:
        recent_output = (
            "The controller exited without providing an error message."
        )

    messagebox.showerror(
        "GesturePoint Controller Error",
        f"The controller stopped unexpectedly.\n\n"
        f"Exit code: {exit_code}\n\n"
        f"Recent controller output:\n\n{recent_output}",
        parent=root
    )


# ==================================================
# 10. PROCESS CONTROLLER MESSAGES
# ==================================================

def process_controller_messages():
    global controller_process
    global stopping
    global stop_requested_at
    global shutdown_timeout_stage

    try:
        while True:
            process, message = output_queue.get_nowait()

            # Ignore messages from a previous controller.
            if process is not controller_process:
                continue

            if message.startswith("GESTURE:"):
                gesture = message.split(":", 1)[1].strip()
                update_gesture(gesture)

            elif message == "CONTROLLER_STOPPED":
                camera_status.set("Stopped")
                gesture_status.set("Gesture recognition stopped")
                update_gesture("NO_HAND")

            elif message.startswith("OUTPUT_READER_ERROR:"):
                controller_output_lines.append(message)

            elif message:
                controller_output_lines.append(message)

    except queue.Empty:
        pass

    # Check whether the controller has exited.
    if controller_process is not None:
        exit_code = controller_process.poll()

        if exit_code is not None:
            finished_process = controller_process
            was_stopping = stopping

            controller_process = None
            stopping = False
            stop_requested_at = None
            shutdown_timeout_stage = 0

            stop_activity()
            set_buttons(True, False)

            camera_status.set("Stopped")
            gesture_status.set("Gesture recognition stopped")
            update_gesture("NO_HAND")

            set_badge(
                "STOPPED",
                MUTED,
                "#F1F5F9"
            )

            if STOP_FILE.exists():
                try:
                    STOP_FILE.unlink()
                except OSError:
                    pass

            if closing_application:
                root.destroy()
                return

            if exit_code != 0 and not was_stopping:
                set_badge(
                    "ERROR",
                    RED,
                    LIGHT_RED
                )

                activity_text.set(
                    "Controller encountered an error"
                )

                show_controller_error(finished_process)

    # Graceful shutdown with timeout fallback.
    if (
        controller_process is not None
        and stopping
        and stop_requested_at is not None
    ):
        elapsed = time.monotonic() - stop_requested_at

        if (
            shutdown_timeout_stage == 0
            and elapsed >= GRACEFUL_STOP_TIMEOUT
        ):
            camera_status.set("Requesting forced shutdown...")

            try:
                controller_process.terminate()
                shutdown_timeout_stage = 1
                stop_requested_at = time.monotonic()

            except OSError as error:
                print(f"Could not terminate controller: {error}")

        elif (
            shutdown_timeout_stage == 1
            and elapsed >= FORCED_STOP_TIMEOUT
            and controller_process.poll() is None
        ):
            camera_status.set("Ending unresponsive controller...")

            try:
                controller_process.kill()
                shutdown_timeout_stage = 2

            except OSError as error:
                print(f"Could not kill controller: {error}")

    root.after(100, process_controller_messages)


# ==================================================
# 11. START CONTROL
# ==================================================

def start_control():
    global controller_process
    global stopping
    global stop_requested_at
    global shutdown_timeout_stage
    global controller_output_lines
    global error_reported_for

    if closing_application:
        return

    if controller_process is not None:
        if controller_process.poll() is None:
            messagebox.showinfo(
                "Already Running",
                "GesturePoint is already running.",
                parent=root
            )
            return

        controller_process = None

    # Select the correct controller for the current mode.
    if IS_FROZEN:
        controller_path = CONTROLLER_EXE
        controller_exists = (
            controller_path is not None
            and controller_path.is_file()
        )
    else:
        controller_path = CONTROLLER_FILE
        controller_exists = controller_path.is_file()

    if not controller_exists:
        messagebox.showerror(
            "File Not Found",
            f"Could not find the controller:\n\n{controller_path}",
            parent=root
        )
        return

    # Clear a leftover stop signal.
    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()

        except OSError as error:
            messagebox.showerror(
                "Startup Error",
                f"Could not clear the stop signal:\n\n{error}",
                parent=root
            )
            return

    controller_output_lines = []
    error_reported_for = None

    try:
        if IS_FROZEN:
            assert CONTROLLER_EXE is not None
            command = [str(CONTROLLER_EXE)]
            controller_working_folder = CONTROLLER_EXE.parent
        else:
            command = [sys.executable, str(CONTROLLER_FILE)]
            controller_working_folder = PROJECT_FOLDER

        new_process = subprocess.Popen(
            command,
            cwd=str(controller_working_folder),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        controller_process = new_process

        threading.Thread(
            target=read_controller_output,
            args=(new_process,),
            daemon=True
        ).start()

        stopping = False
        stop_requested_at = None
        shutdown_timeout_stage = 0

        camera_status.set("Starting controller...")
        gesture_status.set("Initialising gesture recognition...")
        update_gesture("NO_HAND")

        set_badge(
            "STARTING",
            AMBER,
            "#FFFBEB"
        )

        activity_text.set("Preparing the controller")
        set_buttons(False, True)

    except (OSError, ValueError) as error:
        controller_process = None

        stop_activity()
        camera_status.set("Failed to start")
        gesture_status.set("Gesture recognition stopped")

        set_badge(
            "ERROR",
            RED,
            LIGHT_RED
        )

        set_buttons(True, False)

        messagebox.showerror(
            "Startup Error",
            f"Could not start GesturePoint.\n\n{error}",
            parent=root
        )


# ==================================================
# 12. STOP CONTROL
# ==================================================

def stop_control():
    global stopping
    global stop_requested_at
    global shutdown_timeout_stage

    if controller_process is None:
        camera_status.set("Stopped")
        gesture_status.set("Gesture recognition stopped")
        update_gesture("NO_HAND")

        stop_activity()
        set_badge("STOPPED", MUTED, "#F1F5F9")
        set_buttons(True, False)
        return

    if controller_process.poll() is not None:
        return

    if stopping:
        return

    stopping = True
    stop_requested_at = time.monotonic()
    shutdown_timeout_stage = 0

    camera_status.set("Stopping controller...")
    gesture_status.set("Gesture recognition stopping")

    set_badge(
        "STOPPING",
        AMBER,
        "#FFFBEB"
    )

    stop_activity()
    set_buttons(False, False)

    try:
        STOP_FILE.touch(exist_ok=True)

    except OSError as error:
        stopping = False
        stop_requested_at = None

        messagebox.showerror(
            "Stop Error",
            f"Could not send the stop signal:\n\n{error}",
            parent=root
        )


# ==================================================
# 13. MODERN HEADER
# ==================================================

header = tk.Frame(
    root,
    bg=NAVY,
    padx=28,
    pady=22
)
header.pack(fill="x")

header_top = tk.Frame(header, bg=NAVY)
header_top.pack(fill="x")

tk.Label(
    header_top,
    text="GesturePoint",
    font=("Segoe UI", 23, "bold"),
    fg=WHITE,
    bg=NAVY
).pack(side="left")

tk.Label(
    header_top,
    text="DESKTOP",
    font=("Segoe UI", 9, "bold"),
    fg="#BFDBFE",
    bg="#29446D",
    padx=10,
    pady=5
).pack(side="left", padx=12, pady=5)

tk.Label(
    header,
    text="Hands-free mouse control powered by machine learning",
    font=("Segoe UI", 10),
    fg="#CBD5E1",
    bg=NAVY
).pack(anchor="w", pady=(7, 0))


# ==================================================
# 14. MAIN CONTENT
# ==================================================

content = tk.Frame(
    root,
    bg=BACKGROUND,
    padx=28,
    pady=22
)
content.pack(fill="both", expand=True)

section_header = tk.Frame(content, bg=BACKGROUND)
section_header.pack(fill="x", pady=(0, 14))

tk.Label(
    section_header,
    text="Control centre",
    font=("Segoe UI", 17, "bold"),
    fg=TEXT,
    bg=BACKGROUND
).pack(side="left")

tk.Label(
    section_header,
    text="LIVE SYSTEM",
    font=("Segoe UI", 9, "bold"),
    fg=BLUE,
    bg=BACKGROUND
).pack(side="right", pady=7)


# ==================================================
# 15. CONTROLLER STATUS CARD
# ==================================================

status_card = tk.Frame(
    content,
    bg=WHITE,
    padx=20,
    pady=18,
    highlightbackground=BORDER,
    highlightthickness=1
)
status_card.pack(fill="x")

status_top = tk.Frame(status_card, bg=WHITE)
status_top.pack(fill="x")

tk.Label(
    status_top,
    text="Controller status",
    font=("Segoe UI", 11, "bold"),
    fg=TEXT,
    bg=WHITE
).pack(side="left")

status_badge_text = tk.Label(
    status_top,
    text="STOPPED",
    font=("Segoe UI", 9, "bold"),
    fg=MUTED,
    bg="#F1F5F9",
    padx=11,
    pady=5
)
status_badge_text.pack(side="right")

tk.Label(
    status_card,
    textvariable=camera_status,
    font=("Segoe UI", 12),
    fg=TEXT,
    bg=WHITE
).pack(anchor="w", pady=(14, 5))

tk.Label(
    status_card,
    textvariable=gesture_status,
    font=("Segoe UI", 10),
    fg=MUTED,
    bg=WHITE
).pack(anchor="w")


# ==================================================
# 16. CURRENT GESTURE CARD
# ==================================================

gesture_card = tk.Frame(
    content,
    bg=WHITE,
    padx=20,
    pady=18,
    highlightbackground=BORDER,
    highlightthickness=1
)
gesture_card.pack(fill="x", pady=(14, 0))

tk.Label(
    gesture_card,
    text="CURRENT GESTURE",
    font=("Segoe UI", 9, "bold"),
    fg=MUTED,
    bg=WHITE
).pack(anchor="w")

gesture_display = tk.Frame(gesture_card, bg=WHITE)
gesture_display.pack(fill="x", pady=(10, 4))

gesture_icon_label = tk.Label(
    gesture_display,
    text="○",
    font=("Segoe UI Emoji", 29),
    fg=BLUE,
    bg=WHITE,
    width=3
)
gesture_icon_label.pack(side="left")

tk.Label(
    gesture_display,
    textvariable=current_gesture,
    font=("Segoe UI", 19, "bold"),
    fg=TEXT,
    bg=WHITE
).pack(side="left", padx=(8, 0))


# ==================================================
# 17. LIVE ACTIVITY CARD
# ==================================================

activity_card = tk.Frame(
    content,
    bg=LIGHT_BLUE,
    padx=16,
    pady=12
)
activity_card.pack(fill="x", pady=(14, 0))

activity_row = tk.Frame(activity_card, bg=LIGHT_BLUE)
activity_row.pack(fill="x")

activity_canvas = tk.Canvas(
    activity_row,
    width=18,
    height=18,
    bg=LIGHT_BLUE,
    highlightthickness=0
)
activity_canvas.pack(side="left", padx=(0, 8))

activity_dot = activity_canvas.create_oval(
    3, 3, 15, 15,
    fill="#CBD5E1",
    outline=""
)

tk.Label(
    activity_row,
    textvariable=activity_text,
    font=("Segoe UI", 10, "bold"),
    fg=TEXT,
    bg=LIGHT_BLUE
).pack(side="left")


# ==================================================
# 18. CONTROL BUTTONS
# ==================================================

button_frame = tk.Frame(content, bg=BACKGROUND)
button_frame.pack(fill="x", pady=18)

start_button = tk.Button(
    button_frame,
    text="▶   Start Control",
    command=start_control,
    font=("Segoe UI", 11, "bold"),
    bg=BLUE,
    fg=WHITE,
    activebackground=BLUE_HOVER,
    activeforeground=WHITE,
    disabledforeground=WHITE,
    relief="flat",
    cursor="hand2",
    padx=18,
    pady=12,
    bd=0
)
start_button.pack(
    side="left",
    expand=True,
    fill="x",
    padx=(0, 7)
)

stop_button = tk.Button(
    button_frame,
    text="■   Stop Control",
    command=stop_control,
    font=("Segoe UI", 11, "bold"),
    bg="#CBD5E1",
    fg=WHITE,
    activebackground="#B91C1C",
    activeforeground=WHITE,
    disabledforeground=WHITE,
    relief="flat",
    cursor="arrow",
    padx=18,
    pady=12,
    bd=0,
    state="disabled"
)
stop_button.pack(
    side="left",
    expand=True,
    fill="x",
    padx=(7, 0)
)


# ==================================================
# 19. SAFETY NOTE
# ==================================================

safety_card = tk.Frame(
    content,
    bg="#FFFBEB",
    padx=15,
    pady=12
)
safety_card.pack(fill="x")

tk.Label(
    safety_card,
    text="SAFETY NOTE",
    font=("Segoe UI", 9, "bold"),
    fg="#92400E",
    bg="#FFFBEB"
).pack(anchor="w")

tk.Label(
    safety_card,
    text=(
        "Pinching triggers a left mouse click. Keep your hand visible "
        "and use Stop Control before closing the application."
    ),
    font=("Segoe UI", 9),
    fg="#92400E",
    bg="#FFFBEB",
    justify="left",
    wraplength=690
).pack(anchor="w", pady=(4, 0))


# ==================================================
# 20. SAFE APPLICATION CLOSURE
# ==================================================

def close_application():
    global closing_application

    if closing_application:
        return

    if (
        controller_process is not None
        and controller_process.poll() is None
    ):
        closing_application = True
        stop_control()
        wait_for_shutdown()
    else:
        root.destroy()


def wait_for_shutdown():
    if not root.winfo_exists():
        return

    if (
        controller_process is None
        or controller_process.poll() is not None
    ):
        root.destroy()
        return

    root.after(100, wait_for_shutdown)


# ==================================================
# 21. RUN THE APPLICATION
# ==================================================

root.protocol("WM_DELETE_WINDOW", close_application)

root.after(100, process_controller_messages)
root.mainloop()
