"""
MongoDB data extractor
Extracts raw data from MongoDB and prepares for PostgreSQL marts
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from tqdm import tqdm

from ..utils.db_connectors import MongoConnector
from ..utils.logger import setup_logger


logger = setup_logger('mongo_extractor', log_file='logs/mongo_extractor.log')


class MongoExtractor:
    """Extract data from MongoDB collections"""

    def __init__(self, mongo_connector: MongoConnector):
        """
        Initialize extractor

        Args:
            mongo_connector: MongoDB connector instance
        """
        self.mongo = mongo_connector
        logger.info("MongoExtractor initialized")

    def explore_schema(self, collection_name: str, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Explore schema of a collection

        Args:
            collection_name: Name of collection
            sample_size: Number of documents to sample

        Returns:
            Schema information
        """
        logger.info(f"Exploring schema for collection: {collection_name}")
        schema = self.mongo.get_schema_sample(collection_name, sample_size)
        logger.info(f"Found {len(schema)} fields in {collection_name}")
        return schema

    def extract_users(self, query: Optional[Dict] = None, projection: Optional[Dict] = None) -> pd.DataFrame:
        """
        Extract user data from MongoDB

        Args:
            query: MongoDB query filter
            projection: Fields to include/exclude

        Returns:
            DataFrame with user data
        """
        logger.info("Extracting user data from MongoDB")

        collection = self.mongo.get_collection('users')  # TODO: adjust collection name

        cursor = collection.find(query or {}, projection)
        total = collection.count_documents(query or {})

        logger.info(f"Found {total} users to extract")

        docs = []
        for doc in tqdm(cursor, total=total, desc="Extracting users"):
            docs.append(doc)

        df = pd.DataFrame(docs)
        logger.info(f"Extracted {len(df)} users")

        return df

    def extract_sessions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        query: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Extract session/workout data from MongoDB

        Args:
            start_date: Start date filter
            end_date: End date filter
            query: Additional query filters

        Returns:
            DataFrame with session data
        """
        logger.info(f"Extracting sessions from {start_date} to {end_date}")

        collection = self.mongo.get_collection('sessions')  # TODO: adjust collection name

        # Build query
        if query is None:
            query = {}

        if start_date or end_date:
            query['date'] = {}
            if start_date:
                query['date']['$gte'] = start_date
            if end_date:
                query['date']['$lte'] = end_date

        cursor = collection.find(query)
        total = collection.count_documents(query)

        logger.info(f"Found {total} sessions to extract")

        docs = []
        for doc in tqdm(cursor, total=total, desc="Extracting sessions"):
            docs.append(doc)

        df = pd.DataFrame(docs)
        logger.info(f"Extracted {len(df)} sessions")

        return df

    def extract_heropasses(self, query: Optional[Dict] = None) -> pd.DataFrame:
        """
        Extract HeroPass data from MongoDB

        Args:
            query: MongoDB query filter

        Returns:
            DataFrame with HeroPass data
        """
        logger.info("Extracting HeroPass data from MongoDB")

        collection = self.mongo.get_collection('heropasses')  # TODO: adjust collection name

        cursor = collection.find(query or {})
        total = collection.count_documents(query or {})

        logger.info(f"Found {total} HeroPasses to extract")

        docs = []
        for doc in tqdm(cursor, total=total, desc="Extracting HeroPasses"):
            docs.append(doc)

        df = pd.DataFrame(docs)
        logger.info(f"Extracted {len(df)} HeroPasses")

        return df

    def extract_collection_to_df(
        self,
        collection_name: str,
        query: Optional[Dict] = None,
        projection: Optional[Dict] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Generic method to extract any collection to DataFrame

        Args:
            collection_name: Name of collection
            query: MongoDB query filter
            projection: Fields to include/exclude
            limit: Maximum number of documents

        Returns:
            DataFrame
        """
        logger.info(f"Extracting collection: {collection_name}")

        collection = self.mongo.get_collection(collection_name)

        cursor = collection.find(query or {}, projection)

        if limit:
            cursor = cursor.limit(limit)
            total = min(limit, collection.count_documents(query or {}))
        else:
            total = collection.count_documents(query or {})

        logger.info(f"Found {total} documents in {collection_name}")

        docs = []
        for doc in tqdm(cursor, total=total, desc=f"Extracting {collection_name}"):
            docs.append(doc)

        df = pd.DataFrame(docs)
        logger.info(f"Extracted {len(df)} documents from {collection_name}")

        return df

    def save_to_csv(self, df: pd.DataFrame, output_path: str):
        """
        Save DataFrame to CSV

        Args:
            df: DataFrame to save
            output_path: Path to output file
        """
        logger.info(f"Saving DataFrame to {output_path}")
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} rows to {output_path}")
