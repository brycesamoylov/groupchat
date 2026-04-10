# Group Chat (CIS 457)

This is a simple group chat app with a Python socket server (`server.py`) and a Tkinter client (`client.py`).

## Chat server design (`server.py`)

**Data structures**
- `client_list`: a list of all connected clients. Each item is `(socket, name)`.
- `lock`: a `threading.Lock()` so different threads don’t mess up the list at the same time.
- `last_dm_from`: a dictionary used for `/r` replies. Key is the client socket, value is the last person you were DMing (or the last person who DM’d you).

**Main operations**
- **Accept connections**: the server listens on a port and `accept()`s new clients.
- **Per-client thread**: each new connection starts a thread that runs `handle_one_client()`.
- **Join flow**: the first thing the client sends is their name, which gets stored in `client_list`.
- **Broadcast**: normal messages get sent to everyone else with `send_to_everyone()`.
- **Direct message**: messages that start with `@username ...` only go to that user.
- **Reply to DM**: `/r ...` replies to the last DM partner.
- **Users list**: `/users` sends back a list of connected usernames.
- **Quit**: `/quit` closes that client connection.
- **Stopping the server**: `Ctrl+C` exits the accept loop and closes the server socket.

## Chat client design (`client.py`)

**GUI**
- Tkinter window with:
  - a scrollable chat area (`ScrolledText`) for messages
  - a text box for typing messages
  - buttons for Send / Quit
  - a Light/Dark mode toggle button

**Networking**
- Connects to the server using `socket`.
- Sends your name once after connecting.
- Uses a background thread (`listen_for_messages`) so the GUI doesn’t freeze while waiting for messages.

**Client-side commands/features**
- **Emoji shortcuts**: typing things like `:thumbsup:` turns into the emoji in the input box.
- **`/emoji`** (or just `:`): prints the available emoji shortcuts to the chat window.
- **`/clear`**: clears the chat window on your screen.
- **DMs**: type `@username message` to DM someone (server handles it).
- **`/r`**: replies to your last DM partner (server handles it).
- **`/users`**: asks the server for the list of users.
- **`/quit`**: quits (client sends it to the server and closes).

## Team responsibilities + coordination

I worked on this by myself so I didn't have a team. I prioritized haveing a working server and then built the GUI around it adding features that I thought would be useful and basic things that I would want in a chat. 


