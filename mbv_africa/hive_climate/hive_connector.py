"""
Hive Connection Manager
Handles connections to Apache Hive via PyHive
"""
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from pyhive import hive
from thrift.transport import TSocket, TTransport
from thrift.protocol import TBinaryProtocol
import pandas as pd

logger = logging.getLogger(__name__)


class HiveConnectionManager:
    """
    Manages connections to Apache Hive
    Provides connection pooling and error handling
    """
    
    def __init__(self, host='localhost', port=10000, database='default', 
                 username='hive', auth='NOSASL'):
        """
        Initialize Hive connection manager
        
        Args:
            host: Hive server host
            port: HiveServer2 port (default 10000)
            database: Default database
            username: Hive username
            auth: Authentication method (NOSASL, LDAP, KERBEROS)
        """
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.auth = auth
        
    def get_connection(self):
        """
        Create a new Hive connection
        
        Returns:
            hive.Connection object
        """
        try:
            logger.info(f"Connecting to Hive at {self.host}:{self.port}/{self.database}")
            connection = hive.Connection(
                host=self.host,
                port=self.port,
                database=self.database,
                username=self.username,
                auth=self.auth
            )
            logger.info("Hive connection established successfully")
            return connection
        except Exception as e:
            logger.error(f"Failed to connect to Hive: {str(e)}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """
        Context manager for Hive cursor
        Automatically closes connection after use
        
        Usage:
            with hive_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
        """
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            yield cursor
        except Exception as e:
            logger.error(f"Error executing Hive query: {str(e)}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
                logger.info("Hive connection closed")
    
    def execute_query(self, query: str, fetch_all: bool = True) -> Optional[List[tuple]]:
        """
        Execute a Hive query and return results
        
        Args:
            query: SQL query to execute
            fetch_all: Whether to fetch all results (default True)
            
        Returns:
            List of tuples with query results, or None if no results
        """
        try:
            with self.get_cursor() as cursor:
                logger.info(f"Executing query: {query[:100]}...")
                cursor.execute(query)
                
                if fetch_all:
                    results = cursor.fetchall()
                    logger.info(f"Query returned {len(results)} rows")
                    return results
                else:
                    return None
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_query_to_dataframe(self, query: str) -> pd.DataFrame:
        """
        Execute query and return results as pandas DataFrame
        
        Args:
            query: SQL query to execute
            
        Returns:
            pandas DataFrame with results
        """
        try:
            with self.get_cursor() as cursor:
                logger.info(f"Executing query to DataFrame: {query[:100]}...")
                cursor.execute(query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch data
                data = cursor.fetchall()
                
                # Create DataFrame
                df = pd.DataFrame(data, columns=columns)
                logger.info(f"Created DataFrame with shape {df.shape}")
                
                return df
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {str(e)}")
            raise
    
    def get_tables(self, database: Optional[str] = None) -> List[str]:
        """
        Get list of tables in database
        
        Args:
            database: Database name (uses default if None)
            
        Returns:
            List of table names
        """
        db = database or self.database
        query = f"SHOW TABLES IN {db}"
        results = self.execute_query(query)
        return [row[0] for row in results] if results else []
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, str]]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of dictionaries with column info (name, type, comment)
        """
        query = f"DESCRIBE {table_name}"
        results = self.execute_query(query)
        
        schema = []
        for row in results:
            if row[0] and not row[0].startswith('#'):  # Skip comments
                schema.append({
                    'name': row[0].strip(),
                    'type': row[1].strip() if row[1] else '',
                    'comment': row[2].strip() if len(row) > 2 and row[2] else ''
                })
        
        return schema
    
    def test_connection(self) -> bool:
        """
        Test if Hive connection is working
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_databases(self) -> List[str]:
        """
        Get list of all databases
        
        Returns:
            List of database names
        """
        query = "SHOW DATABASES"
        results = self.execute_query(query)
        return [row[0] for row in results] if results else []
    
    def execute_batch(self, queries: List[str]) -> Dict[str, Any]:
        """
        Execute multiple queries in sequence
        
        Args:
            queries: List of SQL queries
            
        Returns:
            Dictionary with execution statistics
        """
        stats = {
            'total': len(queries),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        with self.get_cursor() as cursor:
            for i, query in enumerate(queries):
                try:
                    logger.info(f"Executing batch query {i+1}/{len(queries)}")
                    cursor.execute(query)
                    stats['successful'] += 1
                except Exception as e:
                    logger.error(f"Batch query {i+1} failed: {str(e)}")
                    stats['failed'] += 1
                    stats['errors'].append({
                        'query_index': i,
                        'query': query[:100],
                        'error': str(e)
                    })
        
        return stats


# Singleton instance
_hive_manager = None


def get_hive_manager(host='localhost', port=10000, database='default') -> HiveConnectionManager:
    """
    Get singleton instance of HiveConnectionManager
    
    Args:
        host: Hive server host
        port: HiveServer2 port
        database: Default database
        
    Returns:
        HiveConnectionManager instance
    """
    global _hive_manager
    if _hive_manager is None:
        _hive_manager = HiveConnectionManager(host=host, port=port, database=database)
    return _hive_manager
