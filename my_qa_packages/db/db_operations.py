from sqlalchemy import Table, MetaData, insert, select, text
from sqlalchemy.exc import SQLAlchemyError


def insert_data(engine, table_name: str, data: dict, schema: str = None):
    """
    Insert a row into a table.
    
    Args:
        engine: SQLAlchemy engine
        table_name: Name of the table
        data: Dictionary of column-value pairs
        schema: Database schema name (optional)
    
    Returns:
        Inserted row's primary key ID, or None on failure
    """
    try:
        metadata = MetaData(schema=schema)
        table = Table(table_name, metadata, autoload_with=engine, schema=schema)

        with engine.connect() as connection:
            stmt = insert(table).values(data)
            result = connection.execute(stmt)
            connection.commit()
            inserted_id = result.inserted_primary_key[0]
            print(f"Data inserted successfully into table '{table_name}' with id: {inserted_id}")
            return inserted_id
    except SQLAlchemyError as e:
        print(f"Error inserting data: {e}")
        return None


def get_all(engine, table_name: str, schema: str = None):
    """
    Get all rows from a table.

    Args:
        engine: SQLAlchemy engine
        table_name: Name of the table
        schema: Database schema name (optional)

    Returns:
        List of rows as dictionaries, or None on failure
    """
    try:
        metadata = MetaData(schema=schema)
        table = Table(table_name, metadata, autoload_with=engine, schema=schema)

        with engine.connect() as connection:
            stmt = select(table)
            result = connection.execute(stmt)
            rows = [row._asdict() for row in result]
            print(f"Fetched {len(rows)} rows from '{table_name}'")
            return rows
    except SQLAlchemyError as e:
        print(f"Error fetching data: {e}")
        return None


def get_by_query(engine, query: str):
    """
    Execute a raw SQL query and return results.

    WARNING: This function executes raw SQL. Never pass unsanitized user input
    directly as the query string to avoid SQL injection attacks.

    Args:
        engine: SQLAlchemy engine
        query: Raw SQL query string

    Returns:
        List of rows as dictionaries, or None on failure
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = [row._asdict() for row in result]
            print(f"Query returned {len(rows)} rows")
            return rows
    except SQLAlchemyError as e:
        print(f"Error executing query: {e}")
        return None
