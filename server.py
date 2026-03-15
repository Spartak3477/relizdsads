import socket
import threading
import time

HOST = "26.88.49.105"
PORT = 5555

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

players = []
symbols = ["X", "O"]  # X для першого, O для другого
lock = threading.Lock()

print("Server started, waiting for players...")

start_time = time.time()
while len(players) < 2 and time.time() - start_time < 5:
    server.settimeout(1)
    try:
        conn, addr = server.accept()
        players.append(conn)
        print(f"Player connected: {addr}")
    except:
        pass

# Якщо другий гравець не підключився — режим BOT
if len(players) == 2:
    for i, p in enumerate(players):
        p.send(f"ONLINE|{symbols[i]}".encode())
else:
    for p in players:
        p.send(f"BOT|X".encode())  # гравець грає проти бота, завжди X

# Функція для передачі ходів/перезапуску
def handle_client(conn):
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            with lock:
                # Всі повідомлення передаємо іншим гравцям
                for p in players:
                    if p != conn:
                        p.send(data.encode())
        except:
            break
    conn.close()

for p in players:
    threading.Thread(target=handle_client, args=(p,), daemon=True).start()