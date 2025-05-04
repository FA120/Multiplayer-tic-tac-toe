from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import threading
import asyncio
import websockets
import json

class Server:
    def __init__(self):
        self.window_main_menu = None
        self.Server = None
        self.peer = None
        self.current_player = None
        self.board = []
        self.shut_down = False
        self.requesting_reset = False
        for i in range(3):
            line = []
            for j in range(3):
                line.append(StringVar(value=''))
            self.board.append(line[:])

    async def stop_connexions(self):
        if self.peer:
            await self.peer.close()
            self.peer = None
        if self.Server:
            self.Server.close()
            self.Server = None
        return True

    async def join_game(self,main_menu,ip,infos):
        infos['text'] = "joining the game..."
        self.window_main_menu = main_menu
        try:
            async with websockets.connect(f"ws://{ip}:8000") as websocket:
                await websocket.send("join")
                response = await websocket.recv()
                if response=="hosted":
                    self.peer = websocket
                    self.current_player = initialize_new_game(self,False)
                    self.window_main_menu.withdraw()
                    await asyncio.gather(self.send_board(),self.receive_updates())
        except websockets.exceptions.ConnectionClosed:
            if self.current_player:
                self.current_player.set("The other player left the game")
        except Exception as error:
           messagebox.showerror(type(error),f"{error}")
        if self.shut_down:
            await self.stop_connexions()
            self.window_main_menu.destroy()

    def run_join_game(self,main_menu,ip,infos):
        asyncio.run(self.join_game(main_menu,ip,infos))

    def join_game_thread(self,main_menu,ip,infos):
        threading.Thread(target=self.run_join_game,args=(main_menu,ip,infos),daemon=True).start()
    async def handle_hosting(self,websocket, path):
        try:
            if self.peer ==None:
                self.peer = websocket
                async for message in websocket:
                    await websocket.send("hosted")
                    if message=="join":
                        self.current_player = initialize_new_game(self,True)
                        self.window_main_menu.withdraw()
                        await asyncio.gather(self.send_board(),self.receive_updates())
        except websockets.exceptions.ConnectionClosed:
            await self.stop_connexions()
            if self.current_player:
                self.current_player.set("The other player left the game")
        except Exception as error:
            messagebox.showerror(type(error),f"{error}")
    async def host_game(self,main_menu,button,ip,infos):
        server = await websockets.serve(self.handle_hosting,ip,8000)
        self.window_main_menu = main_menu
        self.Server = server
        infos['text'] ="Game is hosted.Waiting for the second player to join"
        button['state'] = "disabled"
        await server.wait_closed()
        print("server is shutting down")
        if self.shut_down:
            await self.stop_connexions()
            self.window_main_menu.destroy()
    def run_host_game(self,main_menu,button,ip,infos):
        asyncio.run(self.host_game(main_menu,button,ip,infos))

    def host_game_thread(self,main_menu,button,ip,infos):
        threading.Thread(target=self.run_host_game,args=(main_menu,button,ip,infos),daemon=True).start()

    async def send_board(self):
        while self.peer:
            await asyncio.sleep(0.1)
            if self.shut_down:
                await self.stop_connexions()
                break
            message = json.dumps(serialize_board(self.board))
            if not(self.requesting_reset): #do not send your board while requesting reset
                await self.peer.send(message)

    def reset_board(self):
        for i in range(3):
            for j in range(3):
                self.board[i][j].set('')
        self.current_player.set("Player 1")

    async def receive_updates(self):
        while self.peer:
            if self.shut_down:
                await self.stop_connexions()
                break
            message = await self.peer.recv()
            if message=="Reset":
                result = messagebox.askquestion("Reset","The other player is requesting a reset, do you accept?")
                if result=='yes':
                    self.reset_board()
                    await self.peer.send("Reset accepted")
                else:
                    await self.peer.send("Reset rejected")

            elif message=="Reset accepted":
                self.reset_board()
                messagebox.showinfo("Reset accepted","the player has accepted the reset request")
                self.requesting_reset = False

            elif message=="Reset rejected":
                messagebox.showinfo("Reset rejected","the player has rejected the reset request")
                self.requesting_reset = False

            else: #receive a board update
                peer_board = json.loads(message)
                x,y = check_new_move(serialize_board(self.board),peer_board)
                if (x,y) != (-1,-1):
                    apply_move(self.current_player,self.board,x,y)

    async def request_reset(self):
        if self.peer:
            await self.peer.send("Reset")
        self.requesting_reset = True
    def run_request_reset(self):
        asyncio.run(self.request_reset())

    def request_reset_thread(self):
        threading.Thread(target=self.run_request_reset,daemon=True).start()       
 
