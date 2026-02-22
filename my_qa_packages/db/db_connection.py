import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sshtunnel import SSHTunnelForwarder


def create_db_connection(
    host: str = None,
    user: str = None,
    password: str = None,
    database: str = None,
    port: int = 3306,
    config: dict = None
):
    try:
        # if connection configuration provided in config parameter then set all value in individual variables
        if config:
            host = config.get("host")
            user = config.get("user")
            password = config.get("password")
            database = config.get("database")
            port = config.get("port", 3306)

        # If database is local, password is not required
        if host == "localhost":
            if not all ([user, database]):
                raise ValueError("Missing required database configuration parameters")
        else:
            if not all ([host, user, password, database]):
                raise ValueError("Missing required database configuration parameters for remote database")

        # URL encode password to handle special characters like @, #, etc.
        encoded_password = quote_plus(password) if password else ""

        # create connection string from above given configuration
        connection_string = f"mysql+mysqlconnector://{user}:{encoded_password}@{host}:{port}/{database}"

        # create database connection
        engine = create_engine(connection_string)

        # Test if connection working
        with engine.connect() as connection:
            print(f"connected to database '{database}' as host '{host}'")
        
        return engine

    except SQLAlchemyError as e:
        print("Database connection failed:", e)
        return None

    except ValueError as e:
        print("Configuration error:", e)
        return None


def create_ssh_tunnel(
    ssh_host: str,
    ssh_user: str,
    ssh_pkey_path: str,
    remote_host: str,
    remote_port: int,
    local_bind_port: int = 3307,
    ssh_port: int = 22
):
    """
    Create an SSH tunnel to a remote database.
    
    Args:
        ssh_host: SSH server hostname/IP
        ssh_user: SSH username
        ssh_pkey_path: Path to SSH private key (.pem file)
        remote_host: Remote database host
        remote_port: Remote database port
        local_bind_port: Local port to bind the tunnel (default: 3307)
        ssh_port: SSH server port (default: 22)
    
    Returns:
        SSHTunnelForwarder instance
    """
    if not ssh_pkey_path or not os.path.exists(ssh_pkey_path):
        raise FileNotFoundError(f"PEM key not found: {ssh_pkey_path}")

    tunnel = SSHTunnelForwarder(
        (ssh_host, ssh_port),
        ssh_username=ssh_user,
        ssh_private_key=ssh_pkey_path,
        remote_bind_address=(remote_host, remote_port),
        local_bind_address=("127.0.0.1", local_bind_port)
    )
    tunnel.start()
    print(f"SSH tunnel established on localhost:{local_bind_port}")
    
    return tunnel


def create_db_connection_with_tunnel(
    ssh_host: str,
    ssh_user: str,
    ssh_pkey_path: str,
    db_host: str,
    db_port: int,
    db_user: str,
    db_password: str,
    db_name: str,
    local_bind_port: int = 3307,
    ssh_port: int = 22
):
    """
    Create a database connection through an SSH tunnel.
    
    Args:
        ssh_host: SSH server hostname/IP
        ssh_user: SSH username
        ssh_pkey_path: Path to SSH private key (.pem file)
        db_host: Remote database host
        db_port: Remote database port
        db_user: Database username
        db_password: Database password
        db_name: Database name
        local_bind_port: Local port to bind the tunnel (default: 3307)
        ssh_port: SSH server port (default: 22)
    
    Returns:
        tuple: (engine, tunnel) - SQLAlchemy engine and SSH tunnel
    """
    tunnel = create_ssh_tunnel(
        ssh_host=ssh_host,
        ssh_user=ssh_user,
        ssh_pkey_path=ssh_pkey_path,
        remote_host=db_host,
        remote_port=db_port,
        local_bind_port=local_bind_port,
        ssh_port=ssh_port
    )
    
    engine = create_db_connection(
        host="127.0.0.1",
        port=local_bind_port,
        user=db_user,
        password=db_password,
        database=db_name
    )
    
    return engine, tunnel
