import socket
import threading
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import simpledialog
from tkinter import messagebox

# server info
HOST = "127.0.0.1" #localhost
PORT = 5000

my_socket = None
my_name = ""
still_running = False

# emoji shortcuts
emoji_map = {
    ":thumbsup:": "\U0001F44D",
    ":smile:": "\U0001F604",
    ":heart:": "\U00002764",
    ":laughing:": "\U0001F606",
    ":sob:": "\U0001F62D",
}

fixing_emoji = False

dark_mode = True

# adds a message to the chat box
def add_message(text):
    chat_box.configure(state="normal")
    chat_box.insert(tk.END, text + "\n")
    chat_box.configure(state="disabled")
    # scroll down automatically
    chat_box.see(tk.END)


# runs in a thread and listens for incoming messages
def listen_for_messages():
    global still_running
    global my_socket

    while still_running:
        try:
            incoming = my_socket.recv(4096)

            if not incoming:
                # server disconnected
                still_running = False
                # update the gui from main thread
                window.after(0, lambda: add_message("\n*** server shut down ***"))
                window.after(3000, window.destroy)
                break

            msg = incoming.decode()
            # show it in the chat
            window.after(0, lambda m=msg: add_message(m))

        except OSError:
            break
        except Exception as e:
            if still_running:
                window.after(0, lambda: add_message("error: " + str(e)))
            break


def send_message(event=None):
    global my_socket

    # grab what the user typed
    text = input_box.get("1.0", "end-1c")
    text = text.strip()

    if text == "":
        return "break"

    # show emoji list
    if text == "/emoji" or text == ":":
        add_message("emoji shortcuts you can type:")
        for code in emoji_map:
            add_message("- " + code + " = " + emoji_map[code])
        input_box.delete("1.0", tk.END)
        return "break"

    # clear the chat box
    if text == "/clear":
        chat_box.configure(state="normal")
        chat_box.delete("1.0", tk.END)
        chat_box.configure(state="disabled")
        input_box.delete("1.0", tk.END)
        return "break"

    # if they typed a command dont show "You: /r ...."
    show_me = True
    if text.startswith("/r"):
        show_me = False
    if text == "/users":
        show_me = False

    # send it
    try:
        my_socket.sendall(text.encode())
    except Exception as e:
        add_message("couldn't send: " + str(e))
        return "break"

    # show it in our own chat window too
    if show_me:
        add_message("You: " + text)

    # clear the input box
    input_box.delete("1.0", tk.END)

    return "break"


def emoji_shortcuts(event=None):
    global fixing_emoji

    if fixing_emoji:
        return

    # grab text and replace shortcuts
    text = input_box.get("1.0", "end-1c")
    new_text = text

    for code in emoji_map:
        if code in new_text:
            new_text = new_text.replace(code, emoji_map[code])

    if new_text != text:
        fixing_emoji = True
        input_box.delete("1.0", tk.END)
        input_box.insert("1.0", new_text)
        input_box.mark_set(tk.INSERT, tk.END)
        fixing_emoji = False


def quit_chat():
    global still_running
    global my_socket

    still_running = False

    if my_socket:
        try:
            my_socket.sendall("/quit".encode())
        except:
            pass
        try:
            my_socket.close()
        except:
            pass

    window.destroy()


# build the window
window = tk.Tk()
window.title("Group Chat")
window.geometry("580x480")
window.minsize(520, 420)
window.configure(bg="#0f172a")

# styling
style = ttk.Style()
try:
    style.theme_use("clam")
except:
    pass
style.configure("Top.TFrame", background="#0f172a")
style.configure("Bottom.TFrame", background="#0b1220")
style.configure("Header.TLabel", background="#0f172a", foreground="#e5e7eb", font=("Segoe UI", 12, "bold"))
style.configure("Sub.TLabel", background="#0f172a", foreground="#9ca3af", font=("Segoe UI", 9))
style.configure("Send.TButton", padding=(12, 6))
style.configure("Quit.TButton", padding=(12, 6))

# switch theme colors
def apply_theme():
    if dark_mode:
        window.configure(bg="#0f172a")
        style.configure("Top.TFrame", background="#0f172a")
        style.configure("Bottom.TFrame", background="#0b1220")
        style.configure("Header.TLabel", background="#0f172a", foreground="#e5e7eb")
        style.configure("Sub.TLabel", background="#0f172a", foreground="#9ca3af")

        chat_box.configure(
            bg="#0b1220",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            highlightbackground="#243244",
            highlightcolor="#3b82f6"
        )
        input_box.configure(
            bg="#0a1020",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            highlightbackground="#243244",
            highlightcolor="#3b82f6"
        )

        theme_btn.configure(text="Light mode")
    else:
        window.configure(bg="#f3f4f6")
        style.configure("Top.TFrame", background="#f3f4f6")
        style.configure("Bottom.TFrame", background="#e5e7eb")
        style.configure("Header.TLabel", background="#f3f4f6", foreground="#111827")
        style.configure("Sub.TLabel", background="#f3f4f6", foreground="#374151")

        chat_box.configure(
            bg="white",
            fg="#111827",
            insertbackground="#111827",
            highlightbackground="#cbd5e1",
            highlightcolor="#2563eb"
        )
        input_box.configure(
            bg="white",
            fg="#111827",
            insertbackground="#111827",
            highlightbackground="#cbd5e1",
            highlightcolor="#2563eb"
        )

        theme_btn.configure(text="Dark mode")


