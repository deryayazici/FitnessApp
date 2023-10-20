import sqlite3

db_file = 'fitness.db'

def create_table():

    conn = sqlite3.connect(db_file)
    
    cursor = conn.cursor()
    
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS fitness (
        id INTEGER PRIMARY KEY,
        title TEXT,
        description TEXT,
        image TEXT
    )
    '''
    
    cursor.execute(create_table_sql)
    
    conn.commit()
    conn.close()

if __name__ == '__main__':

    create_table()
    print(f'Table created in {db_file}')
