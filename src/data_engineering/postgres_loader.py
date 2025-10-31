"""
PostgreSQL data loader
Loads data into PostgreSQL marts
"""

from typing import Optional, Dict, Any
import pandas as pd
from sqlalchemy import text

from ..utils.db_connectors import PostgresConnector
from ..utils.logger import setup_logger


logger = setup_logger('postgres_loader', log_file='logs/postgres_loader.log')


class PostgresLoader:
    """Load data into PostgreSQL tables"""

    def __init__(self, postgres_connector: PostgresConnector):
        """
        Initialize loader

        Args:
            postgres_connector: PostgreSQL connector instance
        """
        self.pg = postgres_connector
        self.schema = postgres_connector.schema
        logger.info("PostgresLoader initialized")

    def execute_sql_file(self, sql_file_path: str):
        """
        Execute SQL file

        Args:
            sql_file_path: Path to SQL file
        """
        logger.info(f"Executing SQL file: {sql_file_path}")
        self.pg.execute_script(sql_file_path)
        logger.info(f"Successfully executed {sql_file_path}")

    def load_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        if_exists: str = 'append',
        chunksize: int = 1000
    ):
        """
        Load DataFrame into PostgreSQL table

        Args:
            df: DataFrame to load
            table_name: Target table name
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
            chunksize: Number of rows to insert at once
        """
        logger.info(f"Loading {len(df)} rows into {self.schema}.{table_name}")

        df.to_sql(
            name=table_name,
            con=self.pg.engine,
            schema=self.schema,
            if_exists=if_exists,
            index=False,
            chunksize=chunksize,
            method='multi'
        )

        logger.info(f"Successfully loaded {len(df)} rows into {self.schema}.{table_name}")

    def truncate_table(self, table_name: str):
        """
        Truncate table

        Args:
            table_name: Table name
        """
        logger.info(f"Truncating table {self.schema}.{table_name}")

        with self.pg.engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {self.schema}.{table_name} CASCADE"))
            conn.commit()

        logger.info(f"Successfully truncated {self.schema}.{table_name}")

    def upsert_dataframe(
        self,
        df: pd.DataFrame,
        table_name: str,
        unique_columns: list,
        update_columns: Optional[list] = None
    ):
        """
        Upsert DataFrame into PostgreSQL table (INSERT ... ON CONFLICT UPDATE)

        Args:
            df: DataFrame to upsert
            table_name: Target table name
            unique_columns: Columns that form unique constraint
            update_columns: Columns to update on conflict (if None, update all except unique)
        """
        logger.info(f"Upserting {len(df)} rows into {self.schema}.{table_name}")

        if update_columns is None:
            update_columns = [col for col in df.columns if col not in unique_columns]

        # Create temp table
        temp_table = f"{table_name}_temp"
        df.to_sql(
            name=temp_table,
            con=self.pg.engine,
            schema=self.schema,
            if_exists='replace',
            index=False
        )

        # Build upsert query
        columns = df.columns.tolist()
        columns_str = ', '.join(columns)
        values_str = ', '.join([f't.{col}' for col in columns])
        unique_str = ', '.join(unique_columns)
        update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_columns])

        upsert_query = f"""
            INSERT INTO {self.schema}.{table_name} ({columns_str})
            SELECT {columns_str} FROM {self.schema}.{temp_table} t
            ON CONFLICT ({unique_str})
            DO UPDATE SET {update_str}
        """

        with self.pg.engine.connect() as conn:
            conn.execute(text(upsert_query))
            conn.execute(text(f"DROP TABLE {self.schema}.{temp_table}"))
            conn.commit()

        logger.info(f"Successfully upserted {len(df)} rows into {self.schema}.{table_name}")

    def get_table_row_count(self, table_name: str) -> int:
        """
        Get row count from table

        Args:
            table_name: Table name

        Returns:
            Number of rows
        """
        query = f"SELECT COUNT(*) as count FROM {self.schema}.{table_name}"
        with self.pg.engine.connect() as conn:
            result = conn.execute(text(query))
            return result.fetchone()[0]

    def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists

        Args:
            table_name: Table name

        Returns:
            True if exists
        """
        return self.pg.table_exists(table_name, self.schema)
