import tkinter as tk
import random
from playsound import playsound
import threading

def play_bomb_sound():
    threading.Thread(target=playsound, args=("bomb_sound.wav",), daemon=True).start()

class Minesweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper")
        self.grid_size = 8
        self.bomb_count = 10
        self.board = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.buttons = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.generate_board()
        self.create_buttons()

    def generate_board(self):
        # Place bombs
        self.bombs = set(random.sample(range(self.grid_size * self.grid_size), self.bomb_count))
        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

        # Initialize the board with zeros
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                self.board[i][j] = 0

        for bomb in self.bombs:
            x, y = divmod(bomb, self.grid_size)
            self.board[x][y] = "B"

            # Update numbers around the bomb
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size and self.board[nx][ny] != "B":
                    self.board[nx][ny] += 1

        # Replace non-bomb tiles with either numbers (1 or 2) or blanks ("")
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] != "B":
                    self.board[i][j] = self.board[i][j] if self.board[i][j] in (1, 2) else ""

    def reveal_tile(self, i, j):
        if self.board[i][j] == "B":
            self.buttons[i][j].config(text="💣", bg="red", state="disabled")
            play_bomb_sound()
            self.game_over()
        elif self.board[i][j] == "":
            self.reveal_blank(i, j)
        else:
            self.buttons[i][j].config(text=str(self.board[i][j]), bg="lightgray", state="disabled")

    def reveal_blank(self, i, j):
        # Use BFS/DFS to reveal connected blank spaces
        stack = [(i, j)]
        visited = set()

        while stack:
            ci, cj = stack.pop()
            if (ci, cj) in visited:
                continue
            visited.add((ci, cj))

            self.buttons[ci][cj].config(text="", bg="lightgray", state="disabled")

            # Add neighbors if they are blank or numbered
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dx, dy in directions:
                ni, nj = ci + dx, cj + dy
                if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                    if self.board[ni][nj] == "" and (ni, nj) not in visited:
                        stack.append((ni, nj))
                    elif self.board[ni][nj] != "B":
                        self.buttons[ni][nj].config(text=str(self.board[ni][nj]), bg="lightgray", state="disabled")

    def create_buttons(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                btn = tk.Button(self.root, width=4, height=2, command=lambda i=i, j=j: self.reveal_tile(i, j))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def game_over(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == "B":
                    self.buttons[i][j].config(text="💣", bg="red", state="disabled")
                else:
                    self.buttons[i][j].config(text=str(self.board[i][j]), state="disabled")
        tk.Label(self.root, text="Game Over!", font=("Arial", 16), fg="red").grid(row=self.grid_size, column=0, columnspan=self.grid_size)

# Main application
root = tk.Tk()
app = Minesweeper(root)
root.mainloop()
