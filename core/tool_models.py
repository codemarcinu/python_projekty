from pydantic import BaseModel, Field
from typing import List, Union

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