import subprocess
import sys
import os
import ctypes
import threading
import time
import random

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

dependencies = ["pyautogui", "pillow", "keyboard", "pywin32"]

for package in dependencies:
    try:
        __import__(package)
    except ImportError:
        print(f"[+] Installing missing package: {package}")
        install(package)

import pyautogui
import tkinter as tk
from PIL import Image, ImageTk
import PIL
import keyboard

# Pillow resize compatibility
resample_filter = PIL.Image.Resampling.LANCZOS if hasattr(PIL.Image, 'Resampling') else PIL.Image.ANTIALIAS

goose_active = True

# --- Get original wallpaper path ---
def get_current_wallpaper():
    SPI_GETDESKWALLPAPER = 0x0073
    buffer_size = 260
    buffer = ctypes.create_unicode_buffer(buffer_size)
    ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, buffer_size, buffer, 0)
    return buffer.value

original_wallpaper = get_current_wallpaper()

# --- Toggle desktop icons ---
def toggle_desktop_icons(show=True):
    try:
        import win32gui, win32con
    except ImportError:
        print("pywin32 is required for toggling desktop icons.")
        return False

    def find_shelldll_defview():
        progman = win32gui.FindWindow("Progman", None)
        defview = None
        defview = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
        if defview:
            return defview

        def enum_windows(hwnd, results):
            if win32gui.GetClassName(hwnd) == "WorkerW":
                child = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
                if child:
                    results.append(child)
        results = []
        win32gui.EnumWindows(enum_windows, results)
        if results:
            return results[0]
        return None

    defview = find_shelldll_defview()
    if not defview:
        print("Could not find desktop SHELLDLL_DefView window.")
        return False

    listview = win32gui.FindWindowEx(defview, 0, "SysListView32", "FolderView")
    if listview == 0:
        print("Could not find desktop ListView window.")
        return False

    win32gui.ShowWindow(listview, win32con.SW_SHOW if show else win32con.SW_HIDE)
    return True

# --- Change wallpaper ---
def change_wallpaper():
    path = os.path.abspath("goose_wallpaper.jpg")
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)

# --- Restore system (icons + wallpaper) ---
def restore_system(root=None):
    global goose_active
    goose_active = False
    toggle_desktop_icons(True)
    if original_wallpaper and os.path.exists(original_wallpaper):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, original_wallpaper, 3)
    else:
        print("[!] Could not find original wallpaper to restore.")
    if root:
        root.destroy()

# --- Screen flicker ---
def flicker_screen():
    while goose_active:
        if random.random() < 0.1:
            flicker = tk.Toplevel()
            flicker.overrideredirect(True)
            flicker.attributes("-topmost", True)
            flicker.geometry(f"{flicker.winfo_screenwidth()}x{flicker.winfo_screenheight()}+0+0")
            flicker.configure(bg="black")
            flicker.lift()
            flicker.after(300, flicker.destroy)
        time.sleep(random.randint(5, 10))

# --- Popup spam ---
def spawn_popup():
    screen_width, screen_height = pyautogui.size()
    popup_width, popup_height = 350, 120
    pos_x = (screen_width - popup_width) // 2
    pos_y = (screen_height - popup_height) // 2
    while goose_active:
        win = tk.Toplevel()
        win.title("System Warning")
        win.geometry(f"{popup_width}x{popup_height}+{pos_x}+{pos_y}")
        tk.Label(win, text="WHOOPS YOUR FILES ARE ENCRYPTED", fg="red", font=("Arial", 14, "bold")).pack(expand=True)
        win.after(3000, win.destroy)
        time.sleep(random.randint(3, 6))

# --- Goose walks randomly ---
def goose_walk(canvas, goose_img):
    x = random.randint(0, canvas.winfo_screenwidth() - 100)
    y = random.randint(0, canvas.winfo_screenheight() - 100)
    dx = random.choice([-5, -4, -3, 3, 4, 5])
    dy = random.choice([-5, -4, -3, 3, 4, 5])
    img = canvas.create_image(x, y, image=goose_img, anchor='nw')
    while goose_active:
        x += dx
        y += dy
        width = canvas.winfo_screenwidth()
        height = canvas.winfo_screenheight()

        if x <= 0 or x >= width - 100:
            dx = -dx
            x = max(0, min(x, width - 100))
        if y <= 0 or y >= height - 100:
            dy = -dy
            y = max(0, min(y, height - 100))

        canvas.coords(img, x, y)
        time.sleep(0.05)

# --- Mouse moves slightly ---
def goose_mouse_move():
    while goose_active:
        pyautogui.moveRel(random.randint(-15, 15), random.randint(-15, 15), duration=0.2)
        time.sleep(1.5)

# --- Mouse drags randomly ---
def mouse_drag_to_random():
    while goose_active:
        screen_width, screen_height = pyautogui.size()
        target_x = random.randint(0, screen_width)
        target_y = random.randint(0, screen_height)
        duration = random.uniform(0.5, 1.5)
        pyautogui.moveTo(target_x, target_y, duration=duration)
        time.sleep(random.randint(4, 8))

