import tkinter as tk
from tkinter import filedialog
import sqlite3
import os
import pandas as pd
from config import process_file, extract_text_from_pdf, count_words, word_counts
from db_queries.db_queries import create_table_query
import openai

# connect sqlitedb and create Database
conn = sqlite3.connect("testdb3.db")
mycursor = conn.cursor()

mycursor.execute(create_table_query)

openai.api_key = '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'


class OCRApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.master)
        self.scrollbar = tk.Scrollbar(self.master, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.create_widgets()
        self.processed_files = set()  # used for storing file_paths


    def create_widgets(self):
        self.upload_button = tk.Button(self, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        # Print Database button
        self.print_db_button = tk.Button(self, text="Print database", command=self.print_database_contents)
        self.print_db_button.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        # ChatGPT submit button
        self.chat_button = tk.Button(self, text="Chat with GPT", command=self.chat_with_gpt)
        self.chat_button.grid(row=6, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        # result_label for feedback to the user
        self.result_label = tk.Label(self, text="")
        self.result_label.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        # database_contents
        self.database_contents = tk.Text(self, wrap=tk.WORD, height=20, width=50)
        self.database_contents.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))

        # Text widget for displaying the response from GPT
        self.gpt_response = tk.Text(self, wrap=tk.WORD, height=10, width=50)
        self.gpt_response.grid(row=7, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))

        self.database_contents.bind("<ButtonRelease-1>", self.on_text_widget_click)

    def on_text_widget_click(self, event):
        # Clear any previous selection
        self.database_contents.tag_remove("selected", "1.0", tk.END)

        # Try to get the selected text
        try:
            selected_word = self.database_contents.get(tk.SEL_FIRST, tk.SEL_LAST)

            # Highlight the selected text
            if selected_word:
                self.database_contents.tag_add("selected", tk.SEL_FIRST, tk.SEL_LAST)
                self.database_contents.tag_configure("selected", background="gray")
        except tk.TclError:
            # Handle the case when no text is selected
            pass

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            if file_path in self.processed_files:
                print(f"Error: The file '{os.path.basename(file_path)}' has already been uploaded and processed.")
                return

            try:
                self.processed_files.add(file_path)
                word_counts = process_file(file_path)

                # Create a DataFrame from the word counts dictionary
                df = pd.DataFrame(list(word_counts.items()), columns=['Text', 'Count'])

                # Save the DataFrame to an Excel file
                output_file = 'ExtractionOcr.xlsx'
                df.to_excel(output_file, index=False)

                # Insert df into sqlite
                data = df.to_records(index=False).tolist()
                mycursor.executemany("""INSERT INTO pdf_text(Text,Count) VALUES (?,?)""", data)
                conn.commit()

                # Get the file name from the file_path
                file_name = os.path.basename(file_path)

                self.result_label.config(
                    text=f"OCR text extraction successful for '{file_name}'. Results saved to {output_file}.")

            except Exception as e:
                print(f"Error processing the file: {e}")

    def on_closing(self):
        mycursor.close()
        conn.close()
        self.master.destroy()

    def print_database_contents(self):
        mycursor.execute("SELECT * FROM pdf_text")
        rows = mycursor.fetchall()

        # Clear the Text widget
        self.database_contents.delete("1.0", tk.END)

        # Add words to the Text widget
        for row in rows:
            word = row[1]
            self.database_contents.insert(tk.END, f"{word}\n")

    def chat_with_gpt(self):
        # Get the selected word
        try:
            selected_word = self.database_contents.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            # Handle the case when no text is selected
            selected_word = None

        # Check if a word is selected
        if not selected_word:
            self.result_label.config(text="Please select a word from the database before chatting with GPT.")
            return

        print(f"Selected word: '{selected_word}'")

        message_template = f"Tell me everything about: {selected_word}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user",
                        "content": message_template
                    }
                ]
            )

            print(response)
            self.gpt_response.delete("1.0", tk.END)
            self.gpt_response.insert(tk.END, response['choices'][0]['message']['content'])
        except Exception as e:
            self.result_label.config(text=f"Error processing the chat: {e}")
            print(f"Exception Type: {type(e)}")
            print(f"Exception Args: {e.args}")
            print(f"Exception: {e}")


def main():
    root = tk.Tk()
    root.geometry("800x600")
    root.title("OCR Text Extraction")
    app = OCRApp(master=root)
    app.pack(side="left", fill="both", expand=True)
    root.mainloop()


# ensure that code is executed only when script is running directly / not when imported
if __name__ == "__main__":
    main()
