"""
Ten plik zawiera modele Pydantic służące jako "kontrakty" 
do walidacji argumentów przekazywanych do narzędzi przez AI.
"""

from pydantic import BaseModel, Field
from typing import List, Union, Protocol, runtime_checkable

@runtime_checkable
class BaseTool(Protocol):
    """
    Bazowy protokół dla wszystkich narzędzi w systemie.
    
    Każde narzędzie musi implementować:
    - name: nazwę narzędzia
    - description: opis funkcjonalności narzędzia
    - execute: metodę wykonującą akcję narzędzia
    """
    name: str
    description: str
    
    def execute(self, *args, **kwargs) -> str:
        """
        Wykonuje akcję narzędzia.
        
        Returns:
            str: Wynik wykonania narzędzia
        """
        ...

class WeatherArgs(BaseModel):
    city: str = Field(..., description="Nazwa miasta, dla którego ma być sprawdzona pogoda.")

class AddTaskArgs(BaseModel):
    description: str = Field(..., description="Pełny opis zadania do dodania.")

class ListTasksArgs(BaseModel):
    status: str = Field(default='todo', description="Status zadań do wyświetlenia, np. 'todo' lub 'done'.")

class TaskIdArgs(BaseModel):
    task_ids: Union[int, List[int]] = Field(..., description="Pojedynczy numer ID zadania lub lista numerów ID.")

class MathArgs(BaseModel):
    a: int
    b: int 