import collections
import configparser
import cv2
import fitz
import numpy as np
import pytesseract
import spacy

config = configparser.ConfigParser()
config.read("config/config.ini")

pytesseract.pytesseract.tesseract_cmd = config.get("DEFAULT", "tesseract_path")

# Load the German model from spacy
nlp = spacy.load("de_core_news_sm")
print("Spacy model loaded")

def process_file(file_path):
    if file_path.endswith('.pdf'):
        extracted_text = extract_text_from_pdf(file_path)
    else:
        raise Exception("Unsupported file format")

    word_counts.update(count_words(extracted_text))

    return word_counts


def extract_text_from_pdf(filename):
    with fitz.open(filename) as doc:
        text = ""
        for page_number in range(doc.page_count):
            page = doc.load_page(page_number)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)

            # Preprocessing / useful for handwritten text
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
            _, thresh_img = cv2.threshold(blurred_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # here we got to retrieve the german language package from pytesseract stored locally on a C:drive
            text += pytesseract.image_to_string(thresh_img, lang='deu')

            # Look for the three words following "Therapieempfehlung"
            index = text.find("Therapieempfehlung")
            if index != -1:
                words_after = text[index:].split()[1:5]  # Get the next three words
                drug = " ".join(words_after)
                print("Drug:", drug)

        return text


def count_words(text):
    # Process the text with spaCy -> NLP model
    doc = nlp(text.lower())

    # Filter out words so that only NOUNS are stored to the DB
    words = [token.text for token in doc if token.pos_ == 'NOUN']
    print(words)

    # Count the filtered words
    return collections.Counter(words)


word_counts = collections.Counter()
