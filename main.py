from tkinter import *
from tkinter import ttk
from tkinter import messagebox

def initialize_new_game(game_window,board, first_game):
    current_player = StringVar()
    current_player.set("Player 1")
    if first_game:
        buttons_frame = ttk.Frame(game_window)
        buttons_frame.grid(column=0,row=0,sticky="NS")

        reset_button = ttk.Button(buttons_frame,text="Reset",command = lambda: initialize_new_game(game_window,board,False))
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
        board = []
        for i in range(3):
            line = []
            for j in range(3):
                board_position = Button(board_borders,command=lambda board=board,i=i,j=j: apply_move(current_player,board,i,j),bd=0,font=("arial",50))
                board_borders.create_window(140*i+2,140*j+2,width=137,height=137,anchor="nw",window=board_position)
                line.append(board_position)
            board.append(line[:])
    else:
        for buttons in board:
            for button in buttons:
                button.config(text="",state='normal')    
    return current_player

def check_winning(board,x,y):
    current_board=[['','',''],['','',''],['','','']]
    for i in range(3):
        for j in range(3):
            current_board[i][j] = board[i][j]['text']
    
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
    for buttons in board:
        for button in buttons:
            if button['text']=='':
                end = False
    return end

def apply_move(current_player, board,x,y):
    if board[x][y]['text']=='':
        if current_player.get() == "Player 1":
            board[x][y].config(text="X",state='disabled')
        else:
            board[x][y].config(text="O",state='disabled')
        win = check_winning(board,x,y)
        if win:
            messagebox.showinfo(current_player.get() + " won the game",current_player.get() + " has won the game")
        elif check_end(board) :
            messagebox.showinfo("It's a tie!","The game ended with a tie")
        else:
            if current_player.get()=="Player 1":
                current_player.set("Player 2")
            else:
                current_player.set("Player 1")
        
def main():
    root = Tk()
    root.title("tic-tac-toe")
    board = []
    initialize_new_game(root,board,True)
    root.mainloop()

if __name__=="__main__":
    main()