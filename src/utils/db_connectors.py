"""
Database connectors for PostgreSQL and MongoDB
"""

import os
from typing import Optional, Dict, Any
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import yaml
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


class PostgresConnector:
    """PostgreSQL database connector using psycopg2 and SQLAlchemy"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize PostgreSQL connector

        Args:
            config_path: Path to config YAML file (optional)
        """
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                db_config = config['database']['postgres']
        else:
            db_config = {}

        self.host = os.getenv('POSTGRES_HOST', db_config.get('host', 'localhost'))
        self.port = os.getenv('POSTGRES_PORT', db_config.get('port', 5432))
        self.database = os.getenv('POSTGRES_DB', db_config.get('database'))
        self.schema = db_config.get('schema', 'ris')
        self.user = os.getenv('POSTGRES_USER', db_config.get('user'))
        self.password = os.getenv('POSTGRES_PASSWORD', db_config.get('password'))

        self._engine: Optional[Engine] = None

    @property
    def connection_string(self) -> str:
        """Get SQLAlchemy connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def engine(self) -> Engine:
        """Get or create SQLAlchemy engine"""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        return self._engine

    @contextmanager
    def get_connection(self, cursor_factory=RealDictCursor):
        """
        Context manager for database connections

        Args:
            cursor_factory: Cursor factory (default: RealDictCursor)

        Yields:
            Database connection
        """
        conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            cursor_factory=cursor_factory
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Context manager for database cursors

        Args:
            cursor_factory: Cursor factory (default: RealDictCursor)

        Yields:
            Database cursor
        """
        with self.get_connection(cursor_factory) as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """
        Execute SELECT query and return results

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of results (as dicts if using RealDictCursor)
        """
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_script(self, script_path: str):
        """
        Execute SQL script from file

        Args:
            script_path: Path to SQL file
        """
        with open(script_path, 'r', encoding='utf-8') as f:
            script = f.read()

        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(script)

    def table_exists(self, table_name: str, schema: Optional[str] = None) -> bool:
        """
        Check if table exists

        Args:
            table_name: Table name
            schema: Schema name (default: self.schema)

        Returns:
            True if table exists
        """
        schema = schema or self.schema
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            );
        """
        result = self.execute_query(query, (schema, table_name))
        return result[0]['exists'] if result else False


class MongoConnector:
    """MongoDB connector using pymongo"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MongoDB connector

        Args:
            config_path: Path to config YAML file (optional)
        """
        if config_path:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                db_config = config['database']['mongodb']
        else:
            db_config = {}

        self.host = os.getenv('MONGO_HOST', db_config.get('host', 'localhost'))
        self.port = os.getenv('MONGO_PORT', db_config.get('port', 27017))
        self.database_name = os.getenv('MONGO_DB', db_config.get('database'))
        self.user = os.getenv('MONGO_USER', db_config.get('user'))
        self.password = os.getenv('MONGO_PASSWORD', db_config.get('password'))

        self._client: Optional[MongoClient] = None

    @property
    def connection_string(self) -> str:
        """Get MongoDB connection string"""
        if self.user and self.password:
            return f"mongodb://{self.user}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        return f"mongodb://{self.host}:{self.port}/{self.database_name}"

    @property
    def client(self) -> MongoClient:
        """Get or create MongoDB client"""
        if self._client is None:
            self._client = MongoClient(self.connection_string)
        return self._client

    @property
    def db(self):
        """Get database"""
        return self.client[self.database_name]

    def get_collection(self, collection_name: str):
        """
        Get collection from database

        Args:
            collection_name: Collection name

        Returns:
            MongoDB collection
        """
        return self.db[collection_name]

    def list_collections(self) -> list:
        """
        List all collections in database

        Returns:
            List of collection names
        """
        return self.db.list_collection_names()

    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if collection exists

        Args:
            collection_name: Collection name

        Returns:
            True if collection exists
        """
        return collection_name in self.list_collections()

    def get_schema_sample(self, collection_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Get schema sample from collection

        Args:
            collection_name: Collection name
            sample_size: Number of documents to sample

        Returns:
            Dictionary with field names and sample values
        """
        collection = self.get_collection(collection_name)
        pipeline = [
            {"$sample": {"size": sample_size}},
            {"$limit": sample_size}
        ]

        docs = list(collection.aggregate(pipeline))

        # Collect all unique fields
        schema = {}
        for doc in docs:
            for key, value in doc.items():
                if key not in schema:
                    schema[key] = {
                        'type': type(value).__name__,
                        'sample_values': []
                    }
                if len(schema[key]['sample_values']) < 5:
                    schema[key]['sample_values'].append(value)

        return schema

    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None


# Convenience functions
def get_postgres_connector(config_path: Optional[str] = None) -> PostgresConnector:
    """Get PostgreSQL connector"""
    return PostgresConnector(config_path)


def get_mongo_connector(config_path: Optional[str] = None) -> MongoConnector:
    """Get MongoDB connector"""
    return MongoConnector(config_path)
