import requests
from typing import Optional, List, Dict, Any
from .models import UserFinancialContext, ChatMessage, FinolaResponse

class FinREST:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")

    def health(self) -> Dict[str, Any]:
        try:
            res = requests.get(f"{self.base_url}/health", timeout=5)
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            return {"status": "offline", "error": str(e)}

    def chat(
        self,
        message: str,
        user_id: str = "Student_User",
        context: Optional[UserFinancialContext] = None,
        history: Optional[List[ChatMessage]] = None
    ) -> FinolaResponse:
        payload = {
            "user_id": user_id,
            "message": message,
            "context": context.model_dump() if context else UserFinancialContext().model_dump(),
            "history": [h.model_dump() for h in history] if history else []
        }

        try:
            res = requests.post(f"{self.base_url}/v1/chat/finola", json=payload, timeout=45)
            res.raise_for_status()
            return FinolaResponse(**res.json())
        except requests.RequestException as e:
            return FinolaResponse(
                reply=f"FinREST error: {str(e)}",
                action_type="ERROR",
                issue_detected=False,
                diagnostics={"error": str(e)}
            )