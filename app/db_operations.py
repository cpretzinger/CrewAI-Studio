# db_operations.py

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import logging
import os
import json
from datetime import datetime
from urllib.parse import urlparse

# Database configuration with proper fallbacks
DEFAULT_DB_HOST = "localhost"
DEFAULT_DB_PORT = "5432"
DEFAULT_DB_NAME = "crewai_agents"
DEFAULT_DB_USER = "user"
DEFAULT_DB_PASS = "pass"

DATABASE_URL = os.getenv('DATABASE_URL', 
    f"postgresql://{DEFAULT_DB_USER}:{DEFAULT_DB_PASS}@{DEFAULT_DB_HOST}:{DEFAULT_DB_PORT}/{DEFAULT_DB_NAME}")

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def initialize_db():
    """Initialize the database with required tables"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Drop all tables with CASCADE to handle dependencies
            cursor.execute('''
                DROP TABLE IF EXISTS agent_activity_log CASCADE;
                DROP TABLE IF EXISTS agent_tools CASCADE;
                DROP TABLE IF EXISTS crew_agents CASCADE;
                DROP TABLE IF EXISTS crew_run CASCADE;
                DROP TABLE IF EXISTS crew_tasks CASCADE;
                DROP TABLE IF EXISTS enabled_tools CASCADE;
                DROP TABLE IF EXISTS entities CASCADE;
                DROP TABLE IF EXISTS crews CASCADE;
                DROP TABLE IF EXISTS agents CASCADE;
                DROP TABLE IF EXISTS tasks CASCADE;
                DROP TABLE IF EXISTS tools CASCADE;
                DROP TABLE IF EXISTS tool_states CASCADE;
                DROP TABLE IF EXISTS tool_usage_log CASCADE;
            ''')

            # Create agents table
            cursor.execute('''
                CREATE TABLE agents (
                    id TEXT PRIMARY KEY,
                    role TEXT,
                    backstory TEXT,
                    goal TEXT,
                    allow_delegation BOOLEAN DEFAULT FALSE,
                    is_verbose BOOLEAN DEFAULT TRUE,
                    cache BOOLEAN DEFAULT TRUE,
                    llm_provider_model TEXT,
                    temperature NUMERIC DEFAULT 0.1,
                    max_iter INTEGER DEFAULT 25,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX idx_agents_role ON agents(role);
            ''')

            # Create crews table
            cursor.execute('''
                CREATE TABLE crews (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create tasks table
            cursor.execute('''
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    description TEXT,
                    expected_output TEXT,
                    agent_id TEXT REFERENCES agents(id) ON DELETE SET NULL,
                    async_execution BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create crew_agents table
            cursor.execute('''
                CREATE TABLE crew_agents (
                    crew_id TEXT REFERENCES crews(id) ON DELETE CASCADE,
                    agent_id TEXT REFERENCES agents(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (crew_id, agent_id)
                )
            ''')

            # Create crew_run table
            cursor.execute('''
                CREATE TABLE crew_run (
                    id SERIAL PRIMARY KEY,
                    crew_id TEXT REFERENCES crews(id) ON DELETE CASCADE,
                    agent_id TEXT REFERENCES agents(id) ON DELETE CASCADE,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create agent_activity_log table
            cursor.execute('''
                CREATE TABLE agent_activity_log (
                    id SERIAL PRIMARY KEY,
                    agent_id TEXT REFERENCES agents(id) ON DELETE CASCADE,
                    activity_type TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create remaining tables
            cursor.execute('''
                CREATE TABLE crew_tasks (
                    crew_id TEXT REFERENCES crews(id) ON DELETE CASCADE,
                    task_id TEXT REFERENCES tasks(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (crew_id, task_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE agent_tools (
                    agent_id TEXT REFERENCES agents(id) ON DELETE CASCADE,
                    tool_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (agent_id, tool_id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE enabled_tools (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE entities (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE tools (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    metadata JSONB
                )
            ''')

            cursor.execute('''
                CREATE TABLE tool_states (
                    id SERIAL PRIMARY KEY,
                    tool_id INTEGER REFERENCES tools(id) ON DELETE CASCADE,
                    state JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE tool_usage_log (
                    id SERIAL PRIMARY KEY,
                    tool_id INTEGER REFERENCES tools(id) ON DELETE CASCADE,
                    usage_data JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.commit()

@contextmanager
def get_db_connection():
    """Context manager for database connections with pooling"""
    conn = None
    try:
        conn = pool.getconn()
        conn.cursor_factory = RealDictCursor
        yield conn
    except psycopg2.OperationalError as e:
        logging.error(f"Could not connect to database: {e}")
        raise
    finally:
        if conn:
            pool.putconn(conn)

def load_agents_data():
    """Load all agents data from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM agents ORDER BY created_at DESC
            ''')
            return cursor.fetchall()

def load_tasks_data():
    """Load all tasks data from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT t.*, a.* FROM tasks t
                LEFT JOIN agents a ON t.agent_id = a.id
                ORDER BY t.created_at DESC
            ''')
            return cursor.fetchall()

