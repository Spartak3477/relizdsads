import tkinter as tk
import socket
import threading
import winsound  # 🔊 звук (Windows)

# --- Налаштування ---
HOST = "26.88.49.105"
PORT = 5555

# --- Глобальні змінні ---
board = [""] * 9
buttons = []
game_over = False
turn = True
player_symbol = "X"
enemy_symbol = "O"
mode = None
client = None

colors = {"X": "#ff4d4d", "O": "#4da6ff"}

# --- Перевірка перемоги ---
def check_winner(b=None):
    b = b or board
    wins = [(0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)]

    for a,b_,c in wins:
        if b[a] == b[b_] and b[b_] == b[c] and b[a] != "":
            return b[a], (a,b_,c)

    if "" not in b:
        return "Draw", None

    return None, None


# --- Підсвітка ---
def highlight_winner(combo):
    for i in combo:
        buttons[i]["bg"] = "#2ecc71"  # 🟩 зелений


# --- Звук ---
def play_sound():
    try:
        winsound.Beep(800, 100)  # частота, тривалість
    except:
        pass


# --- Кнопки ---
def update_buttons_state():
    for i,b in enumerate(buttons):
        if board[i] != "" or not turn or game_over:
            b["state"] = "disabled"
        else:
            b["state"] = "normal"


# --- Хід ---
def make_move(i,p):
    global game_over, turn

    if game_over or board[i] != "":
        return

    play_sound()  # 🔊 звук

    board[i] = p
    buttons[i]["text"] = p
    buttons[i]["fg"] = colors[p]
    buttons[i]["disabledforeground"] = colors[p]

    winner, combo = check_winner()

    if winner:
        game_over = True

        if combo:
            highlight_winner(combo)

        if winner == "Draw":
            status["text"] = "Draw!"
        else:
            status["text"] = f"{winner} wins!"

        update_buttons_state()
        return

    if mode == "ONLINE":
        if p == player_symbol:
            turn = False
            status["text"] = "Enemy turn..."
        else:
            turn = True
            status["text"] = "Your turn"

    elif mode == "BOT":
        turn = (p == enemy_symbol)

    update_buttons_state()


# --- Клік ---
def click(i):
    if not turn or game_over:
        return

    make_move(i,player_symbol)

    if mode == "ONLINE":
        client.send(str(i).encode())

    if mode == "BOT":
        window.after(300, bot_move)


# --- Minimax BOT ---
def minimax(b,is_max):

    winner, _ = check_winner(b)

    if winner == enemy_symbol:
        return 1
    if winner == player_symbol:
        return -1
    if winner == "Draw":
        return 0

    if is_max:
        best = -999
        for i in range(9):
            if b[i] == "":
                b[i] = enemy_symbol
                score = minimax(b,False)
                b[i] = ""
                best = max(best,score)
        return best

    else:
        best = 999
        for i in range(9):
            if b[i] == "":
                b[i] = player_symbol
                score = minimax(b,True)
                b[i] = ""
                best = min(best,score)
        return best


def bot_move():
    global turn

    if game_over:
        return

    best_score = -999
    best_move = None

    for i in range(9):
        if board[i] == "":
            board[i] = enemy_symbol
            score = minimax(board,False)
            board[i] = ""

            if score > best_score:
                best_score = score
                best_move = i

    if best_move is not None:
        make_move(best_move,enemy_symbol)


# --- ONLINE receive ---
def receive():
    while True:
        try:
            data = client.recv(1024).decode()

            if data == "RESTART":
                restart_game(sync=True)
            else:
                move = int(data)
                make_move(move,enemy_symbol)

        except:
            break


# --- Restart ---
def restart_game(sync=False):
    global board, game_over, turn

    board = [""] * 9
    game_over = False

    turn = player_symbol == "X"

    for b in buttons:
        b["text"] = ""
        b["fg"] = "white"
        b["disabledforeground"] = "white"
        b["bg"] = "#222"  # 🔄 скидання підсвітки

    if turn:
        status["text"] = "Your turn"
    else:
        status["text"] = "Enemy turn"

    update_buttons_state()

    if mode == "ONLINE" and not sync:
        try:
            client.send("RESTART".encode())
        except:
            pass

    if mode == "BOT" and not turn:
        window.after(300, bot_move)


# --- Старт гри ---
def start_game(selected_mode):

    global mode, client, turn, player_symbol, enemy_symbol

    menu_frame.destroy()
    game_frame.pack()

    if selected_mode == "ONLINE":

        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(5)
            client.connect((HOST, PORT))

            data = client.recv(1024).decode()
            mode_server, player_symbol = data.split("|")

            enemy_symbol = "O" if player_symbol == "X" else "X"

            if mode_server == "ONLINE":
                mode = "ONLINE"
                turn = player_symbol == "X"

                status["text"] = "Your turn" if turn else "Enemy turn..."

                threading.Thread(target=receive, daemon=True).start()

            else:
                raise Exception("No opponent")

        except:
            mode = "BOT"
            turn = True
            status["text"] = "No player found. Playing vs Bot"

    else:
        mode = "BOT"
        turn = True
        status["text"] = "Bot mode"

    update_buttons_state()

    if mode == "BOT" and not turn:
        window.after(300, bot_move)


# --- GUI ---
window = tk.Tk()
window.title("Tic-Tac-Toe")
window.configure(bg="#1e1e1e")

menu_frame = tk.Frame(window,bg="#1e1e1e")
menu_frame.pack()

tk.Label(menu_frame,text="Tic-Tac-Toe",font=("Arial",24),
         bg="#1e1e1e",fg="white").pack(pady=20)

tk.Button(menu_frame,text="Play vs Bot",font=("Arial",14),
          width=20,command=lambda:start_game("BOT")).pack(pady=10)

tk.Button(menu_frame,text="Play Online vs Friend",font=("Arial",14),
          width=20,command=lambda:start_game("ONLINE")).pack(pady=10)

game_frame = tk.Frame(window,bg="#1e1e1e")

for i in range(9):
    btn = tk.Button(
        game_frame,
        text="",
        font=("Arial",36),
        width=5,
        height=2,
        bg="#222",
        fg="white",
        activebackground="#333",
        disabledforeground="white",
        command=lambda i=i: click(i)
    )
    btn.grid(row=i//3,column=i%3,padx=5,pady=5)
    buttons.append(btn)

status = tk.Label(game_frame,text="Game started",
                  font=("Arial",14),bg="#1e1e1e",fg="white")
status.grid(row=3,column=0,columnspan=3,pady=10)

restart_btn = tk.Button(game_frame,text="Restart Game",
                        font=("Arial",12),bg="#444",
                        fg="white",command=restart_game)
restart_btn.grid(row=4,column=0,columnspan=3,pady=5)

window.mainloop()