# --- Fake icons run from mouse ---
def icons_run_from_mouse(canvas, fake_icons):
    while goose_active:
        mouse_x, mouse_y = pyautogui.position()
        for icon_img_id, label_id in fake_icons:
            coords = canvas.coords(icon_img_id)
            if coords:
                icon_x, icon_y = coords[0], coords[1]
                distance = ((mouse_x - icon_x)**2 + (mouse_y - icon_y)**2) ** 0.5
                if distance < 120:
                    dx = (icon_x - mouse_x) / distance * 50
                    dy = (icon_y - mouse_y) / distance * 50
                    canvas.move(icon_img_id, dx, dy)
                    canvas.move(label_id, dx, dy)
        time.sleep(0.05)

# --- Listen for "die goose" or ESC to exit ---
def listen_for_exit(root=None):
    global goose_active
    typed = ""
    target = "die goose"
    while goose_active:
        for char in target:
            while goose_active:
                if keyboard.is_pressed(char):
                    typed += char
                    break
                elif keyboard.is_pressed("esc"):
                    restore_system(root)
                    return
                time.sleep(0.05)
        if typed == target:
            print("[+] 'die goose' detected. Shutting down...")
            restore_system(root)
            return
        else:
            typed = ""
        time.sleep(0.1)

# --- Countdown timer and fake BSOD ---
def show_timer(canvas, root):
    time.sleep(30)
    total_seconds = 180

    timer_text = canvas.create_text(
        canvas.winfo_screenwidth() - 10, 10,
        text="",
        fill="red",
        font=("Arial", 16, "bold"),
        anchor='ne'
    )

    while goose_active and total_seconds >= 0:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        canvas.itemconfigure(timer_text, text=f"YOUR PC WILL TURN INTO A BEAN IN {minutes}:{seconds:02}")
        time.sleep(1)
        total_seconds -= 1

    if goose_active:
        bsod = Image.open("bsod.png")
        bsod = bsod.resize((canvas.winfo_screenwidth(), canvas.winfo_screenheight()), resample_filter)
        bsod_tk = ImageTk.PhotoImage(bsod)
        
        bsod_screen = tk.Toplevel()
        bsod_screen.overrideredirect(True)
        bsod_screen.geometry(f"{canvas.winfo_screenwidth()}x{canvas.winfo_screenheight()}+0+0")
        bsod_label = tk.Label(bsod_screen, image=bsod_tk)
        bsod_label.pack()
        bsod_screen.lift()
        bsod_screen.attributes("-topmost", True)
        bsod_screen.update()

        time.sleep(4)

        bsod_screen.destroy()
        blackout = tk.Toplevel()
        blackout.overrideredirect(True)
        blackout.geometry(f"{canvas.winfo_screenwidth()}x{canvas.winfo_screenheight()}+0+0")
        blackout.configure(bg="black")
        blackout.lift()
        blackout.attributes("-topmost", True)
        blackout.update()

        time.sleep(5)

        blackout.destroy()
        restore_system(root)

# --- Main ---
def main():
    global goose_active

    toggle_desktop_icons(False)
    change_wallpaper()

    root = tk.Tk()
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")
    root.config(bg='white')
    root.wm_attributes("-transparentcolor", "white")

    canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight(), bg='white', highlightthickness=0)
    canvas.pack()

    goose_img = Image.open("goose.png").resize((100, 100), resample_filter)
    goose_img_tk = ImageTk.PhotoImage(goose_img)

    goose_icon_img = Image.open("goose.png").resize((48, 48), resample_filter)
    goose_icon_tk = ImageTk.PhotoImage(goose_icon_img)

    fake_icons = []
    cols = 5
    rows = 2
    start_x, start_y = 50, 100
    gap_x, gap_y = 100, 100

    for row in range(rows):
        for col in range(cols):
            x = start_x + col * gap_x
            y = start_y + row * gap_y
            icon_img_id = canvas.create_image(x, y, image=goose_icon_tk, anchor='nw')
            label_id = canvas.create_text(x + 24, y + 60, text="GOOSE", font=("Arial", 10), fill="white")
            fake_icons.append((icon_img_id, label_id))

    threading.Thread(target=spawn_popup, daemon=True).start()
    threading.Thread(target=goose_mouse_move, daemon=True).start()
    threading.Thread(target=mouse_drag_to_random, daemon=True).start()
    threading.Thread(target=listen_for_exit, args=(root,), daemon=True).start()
    threading.Thread(target=flicker_screen, daemon=True).start()
    threading.Thread(target=goose_walk, args=(canvas, goose_img_tk), daemon=True).start()
    threading.Thread(target=icons_run_from_mouse, args=(canvas, fake_icons), daemon=True).start()
    threading.Thread(target=show_timer, args=(canvas, root), daemon=True).start()

    def check_goose():
        if goose_active:
            root.after(100, check_goose)
        else:
            root.destroy()

    check_goose()
    root.mainloop()

if __name__ == "__main__":
    main()