def load_crews_data(limit: int = 100, offset: int = 0):
    """Load crews data from the database with pagination"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                SELECT c.*, array_agg(ca.agent_id) as agent_ids
                FROM crews c
                LEFT JOIN crew_agents ca ON c.id = ca.crew_id
                GROUP BY c.id
                ORDER BY c.created_at DESC
                LIMIT %s OFFSET %s
            ''', (limit, offset))
            return cursor.fetchall()

def save_agent_data(agent_data):
    """Save or update agent data in the database"""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                # Check if agent exists
                cursor.execute('SELECT id FROM agents WHERE id = %s', (agent_data['id'],))
                exists = cursor.fetchone()

                if exists:
                    # Update existing agent
                    cursor.execute('''
                        UPDATE agents 
                        SET role = %s,
                            backstory = %s,
                            goal = %s,
                            allow_delegation = %s,
                            is_verbose = %s,
                            cache = %s,
                            llm_provider_model = %s,
                            temperature = %s,
                            max_iter = %s
                        WHERE id = %s
                        RETURNING id
                    ''', (
                        agent_data['role'],
                        agent_data['backstory'],
                        agent_data['goal'],
                        agent_data['allow_delegation'],
                        agent_data['is_verbose'],
                        agent_data['cache'],
                        agent_data['llm_provider_model'],
                        agent_data['temperature'],
                        agent_data['max_iter'],
                        agent_data['id']
                    ))
                else:
                    # Insert new agent
                    cursor.execute('''
                        INSERT INTO agents (
                            id, role, backstory, goal, allow_delegation,
                            is_verbose, cache, llm_provider_model, temperature, max_iter
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        agent_data['id'],
                        agent_data['role'],
                        agent_data['backstory'],
                        agent_data['goal'],
                        agent_data['allow_delegation'],
                        agent_data['is_verbose'],
                        agent_data['cache'],
                        agent_data['llm_provider_model'],
                        agent_data['temperature'],
                        agent_data['max_iter']
                    ))

                conn.commit()
                return cursor.fetchone()['id']

        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to save agent: {str(e)}")
            raise

def delete_agent_data(agent_id: str):
    """Delete an agent from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM agents WHERE id = %s', (agent_id,))
            conn.commit()

def save_crew_data(crew_data):
    """Save or update crew data in the database"""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                if 'id' in crew_data:
                    cursor.execute('''
                        UPDATE crews 
                        SET name = %s, metadata = %s
                        WHERE id = %s
                        RETURNING id
                    ''', (crew_data['name'], json.dumps(crew_data['metadata']), crew_data['id']))
                else:
                    cursor.execute('''
                        INSERT INTO crews (name, metadata)
                        VALUES (%s, %s)
                        RETURNING id
                    ''', (crew_data['name'], json.dumps(crew_data['metadata'])))
                
                crew_id = cursor.fetchone()['id']
                
                if 'agents' in crew_data:
                    cursor.execute('DELETE FROM crew_run WHERE crew_id = %s', (crew_id,))
                    for agent in crew_data['agents']:
                        cursor.execute('''
                            INSERT INTO crew_run (crew_id, agent_id)
                            VALUES (%s, %s)
                        ''', (crew_id, agent['id']))
                
                conn.commit()
                return crew_id
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to save crew: {str(e)}")
            raise

def save_task_data(task_data):
    """Save or update task data in the database"""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                if 'id' in task_data:
                    cursor.execute('''
                        UPDATE tasks 
                        SET description = %s,
                            expected_output = %s,
                            agent_id = %s,
                            async_execution = %s
                        WHERE id = %s
                        RETURNING id
                    ''', (
                        task_data['description'],
                        task_data['expected_output'],
                        task_data['agent_id'],
                        task_data['async_execution'],
                        task_data['id']
                    ))
                else:
                    cursor.execute('''
                        INSERT INTO tasks (
                            id, description, expected_output, agent_id, async_execution
                        ) VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    ''', (
                        task_data['id'],
                        task_data['description'],
                        task_data['expected_output'],
                        task_data['agent_id'],
                        task_data['async_execution']
                    ))

                conn.commit()
                return cursor.fetchone()['id']

        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to save task: {str(e)}")
            raise

def delete_task_data(task_id: str):
    """Delete a task from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
            conn.commit()

def delete_crew_data(crew_id: str):
    """Delete a crew and its agent relationships from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM crews WHERE id = %s', (crew_id,))
            conn.commit()

def cleanup_old_logs(days: int = 30):
    """Delete logs older than specified days"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                DELETE FROM agent_activity_log 
                WHERE created_at < NOW() - INTERVAL '%s days'
            ''', (days,))
            conn.commit()

def load_crew_run_data():
    """Load crew run data from the database"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM crew_run')
            return cursor.fetchall()

def save_crew_run_data(crew_id: str, agent_id: str, status: str = None):
    """Save crew run data with optional status"""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO crew_run (crew_id, agent_id, status)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (crew_id, agent_id, status))
                conn.commit()
                return cursor.fetchone()['id']
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to save crew run: {str(e)}")
            raise

def log_agent_activity(agent_id: str, activity_type: str, details: str):
    """Log agent activity"""
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO agent_activity_log (agent_id, activity_type, details)
                    VALUES (%s, %s, %s)
                    RETURNING id
                ''', (agent_id, activity_type, details))
                conn.commit()
                return cursor.fetchone()['id']
        except Exception as e:
            conn.rollback()
            logging.error(f"Failed to log agent activity: {str(e)}")
            raise
