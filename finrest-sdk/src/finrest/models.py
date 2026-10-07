from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class UserFinancialContext(BaseModel):
    current_balance: float = 1200.0
    emergency_vault: float = 500.0
    hourly_wage: float = 24.10
    hours_worked_this_fortnight: float = 0.0
    days_left_in_cycle: int = 7

class ChatMessage(BaseModel):
    role: str
    content: str

class FinolaResponse(BaseModel):
    reply: str
    action_type: str
    issue_detected: bool
    diagnostics: Dict[str, Any]