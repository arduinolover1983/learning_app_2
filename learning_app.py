import tkinter as tk
from tkinter import ttk
import pandas as pd
import pygame

# Load the words data
try:
    data = pd.read_csv("test_set.csv", delimiter=";")
except FileNotFoundError:
    print("Error: 'test_set.csv' not found.")
    exit()
except pd.errors.ParserError as e:
    print(f"Error parsing CSV: {e}")
    exit()

# Debugging: Print column names to verify
print(data.columns)

# Initialize pygame for audio
pygame.mixer.init()

# Create the main application window
root = tk.Tk()
root.title("Afghan to Dutch Translation Quiz")

# Define global variables
current_word = None
score = 0
categories = data['categorie'].unique()  # Get the unique categories from the data

# Start page (Beginner Page)
def show_start_page():
    """Show the starting page where the user selects a category."""
    quiz_frame.grid_forget()  # Hide the quiz page if it's visible
    start_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))  # Show the start page frame

def show_quiz_page(selected_category):
    """Show the quiz page with the selected category."""
    global current_word
    global score
    
    # Hide the start page
    start_frame.grid_forget()
    
    # Show the quiz page frame
    quiz_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Filter the data based on the selected category
    category_data = data[data['categorie'] == selected_category]
    
    # Get a random word from the selected category
    current_word = category_data.sample(1).iloc[0]
    
    # Display the word in the quiz page
    word_label.config(text=f"Translate this word: {current_word['afghaans_woord']}")
    score_label.config(text=f"Score: {score}")

    # Create a "Back" button if it doesn't exist already
    back_button = ttk.Button(quiz_frame, text="Back", command=show_start_page)
    back_button.grid(row=4, column=0, columnspan=2, pady=10)

def choose_category():
    """Show a popup for category selection."""
    def on_category_selected():
        selected_category = category_var.get()
        show_quiz_page(selected_category)
    
    # Create a new window for category selection
    category_window = tk.Toplevel(root)
    category_window.title("Choose Category")
    
    category_var = tk.StringVar(value=categories[0])  # Default to the first category
    category_label = ttk.Label(category_window, text="Select a category:")
    category_label.pack(padx=20, pady=10)
    
    category_menu = ttk.OptionMenu(category_window, category_var, *categories)
    category_menu.pack(padx=20, pady=10)
    
    select_button = ttk.Button(category_window, text="Start Quiz", command=on_category_selected)
    select_button.pack(pady=20)

def get_random_word():
    """Selects a random Afghan word from the dataset."""
    global current_word
    current_word = data.sample(1).iloc[0]  # Randomly select a row
    afghan_word = current_word["afghaans_woord"]
    return afghan_word

def check_answer():
    """Checks if the entered Dutch word matches the expected translation."""
    global score
    user_answer = answer_entry.get().strip().lower()
    correct_answer = current_word["nederlands_woord"].strip().lower()
    if user_answer == correct_answer:
        feedback_label.config(text="Correct!", foreground="green")
        score += 1
    else:
        feedback_label.config(
            text=f"Incorrect! The correct answer was: {correct_answer}", foreground="red"
        )
    score_label.config(text=f"Score: {score}")
    load_new_word()

def load_new_word():
    """Loads a new Afghan word for translation."""
    afghan_word = get_random_word()
    word_label.config(text=f"Translate this word: {afghan_word}")
    answer_entry.delete(0, tk.END)  # Clear the input field

# UI Elements (Uncommented)
start_frame = ttk.Frame(root, padding="10")

welcome_label = ttk.Label(start_frame, text="Welcome to the Translation Quiz!", font=("Arial", 16))
welcome_label.pack(pady=20)

start_button = ttk.Button(start_frame, text="Choose Category", command=choose_category)
start_button.pack(pady=10)

# Quiz page frame
quiz_frame = ttk.Frame(root, padding="10")

word_label = ttk.Label(quiz_frame, text="Translate this word:", font=("Arial", 14))
word_label.grid(row=0, column=0, columnspan=2, pady=10)

answer_entry = ttk.Entry(quiz_frame, width=30)
answer_entry.grid(row=1, column=0, padx=5, pady=5)

submit_button = ttk.Button(quiz_frame, text="Submit", command=check_answer)
submit_button.grid(row=1, column=1, padx=5, pady=5)

feedback_label = ttk.Label(quiz_frame, text="", font=("Arial", 12))
feedback_label.grid(row=2, column=0, columnspan=2, pady=10)

score_label = ttk.Label(quiz_frame, text="Score: 0", font=("Arial", 12))
score_label.grid(row=3, column=0, columnspan=2, pady=10)

# Start with the welcome page
show_start_page()

# Start the application
root.mainloop()