def serialize_board(board):
    new_board = [['','',''],['','',''],['','','']]
    for i in range(3):
        for j in range(3):
            new_board[i][j] = board[i][j].get()
    return new_board

def check_new_move(board, peer_board):
    for i in range(3):
        for j in range(3):
            if board[i][j] != peer_board[i][j]:
                return (i,j)
    return (-1,-1)

def initialize_new_game(server,host):
    current_player = StringVar()
    current_player.set("Player 1")
    board = server.board
    game_window = Toplevel()
    game_window.focus()
    game_window.title("tic-tac-toe")
    game_window.resizable(False,False)
    if host:
        game_window.title("tic-tac-toe: Hosting")
    def on_close():
        server.shut_down = True
        game_window.destroy()
    game_window.protocol("WM_DELETE_WINDOW",on_close)
    buttons_frame = ttk.Frame(game_window)
    buttons_frame.grid(column=0,row=0,sticky="NS")

    reset_button = ttk.Button(buttons_frame,text="Reset",command = server.request_reset_thread)
    reset_button.grid(column=0,row=0,sticky="N")

    close_button = ttk.Button(buttons_frame, text="Close", command=game_window.destroy)
    close_button.grid(column=0, row = 1, pady=100)

    board_frame = ttk.Frame(game_window)
    board_frame.grid(column=1,row=0)

    player_monitor = ttk.Label(board_frame,textvariable=current_player,font=("Arial", 25))
    player_monitor.grid(column = 0, row = 0,padx=100)

    board_borders = Canvas(board_frame, width = 426, height = 426)
    board_borders.create_line(140,0,140,426, fill="black", width=3)
    board_borders.create_line(280,0,280,426, fill="black", width=3)
    board_borders.create_line(0,140,426,140, fill="black", width=3)
    board_borders.create_line(0,280,426,280, fill="black", width=3)
    board_borders.grid(column=0, row=1)
    for i in range(3):
        for j in range(3):
            board_position = Button(board_borders,command=lambda board=board,i=i,j=j: allow_move(current_player,board,host,i,j),bd=0,font=("arial",50),textvariable=server.board[i][j])
            board_borders.create_window(140*i+2,140*j+2,width=137,height=137,anchor="nw",window=board_position)  
    return current_player

def check_winning(current_board,x,y):
    player = current_board[x][y]
    if current_board[x].count(player)==3:
        return True
    elif [current_board[i][y] for i in range(3)].count(player)==3:
        return True
    ### check the two diagonals
    elif [current_board[i][i] for i in range(3)].count(player)==3:
        return True
    elif [current_board[i][2-i] for i in range(3)].count(player)==3:
        return True
    else:
        return False
    
def check_end(board):
    end = True
    for i in range(3):
        for j in range(3):
            if board[i][j]=='':
                end = False
    return end

def allow_move(current_player,board,host,x,y):
    if current_player.get()=="Player 1" and host:
        apply_move(current_player,board,x,y)
    elif current_player.get()=="Player 2" and not(host):
        apply_move(current_player,board,x,y)


def apply_move(current_player, board,x,y):
    if board[x][y].get()=='':
        if current_player.get() == "Player 1":
            board[x][y].set("X")
        elif current_player.get() == "Player 2":
            board[x][y].set("O")
        win = check_winning(serialize_board(board),x,y) and board[x][y].get() !=''
        if win:
            messagebox.showinfo(current_player.get() + " won the game",current_player.get() + " has won the game")
        elif check_end(serialize_board(board)) :
            messagebox.showinfo("It's a tie!","The game ended with a tie")
        else:
            if current_player.get()=="Player 1":
                current_player.set("Player 2")
            else:
                current_player.set("Player 1") 


def main():
    main_menu = Tk()
    main_menu.title("tic-tac-toe")
    main_menu.resizable(False,False)
    ip = StringVar(value="0.0.0.0")
    ip_label = Label(main_menu,text="Enter the host's ip/the ip you will be hosting with")
    ip_label.grid(column = 0, row = 0, padx = 10,sticky="N")
    ip_entry = Entry(main_menu,textvariable=ip)
    ip_entry.grid(column = 0, row = 1)
    server = Server()
    host_game_button = Button(main_menu,text="Host game",command=lambda: server.host_game_thread(main_menu,host_game_button,ip.get(),informative_label))
    host_game_button.grid(column = 0, row = 2,pady = 10)
    client = Server()
    join_game_button = Button(main_menu,text="Join game",command=lambda: client.join_game_thread(main_menu,ip.get(),informative_label))
    join_game_button.grid(column= 0, row = 3, pady = 10)

    informative_label = Label()
    informative_label.grid(column = 0, row = 4)
    main_menu.mainloop()
if __name__=="__main__":
    main()