# db_utils.py

from typing import List, Dict
from my_crew import MyCrew
from my_agent import MyAgent
from my_task import MyTask
import db_operations

def initialize_db():
    """Initialize the database with required tables"""
    db_operations.initialize_db()

def load_agents() -> List[MyAgent]:
    """Load all agents from the database"""
    agents_data = db_operations.load_agents_data()
    agents = []
    for agent_data in agents_data:
        agent = MyAgent(
            id=agent_data['id'],
            role=agent_data['role'],
            backstory=agent_data['backstory'],
            goal=agent_data['goal'],
            allow_delegation=agent_data['allow_delegation'],
            verbose=agent_data['is_verbose'],
            cache=agent_data['cache'],
            llm_provider_model=agent_data['llm_provider_model'],
            temperature=float(agent_data['temperature']),
            max_iter=agent_data['max_iter'],
            created_at=agent_data['created_at'].isoformat()
        )
        agents.append(agent)
    return agents

def save_agent(agent: MyAgent):
    """Save or update an agent in the database"""
    agent_data = {
        'id': agent.id,
        'role': agent.role,
        'backstory': getattr(agent, 'backstory', None),
        'goal': getattr(agent, 'goal', None),
        'allow_delegation': getattr(agent, 'allow_delegation', False),
        'is_verbose': getattr(agent, 'verbose', True),
        'cache': getattr(agent, 'cache', True),
        'llm_provider_model': getattr(agent, 'llm_provider_model', None),
        'temperature': getattr(agent, 'temperature', 0.1),
        'max_iter': getattr(agent, 'max_iter', 25)
    }
    return db_operations.save_agent_data(agent_data)

def delete_agent(agent_id: str):
    """Delete an agent"""
    db_operations.delete_agent_data(agent_id)

def load_tasks() -> List[MyTask]:
    """Load all tasks from the database"""
    tasks_data = db_operations.load_tasks_data()
    tasks = []
    for task_data in tasks_data:
        agent = None
        if task_data['agent_id']:
            agent = MyAgent(
                id=task_data['agent_id'],
                role=task_data['role'],
                backstory=task_data['backstory'],
                goal=task_data['goal'],
                allow_delegation=task_data['allow_delegation'],
                verbose=task_data['is_verbose'],
                cache=task_data['cache'],
                llm_provider_model=task_data['llm_provider_model'],
                temperature=float(task_data['temperature']),
                max_iter=task_data['max_iter'],
                created_at=task_data['created_at'].isoformat()
            )
        task = MyTask(
            id=task_data['id'],
            description=task_data['description'],
            expected_output=task_data['expected_output'],
            agent=agent,
            async_execution=task_data['async_execution'],
            created_at=task_data['created_at'].isoformat()
        )
        tasks.append(task)
    return tasks

def save_task(task: MyTask):
    """Save or update a task in the database"""
    task_data = {
        'id': task.id,
        'description': task.description,
        'expected_output': task.expected_output,
        'agent_id': task.agent.id if task.agent else None,
        'async_execution': task.async_execution
    }
    return db_operations.save_task_data(task_data)

def delete_task(task_id: str):
    """Delete a task"""
    db_operations.delete_task_data(task_id)

def load_crews(limit: int = 100, offset: int = 0) -> List[MyCrew]:
    """Load crews from the database with pagination"""
    crews_data = db_operations.load_crews_data(limit, offset)
    crews = []
    for crew_data in crews_data:
        metadata = crew_data['metadata'] or {}
        crew = MyCrew(
            id=crew_data['id'],
            name=crew_data['name'],
            description=metadata.get('description'),
            goal=metadata.get('goal'),
            created_at=crew_data['created_at'].isoformat()
        )
        crews.append(crew)
    return crews

def save_crew(crew: MyCrew):
    """Save or update a crew in the database"""
    crew_data = {
        'id': crew.id if hasattr(crew, 'id') else None,
        'name': crew.name,
        'metadata': {
            'description': crew.description,
            'goal': getattr(crew, 'goal', None),
            'other_attributes': getattr(crew, 'other_attributes', {}),
        }
    }
    if hasattr(crew, 'agents'):
        crew_data['agents'] = [{'id': agent.id} for agent in crew.agents]
    return db_operations.save_crew_data(crew_data)

def delete_crew(crew_id: str):
    """Delete a crew"""
    db_operations.delete_crew_data(crew_id)

def load_crew_run():
    """Load crew run data"""
    return db_operations.load_crew_run_data()

def save_crew_run(crew_id: str, agent_id: str, status: str = None):
    """Save crew run data with optional status"""
    return db_operations.save_crew_run_data(crew_id, agent_id, status)

def load_tools():
    """Load all tools from the database"""
    return []  # Tools will be created as needed

def save_tool(tool):
    """Save or update a tool in the database"""
    pass  # Tools are managed in memory only

def load_tools_state():
    """Load tools state"""
    return []  # Initially empty, will be populated as tools are enabled

def cleanup_old_logs(days: int = 30):
    """Delete logs older than specified days"""
    db_operations.cleanup_old_logs(days)

def log_agent_activity(agent_id: str, activity_type: str, details: str):
    """Log agent activity"""
    db_operations.log_agent_activity(agent_id, activity_type, details)
