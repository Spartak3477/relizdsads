import tkinter as tk
import socket
import threading
import random

# --- Налаштування ---
HOST = "26.88.49.105"  # IP сервера
PORT = 5555

# --- Глобальні змінні ---
board = [""] * 9
buttons = []
game_over = False
turn = True
player_symbol = "X"
enemy_symbol = "O"
mode = None  # "BOT" або "ONLINE"
client = None

colors = {"X": "#ff4d4d", "O": "#4da6ff"}

# --- Tic-Tac-Toe логіка ---
def check_winner(b=None):
    b = b or board
    wins = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    for a,b_,c in wins:
        if b[a]==b[b_] and b[b_]==b[c] and b[a]!="":
            return b[a]
    if "" not in b:
        return "Draw"
    return None

def update_buttons_state():
    for i,b in enumerate(buttons):
        if board[i]!="" or not turn or game_over:
            b["state"]="disabled"
        else:
            b["state"]="normal"

def make_move(i,p):
    global game_over, turn
    if game_over or board[i]!="":
        return
    board[i]=p
    buttons[i]["text"]=p
    buttons[i]["fg"]=colors[p]

    winner=check_winner()
    if winner:
        game_over=True
        status["text"]=f"{winner} wins!" if winner!="Draw" else "Draw!"

    if mode=="ONLINE":
        if p==player_symbol:
            turn=False
            status["text"]="Enemy turn..."
        else:
            turn=True
            status["text"]="Your turn"
        update_buttons_state()

def click(i):
    if not turn or game_over:
        return
    make_move(i,player_symbol)
    if mode=="ONLINE":
        client.send(str(i).encode())
    else:
        window.after(300, bot_move)

# --- Minimax Bot ---
def minimax(b,is_max):
    winner=check_winner(b)
    if winner==enemy_symbol: return 1
    if winner==player_symbol: return -1
    if winner=="Draw": return 0

    if is_max:
        best=-float('inf')
        for i in range(9):
            if b[i]=="":
                b[i]=enemy_symbol
                score=minimax(b,False)
                b[i]=""
                best=max(best,score)
        return best
    else:
        best=float('inf')
        for i in range(9):
            if b[i]=="":
                b[i]=player_symbol
                score=minimax(b,True)
                b[i]=""
                best=min(best,score)
        return best

def bot_move():
    if game_over: return
    best_score=-float('inf')
    best_move=None
    for i in range(9):
        if board[i]=="":
            board[i]=enemy_symbol
            score=minimax(board,False)
            board[i]=""
            if score>best_score:
                best_score=score
                best_move=i
    if best_move is not None:
        make_move(best_move,enemy_symbol)

# --- Receive ONLINE moves ---
def receive():
    global turn
    while True:
        try:
            data=client.recv(1024).decode()
            if data.startswith("RESTART"):
                restart_game()
            else:
                move=int(data)
                make_move(move,enemy_symbol)
        except:
            break

# --- Restart ---
def restart_game():
    global board, game_over, turn
    board=[""]*9
    game_over=False
    turn=True if player_symbol=="X" else False
    for b in buttons:
        b["text"]=""
    status["text"]="Your turn" if turn else "Enemy turn"
    update_buttons_state()
    if mode=="ONLINE":
        client.send("RESTART".encode())

# --- Початок гри ---
def start_game(selected_mode):
    global mode, client, turn
    mode=selected_mode
    menu_frame.destroy()
    game_frame.pack()

    if mode=="ONLINE":
        # Підключення до сервера
        client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((HOST,PORT))
        mode_symbol=client.recv(1024).decode()
        mode_sym, player_symbol=mode_symbol.split("|")
        global enemy_symbol
        enemy_symbol="O" if player_symbol=="X" else "X"
        turn=True if player_symbol=="X" else False
        threading.Thread(target=receive,daemon=True).start()
    else:
        turn=True
        status["text"]="Bot mode"

    update_buttons_state()

# --- GUI ---
window=tk.Tk()
window.title("Tic-Tac-Toe")
window.configure(bg="#1e1e1e")

# Меню
menu_frame=tk.Frame(window,bg="#1e1e1e")
menu_frame.pack()
tk.Label(menu_frame,text="Tic-Tac-Toe",font=("Arial",24),bg="#1e1e1e",fg="white").pack(pady=20)
tk.Button(menu_frame,text="Play vs Bot",font=("Arial",14),width=20,
          command=lambda:start_game("BOT")).pack(pady=10)
tk.Button(menu_frame,text="Play Online vs Friend",font=("Arial",14),width=20,
          command=lambda:start_game("ONLINE")).pack(pady=10)

# Ігровий фрейм
game_frame=tk.Frame(window,bg="#1e1e1e")
for i in range(9):
    btn=tk.Button(game_frame,text="",font=("Arial",36),width=5,height=2,
                  bg="#222",fg="white",command=lambda i=i: click(i))
    btn.grid(row=i//3,column=i%3,padx=5,pady=5)
    buttons.append(btn)

status=tk.Label(game_frame,text="Game started",font=("Arial",14),bg="#1e1e1e",fg="white")
status.grid(row=3,column=0,columnspan=3,pady=10)

restart_btn=tk.Button(game_frame,text="Restart Game",font=("Arial",12),bg="#444",fg="white",
                      command=restart_game)
restart_btn.grid(row=4,column=0,columnspan=3,pady=5)

window.mainloop()