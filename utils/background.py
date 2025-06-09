import asyncio
from typing import Callable, Dict, Any, List, Coroutine, Optional
import logging
import time
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class TaskStatus:
    """Status zadania w tle."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackgroundTask:
    """Reprezentuje zadanie w tle."""
    
    def __init__(self, task_id: str, coro: Coroutine):
        self.task_id = task_id
        self.coro = coro
        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.result: Any = None
        self.task: Optional[asyncio.Task] = None

class BackgroundTaskManager:
    """Zarządza wykonywaniem zadań w tle."""
    
    def __init__(self, max_workers: int = 10):
        """
        Args:
            max_workers: Maksymalna liczba jednoczesnych zadań
        """
        self.max_workers = max_workers
        self.tasks: Dict[str, BackgroundTask] = {}
        self.semaphore = asyncio.Semaphore(max_workers)
        logger.info(f"Initialized background task manager with {max_workers} workers")
    
    async def run_task(self, coro: Coroutine, task_id: Optional[str] = None) -> str:
        """
        Uruchamia zadanie w tle.
        
        Args:
            coro: Korutyna do wykonania
            task_id: Opcjonalny identyfikator zadania
            
        Returns:
            str: Identyfikator zadania
        """
        # Wygeneruj ID jeśli nie podano
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        # Utwórz obiekt zadania
        task = BackgroundTask(task_id, coro)
        self.tasks[task_id] = task
        
        # Uruchom zadanie
        task.task = asyncio.create_task(self._run_with_semaphore(task))
        
        logger.info(f"Started background task {task_id}")
        return task_id
    
    async def _run_with_semaphore(self, task: BackgroundTask):
        """Wykonuje zadanie z ograniczeniem liczby jednoczesnych zadań."""
        async with self.semaphore:
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.now()
            
            try:
                task.result = await task.coro
                task.status = TaskStatus.COMPLETED
                logger.info(
                    f"Background task {task.task_id} completed in "
                    f"{(datetime.now() - task.start_time).total_seconds():.2f}s"
                )
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
                logger.info(f"Background task {task.task_id} was cancelled")
                raise
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                logger.error(f"Background task {task.task_id} failed: {str(e)}")
                raise
            finally:
                task.end_time = datetime.now()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Zwraca status zadania.
        
        Args:
            task_id: Identyfikator zadania
            
        Returns:
            Optional[Dict[str, Any]]: Status zadania lub None jeśli nie znaleziono
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "error": task.error,
            "result": task.result
        }
    
    def get_running_tasks(self) -> List[str]:
        """Zwraca listę identyfikatorów uruchomionych zadań."""
        return [
            task_id for task_id, task in self.tasks.items()
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        ]
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Anuluje zadanie o podanym identyfikatorze.
        
        Args:
            task_id: Identyfikator zadania
            
        Returns:
            bool: True jeśli zadanie zostało anulowane, False jeśli nie znaleziono zadania
        """
        task = self.tasks.get(task_id)
        if not task or not task.task:
            return False
        
        task.task.cancel()
        task.status = TaskStatus.CANCELLED
        task.end_time = datetime.now()
        logger.info(f"Cancelled background task {task_id}")
        return True
    
    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """
        Czyści zakończone zadania starsze niż podany czas.
        
        Args:
            max_age_hours: Maksymalny wiek zadania w godzinach
        """
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                if task.end_time and (current_time - task.end_time).total_seconds() > max_age_hours * 3600:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.debug(f"Cleaned up completed task {task_id}") 