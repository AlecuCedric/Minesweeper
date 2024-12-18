# -*- coding: utf-8 -*-
"""
Created on Wed Dec 18 12:49:34 2024

@author: senapi
"""

import tkinter as tk
import random
from playsound import playsound
import threading
import json
import os

def play_bomb_sound():
    threading.Thread(target=playsound, args=("bomb_sound.wav",), daemon=True).start()

class LeaderboardManager:
    def __init__(self, filename='leaderboard.json'):
        self.filename = filename
        self.leaderboard = self.load_leaderboard()

    def load_leaderboard(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return []

    def save_leaderboard(self):
        with open(self.filename, 'w') as f:
            json.dump(self.leaderboard, f)

    def add_score(self, name, score):
        # Remove oldest entries if more than 10
        if len(self.leaderboard) >= 10:
            self.leaderboard = sorted(self.leaderboard, key=lambda x: x['score'], reverse=True)[:10]

        # Add new score
        self.leaderboard.append({'name': name, 'score': score})
        
        # Sort and keep top 10
        self.leaderboard.sort(key=lambda x: x['score'], reverse=True)
        self.leaderboard = self.leaderboard[:10]
        
        self.save_leaderboard()

class LeaderboardWindow:
    def __init__(self, root, leaderboard_manager):
        self.window = tk.Toplevel(root)
        self.window.title("Leaderboard")
        self.window.geometry("300x400")
        
        # Title
        tk.Label(self.window, text="Leaderboard", font=("Arial", 16, "bold")).pack(pady=10)
        
        # Leaderboard entries
        leaderboard = leaderboard_manager.leaderboard
        for i, entry in enumerate(leaderboard, 1):
            entry_frame = tk.Frame(self.window)
            entry_frame.pack(fill='x', padx=20, pady=5)
            
            tk.Label(entry_frame, text=f"{i}. {entry['name']}", font=("Arial", 12), width=15, anchor='w').pack(side='left')
            tk.Label(entry_frame, text=str(entry['score']), font=("Arial", 12), width=10, anchor='e').pack(side='right')

class Minesweeper:
    def __init__(self, root):
        self.root = root
        self.root.title("Minesweeper")
        self.grid_size = 8
        self.bomb_count = 10
        self.board = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.buttons = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.leaderboard_manager = LeaderboardManager()
        
        # Set fixed window size
        self.button_size = 4
        self.window_width = self.grid_size * (self.button_size * 10)
        self.window_height = self.grid_size * (self.button_size * 10) + 50
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        
        self.show_start_screen()

    def show_start_screen(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Center frame
        frame = tk.Frame(self.root)
        frame.place(relx=0.5, rely=0.5, anchor='center')

        # Title
        tk.Label(frame, text="Minesweeper", font=("Arial", 20, "bold")).pack(pady=10)

        # Play Button
        play_button = tk.Button(frame, text="Play", font=("Arial", 14), command=self.start_game, width=15)
        play_button.pack(pady=5)

        # Leaderboard Button
        leaderboard_button = tk.Button(frame, text="Leaderboard", font=("Arial", 14), 
                                       command=self.show_leaderboard, width=15)
        leaderboard_button.pack(pady=5)

    def show_leaderboard(self):
        LeaderboardWindow(self.root, self.leaderboard_manager)

    def start_game(self):
        # Clear start screen
        for widget in self.root.winfo_children():
            widget.destroy()

        # Reset game state
        self.board = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.buttons = [[None for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        
        # Create back button
        back_button = tk.Button(self.root, text="Back", command=self.show_start_screen)
        back_button.grid(row=self.grid_size, column=0, columnspan=2, sticky='w', pady=5)
        
        self.generate_board()
        self.create_buttons()
        
        # Reset score tracking
        self.start_time = threading.Timer(1, self.increment_score).start()
        self.score = 0
        self.safe_tiles_count = self.grid_size * self.grid_size - self.bomb_count

    def increment_score(self):
        # Increment score
        self.score += 1
        self.start_time = threading.Timer(1, self.increment_score).start()

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
            self.safe_tiles_count -= 1
        
        # Check for win condition
        if self.safe_tiles_count == 0:
            self.game_win()

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
            self.safe_tiles_count -= 1

            # Add neighbors if they are blank or numbered
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dx, dy in directions:
                ni, nj = ci + dx, cj + dy
                if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                    if self.board[ni][nj] == "" and (ni, nj) not in visited:
                        stack.append((ni, nj))
                    elif self.board[ni][nj] != "B":
                        self.buttons[ni][nj].config(text=str(self.board[ni][nj]), bg="lightgray", state="disabled")
                        self.safe_tiles_count -= 1
        
        # Check for win condition
        if self.safe_tiles_count == 0:
            self.game_win()

    def create_buttons(self):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                btn = tk.Button(self.root, width=self.button_size, height=2, command=lambda i=i, j=j: self.reveal_tile(i, j))
                btn.grid(row=i, column=j)
                self.buttons[i][j] = btn

    def game_win(self):
        # Stop the score timer
        try:
            self.start_time.cancel()
        except:
            pass

        # Reveal all bombs
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == "B":
                    self.buttons[i][j].config(text="💣", bg="green", state="disabled")
                else:
                    self.buttons[i][j].config(text=str(self.board[i][j]), state="disabled")
        
        # Ask for player name and save score
        self.ask_for_name(True)

    def game_over(self):
        # Stop the score timer
        try:
            self.start_time.cancel()
        except:
            pass

        # Reveal all bombs
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if self.board[i][j] == "B":
                    self.buttons[i][j].config(text="💣", bg="red", state="disabled")
                else:
                    self.buttons[i][j].config(text=str(self.board[i][j]), state="disabled")
        
        # Ask for player name and save score
        self.ask_for_name(False)

    def ask_for_name(self, is_win):
        # Create a top-level window for name input
        name_window = tk.Toplevel(self.root)
        name_window.title("Game Over")
        name_window.geometry("300x200")
        
        # Game over label
        result_text = "You Win!" if is_win else "Game Over!"
        result_color = "green" if is_win else "red"
        tk.Label(name_window, text=result_text, font=("Arial", 16), fg=result_color).pack(pady=10)
        
        # Score display (use the tracked score)
        tk.Label(name_window, text=f"Your Score: {self.score}", font=("Arial", 12)).pack(pady=5)
        
        # Name input
        tk.Label(name_window, text="Enter Your Name:", font=("Arial", 12)).pack(pady=5)
        name_entry = tk.Entry(name_window, font=("Arial", 12))
        name_entry.pack(pady=5)
        
        # Submit button
        def submit_score():
            name = name_entry.get().strip()
            if name:
                self.leaderboard_manager.add_score(name, self.score)
                name_window.destroy()
                self.show_start_screen()
            else:
                tk.Label(name_window, text="Please enter a name", fg="red").pack()
        
        submit_button = tk.Button(name_window, text="Submit", command=submit_score)
        submit_button.pack(pady=10)

# Main application
root = tk.Tk()
app = Minesweeper(root)
root.mainloop()
