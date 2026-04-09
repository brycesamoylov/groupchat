import socket
import threading

# list of all clients connected
# each one is (socket, name)
client_list = []

# lock so threads dont mess each other up
lock = threading.Lock()

# for /r reply to last dm
# key is the client socket, value is the last person they dm'd (or who dm'd them)
last_dm_from = {}

# maybe add a max clients limit later?
# MAX_CLIENTS = 10


def send_to_everyone(msg, not_this_one=None):
    # go through every client and send the message
    # skip the one who sent it
    lock.acquire()
    everyone = list(client_list)
    lock.release()

    for c in everyone:
        sock = c[0]
        # name = c[1]
        if sock != not_this_one:
            try:
                sock.sendall(msg.encode())
            except:
                # if it fails just ignore it
                kick_client(sock)


def kick_client(sock):
    lock.acquire()
    for i in range(len(client_list)):
        if client_list[i][0] == sock:
            client_list.pop(i)
            lock.release()
            return
    lock.release()


def send_to_one_person(who_to_dm, msg, also_this_sock=None):
    # send a message to just one person by name (dm)
    lock.acquire()
    everyone = list(client_list)
    lock.release()

    for c in everyone:
        sock = c[0]
        name = c[1]
        if name == who_to_dm:
            try:
                sock.sendall(msg.encode())
            except:
                kick_client(sock)
            return True

    # optionally tell the sender too
    if also_this_sock:
        try:
            also_this_sock.sendall(msg.encode())
        except:
            pass

    return False


def get_all_usernames():
    lock.acquire()
    everyone = list(client_list)
    lock.release()

    names = []
    for c in everyone:
        names.append(c[1])
    return names


def handle_one_client(sock, address):
    print("someone connected: " + str(address))

    name = ""

    try:
        # get their name first
        data = sock.recv(1024)
        name = data.decode()
        name = name.strip()

        # add them to the list
        lock.acquire()
        client_list.append((sock, name))
        lock.release()

        print(name + " joined")

        # tell that [name] joined
        send_to_everyone("*** " + name + " joined the chat ***", not_this_one=sock)

        # keep reading messages
        while True:
            data = sock.recv(4096)

            if not data:
                break

            msg = data.decode()
            msg = msg.strip()

            # check if they said /quit
            if msg == "/quit":
                break

            # show users list (/users)
            if msg == "/users":
                names = get_all_usernames()
                try:
                    sock.sendall(("users (" + str(len(names)) + "): " + ", ".join(names)).encode())
                except:
                    pass
                continue

            # reply to last dm: /r message here
            if msg.startswith("/r"):
                dm_msg = msg[2:].strip()

                if dm_msg == "":
                    try:
                        sock.sendall("server: usage is /r message".encode())
                    except:
                        pass
                    continue

                who_to_dm = None
                if sock in last_dm_from:
                    who_to_dm = last_dm_from[sock]

                if who_to_dm is None or who_to_dm == "":
                    try:
                        sock.sendall("server: no one to reply to yet".encode())
                    except:
                        pass
                    continue

                sent = send_to_one_person(who_to_dm, "(DM) " + name + ": " + dm_msg)

                if sent:
                    # update so /r can keep working both ways
                    last_dm_from[sock] = who_to_dm
                    try:
                        sock.sendall(("(DM to " + who_to_dm + ") You: " + dm_msg).encode())
                    except:
                        pass
                else:
                    try:
                        sock.sendall(("server: user not found: " + who_to_dm).encode())
                    except:
                        pass

                continue

            # direct message: @username message
            if msg.startswith("@"):
                parts = msg.split(" ", 1)
                if len(parts) >= 2:
                    who_to_dm = parts[0][1:]
                    dm_msg = parts[1]

                    if who_to_dm == "":
                        try:
                            sock.sendall("server: usage is @username message".encode())
                        except:
                            pass
                        continue

                    sent = send_to_one_person(who_to_dm, "(DM) " + name + ": " + dm_msg)

                    if sent:
                        # store for /r on the other persons side too so both sides can use /r
                        lock.acquire()
                        everyone = list(client_list)
                        lock.release()
                        for c in everyone:
                            if c[1] == who_to_dm:
                                last_dm_from[c[0]] = name
                                break
                        # and store for the sender too
                        last_dm_from[sock] = who_to_dm
                        try:
                            sock.sendall(("(DM to " + who_to_dm + ") You: " + dm_msg).encode())
                        except:
                            pass
                    else:
                        try:
                            sock.sendall(("server: user not found: " + who_to_dm).encode())
                        except:
                            pass

                    continue

            # forward to everyone else
            full = name + ": " + msg
            print(full)
            send_to_everyone(full, not_this_one=sock)

    except ConnectionResetError:
        # client probably just closed the window
        pass
    except Exception as e:
        print("something went wrong: " + str(e))

    # cleanup
    kick_client(sock)
    sock.close()

    if name != "":
        print(name + " left")
        send_to_everyone("*** " + name + " left the chat ***")


# main function
def main():

    # server settings
    ip = "127.0.0.1"
    port = 5000

    # make the socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this fixes the "address already in use" error when you restart
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.bind((ip, port))
    s.listen()
    s.settimeout(1.0)

    print("server is running on port " + str(port))

    # keep accepting new connections
    try:
        while True:
            try:
                conn, addr = s.accept()
                # make a new thread for this client
                t = threading.Thread(target=handle_one_client, args=(conn, addr))
                t.daemon = True
                t.start()
            except socket.timeout:
                continue 
            
                # print how many people are connected
                # print("total clients: " + str(len(client_list)))

    except KeyboardInterrupt:
        print("closing server")

    s.close()


main()