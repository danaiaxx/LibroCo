from sqlite3 import connect, Row

database: str = "libroco.db"

def postprocess(sql: str, params: tuple) -> bool:
    db = connect(database)
    cursor = db.cursor()
    cursor.execute(sql, params)
    db.commit()
    ok: bool = True if cursor.rowcount > 0 else False
    db.close()
    return ok

def getprocess(sql: str, params: tuple = ()) -> list:
    db = connect(database)
    db.row_factory = Row  # Ensure that rows are returned as dictionaries
    cursor = db.cursor()
    cursor.execute(sql, params)
    data = cursor.fetchall()  # Fetch the data
    db.close()
    return data

# def add_record(table: str, **kwargs) -> bool:
#     keys: list = list(kwargs.keys())
#     values: list = list(kwargs.values())
#     flds: str = "`,`".join(keys)
#     vals: str = "','".join(["?"] * len(values))  # Use placeholders
#     sql: str = f"INSERT INTO `{table}`(`{flds}`) VALUES ({vals})"
#     return postprocess(sql, tuple(values))  # Pass values as a tuple

def add_record(table: str, **kwargs):
    # Extract column names and values from kwargs
    keys = list(kwargs.keys())
    values = list(kwargs.values())
    
    # Build the column names part of the SQL query
    flds = ",".join([f"`{key}`" for key in keys])  # Backtick around column names
    
    # Build the placeholders part of the SQL query
    vals = ",".join(["?" for _ in values])  # Use placeholders for the values
    
    # Build the full SQL query
    sql = f"INSERT INTO `{table}` ({flds}) VALUES ({vals})"
    
    # Call the postprocess function to execute the query with values
    return postprocess(sql, tuple(values))  # Ensure values are passed as a tuple


def getall_records(table: str) -> list:
    sql: str = f"SELECT * FROM `{table}`"
    return getprocess(sql)

def insert_request(user_id: int, book_id: int):
    data = {
        "user_id": user_id,
        "book_id": book_id,
    }
    return add_record("requests", **data)  # Use add_record to insert a new request

def get_pending_requests():
    sql = '''
    SELECT books.book_title, books.author, books.genre, requests.request_date, users.username
    FROM requests
    JOIN books ON requests.book_id = books.book_id
    JOIN users ON requests.user_id = users.user_id
    WHERE requests.status = 'Pending'  -- You can filter requests based on status (e.g., Pending, Approved)
    '''
    return getprocess(sql)

