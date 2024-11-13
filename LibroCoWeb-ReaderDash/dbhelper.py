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