def toggle_theme():
    global dark_mode
    dark_mode = not dark_mode
    apply_theme()


# top header
top = ttk.Frame(window, style="Top.TFrame")
top.pack(fill=tk.X, padx=10, pady=(10, 6))

header = ttk.Label(top, text="Group Chat", style="Header.TLabel")
header.pack(side=tk.LEFT)

sub = ttk.Label(top, text="Connected users can chat here", style="Sub.TLabel")
sub.pack(side=tk.RIGHT)

theme_btn = tk.Button(
    top,
    text="Light mode",
    command=toggle_theme,
    bd=0,
    padx=10,
    pady=4,
    font=("Segoe UI", 9),
    bg="#2563eb",
    fg="white",
    activebackground="#1d4ed8",
    activeforeground="white"
)
theme_btn.pack(side=tk.RIGHT, padx=(0, 8))

# chat display
chat_box = scrolledtext.ScrolledText(
    window,
    state="disabled",
    wrap=tk.WORD,
    font=("Segoe UI", 10),
    bg="#0b1220",
    fg="#e5e7eb",
    insertbackground="#e5e7eb",
    relief=tk.FLAT,
    bd=0,
    highlightthickness=1,
    highlightbackground="#243244",
    highlightcolor="#3b82f6",
    padx=8,
    pady=8,
    height=20
)
chat_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

# bottom frame holds input + buttons
bottom = ttk.Frame(window, style="Bottom.TFrame")
bottom.pack(fill=tk.X, padx=10, pady=(0, 10))

# text input
input_box = tk.Text(
    bottom,
    height=3,
    wrap=tk.WORD,
    font=("Segoe UI", 10),
    bg="#0a1020",
    fg="#e5e7eb",
    insertbackground="#e5e7eb",
    relief=tk.FLAT,
    bd=0
    ,
    highlightthickness=1,
    highlightbackground="#243244",
    highlightcolor="#3b82f6",
    padx=8,
    pady=6
)
input_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

# enter sends, shift+enter does a newline
input_box.bind("<Return>", send_message)
# input_box.bind("<Shift-Return>", lambda e: None)  # this might already work by default
input_box.bind("<KeyRelease>", emoji_shortcuts)

# apply theme once everything is created
apply_theme()

send_btn = ttk.Button(
    bottom,
    text="Send",
    command=send_message,
    style="Send.TButton"
)
send_btn.pack(side=tk.LEFT)

quit_btn = ttk.Button(
    bottom,
    text="Quit",
    command=quit_chat,
    style="Quit.TButton"
)
quit_btn.pack(side=tk.LEFT, padx=(6, 0))

window.protocol("WM_DELETE_WINDOW", quit_chat)


# connect to the server
def start():
    global my_socket, my_name, still_running

    # ask for name
    name = simpledialog.askstring("name", "what is your name?", parent=window)

    if name is None or name.strip() == "":
        messagebox.showerror("error", "you need a name")
        window.destroy()
        return

    my_name = name.strip()
    window.title("Group Chat - " + my_name)

    # try to connect
    try:
        my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_socket.connect((HOST, PORT))
    except:
        messagebox.showerror("error", "could not connect to server\nis server.py running?")
        window.destroy()
        return

    # send name to server
    try:
        my_socket.sendall(my_name.encode())
    except:
        messagebox.showerror("error", "server closed the connection")
        try:
            my_socket.close()
        except:
            pass
        window.destroy()
        return

    still_running = True

    add_message("connected! you are: " + my_name)
    add_message("press Enter to send a message")
    add_message("help:")
    add_message("- @username message  (direct message)")
    add_message("- /r message         (reply to last dm)")
    add_message("- /emoji             (emoji list)")
    add_message("- /clear             (clear chat)")
    add_message("- /users             (show users connected)")
    add_message("- /quit              (quit)\n")

    # start background listener thread
    t = threading.Thread(target=listen_for_messages)
    t.daemon = True
    t.start()


# run start once the window is ready
window.after(100, start)

# start the gui loop
window.mainloop()
