import tkinter as tk
from tkinter import filedialog
import sqlite3
import os
import pandas as pd
from config import process_file, extract_text_from_pdf, count_words, word_counts
from db_queries.db_queries import create_table_query

# connect sqlitedb and create Database
conn = sqlite3.connect("testdb3.db")
mycursor = conn.cursor()

mycursor.execute(create_table_query)


class OCRApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)  # closing protocol
        self.grid(sticky="nsew")
        self.create_widgets()
        self.processed_files = set()  # used for storing file_paths

    def create_widgets(self):
        self.upload_button = tk.Button(self, text="Upload File", command=self.upload_file)
        self.upload_button.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        self.result_label = tk.Label(self, text="")
        self.result_label.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        self.database_contents = tk.Text(self, wrap=tk.WORD, height=10, width=50)
        self.database_contents.grid(row=2, column=0, sticky="nsew", padx=(10, 0), pady=(10, 0))

        self.scrollbar = tk.Scrollbar(self, command=self.database_contents.yview)
        self.scrollbar.grid(row=2, column=1, sticky="ns", pady=(10, 0))
        self.database_contents.config(yscrollcommand=self.scrollbar.set)

        self.print_db_button = tk.Button(self, text="Print database", command=self.print_database_contents)
        self.print_db_button.grid(row=3, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            if file_path in self.processed_files:
                self.result_label.config(
                    text=f"Error: The file '{os.path.basename(file_path)}' has already been uploaded and processed.")
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
                    text=f"OCR text extraction successful for '{file_name}'. Results saved to {output_file}."
                )
            except Exception as e:
                self.result_label.config(text=f"Error processing the file: {e}")

    def on_closing(self):
        mycursor.close()
        conn.close()
        self.master.destroy()

    def print_database_contents(self):
        mycursor.execute("SELECT * FROM pdf_text")
        rows = mycursor.fetchall()
        db_contents = "\nDatabase Contents:\nword_id   |   Text   |   Count\n"
        for row in rows:
            db_contents += f"{row[0]} | {row[1]} | {row[2]}\n"

        self.database_contents.delete(1.0, tk.END)
        self.database_contents.insert(tk.END, db_contents)


def main():
    root = tk.Tk()
    root.geometry("500x300")
    root.title("OCR Text Extraction")
    app = OCRApp(master=root)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    app.mainloop()


# ensure that code is executed only when script is running directly / not when imported
if __name__ == "__main__":
    main()
