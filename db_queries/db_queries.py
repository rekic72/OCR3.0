create_table_query = '''
CREATE TABLE IF NOT EXISTS pdf_text 
    (word_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    text TEXT,
    count INT)    
'''
