import os
import json
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
import requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="FinREST Finola Intelligence Core", version="0.2.3")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ollama inference host and model configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Admin triage & SMTP configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "hazrapopi96@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "hazrapopi96@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

AU_BASE_MIN_WAGE = 24.10
FORTNIGHT_MAX_HOURS = 48.0

class UserFinancialContext(BaseModel):
    current_balance: float = 1200.0
    emergency_vault: float = 500.0
    hourly_wage: float = AU_BASE_MIN_WAGE
    hours_worked_this_fortnight: float = 0.0
    days_left_in_cycle: int = 7

class ChatMessage(BaseModel):
    role: str
    content: str

class FinolaRequest(BaseModel):
    user_id: Optional[str] = "Student_User"
    message: str
    context: Optional[UserFinancialContext] = Field(default_factory=UserFinancialContext)
    history: List[ChatMessage] = Field(default_factory=list)

class FinolaResponse(BaseModel):
    reply: str
    action_type: str
    issue_detected: bool
    diagnostics: Dict[str, Any]

def send_admin_alert(user_id: str, original_msg: str, issue_meta: dict):
    if not SMTP_USER or not SMTP_PASSWORD:
        return

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ADMIN_EMAIL
        msg["Subject"] = f"🚨 [Finola {issue_meta.get('severity', 'BUG').upper()}] {issue_meta.get('category', 'System')}"
        body = (
            f"User: {user_id}\n"
            f"Severity: {issue_meta.get('severity')}\n"
            f"Component: {issue_meta.get('category')}\n"
            f"Summary: {issue_meta.get('summary')}\n\n"
            f"Original Input:\n\"{original_msg}\""
        )
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    except Exception:
        pass

def run_financial_calculus(msg: str, ctx: UserFinancialContext) -> Optional[Dict[str, Any]]:
    # Extract explicit dollar amounts like $400, $400.00, or 400 AUD / 400 dollars
    price_matches = re.findall(r"\$\s*(\d+(?:\.\d{1,2})?)|(\d+(?:\.\d{1,2})?)\s*(?:aud|dollars)", msg, re.IGNORECASE)
    
    cost = None
    if price_matches:
        for match in reversed(price_matches):
            val = match[0] or match[1]
            if val:
                cost = float(val)
                break
    else:
        # Fallback to any standalone number if purchase verbs exist
        if any(k in msg.lower() for k in ["buy", "afford", "spend", "cost", "purchase"]):
            all_nums = re.findall(r"\b(\d+(?:\.\d{1,2})?)\b", msg)
            if all_nums:
                cost = float(all_nums[0])

    if cost is None:
        return None

    wage = max(ctx.hourly_wage, 10.0)
    hours_needed = round(cost / wage, 1)
    
    post_balance = ctx.current_balance - cost
    remaining_visa_hours = max(0.0, FORTNIGHT_MAX_HOURS - ctx.hours_worked_this_fortnight)
    visa_breach = hours_needed > remaining_visa_hours
    
    daily_spend = max(0.0, post_balance / max(1, ctx.days_left_in_cycle))
    
    if post_balance < 0:
        verdict = "DENIED"
    elif post_balance < ctx.emergency_vault:
        verdict = "CRITICAL_BUFFER_WARNING"
    elif visa_breach:
        verdict = "VISA_HOURS_RISK"
    else:
        verdict = "APPROVED"

    return {
        "cost": cost,
        "hours_needed": hours_needed,
        "remaining_visa_hours": remaining_visa_hours,
        "post_balance": round(post_balance, 2),
        "daily_safespend": round(daily_spend, 2),
        "verdict": verdict
    }

FINOLA_CORE_SYSTEM = """You are Finola, the financial engine and system operator for BudgetWise AI.
Analyze user input and Math Context.
Return ONLY valid JSON with this exact key sequence:
{
  "intent": "AFFORDABILITY" | "BUG_REPORT" | "GENERAL",
  "issue_metadata": {
    "detected": true/false,
    "category": "OCR" | "DATABASE" | "CRASH" | "CALCULATION" | null,
    "severity": "LOW" | "HIGH" | "CRITICAL" | null,
    "summary": "Short 1-sentence issue description"
  },
  "reply": "Concise 2-sentence direct answer. State remaining balance and visa cap status if math context exists, and confirm any bug report logged. Never include generic shopping advice."
}
"""

@app.post("/v1/chat/finola", response_model=FinolaResponse)
def execute_finola(req: FinolaRequest, background_tasks: BackgroundTasks):
    ctx = req.context or UserFinancialContext()
    calc_results = run_financial_calculus(req.message, ctx)
    
    prompt_payload = f"User Message: {req.message}\n"
    if calc_results:
        prompt_payload += f"Pre-computed Math Context: {json.dumps(calc_results)}\n"

    messages = [{"role": "system", "content": FINOLA_CORE_SYSTEM}]
    for h in req.history[-3:]:
        messages.append({"role": h.role, "content": h.content})
    messages.append({"role": "user", "content": prompt_payload})

    raw_content = ""
    try:
        res = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_ctx": 2048,
                    "num_predict": 1024
                }
            },
            timeout=45
        )
        res.raise_for_status()
        raw_content = res.json().get("message", {}).get("content", "{}")
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        reply_match = re.search(r'"reply":\s*"([^"]+)', raw_content)
        parsed = {
            "reply": reply_match.group(1) if reply_match else "Calculations updated.",
            "intent": "AFFORDABILITY" if calc_results else "GENERAL",
            "issue_metadata": {"detected": False, "category": None, "severity": None, "summary": None}
        }
    except Exception:
        parsed = {
            "reply": "Encountered an inference error. Operating in offline math fallback mode.",
            "intent": "GENERAL",
            "issue_metadata": {"detected": False, "category": None, "severity": None, "summary": None}
        }

    issue_meta = parsed.get("issue_metadata", {})
    is_issue = bool(issue_meta.get("detected", False))
    
    if is_issue and issue_meta.get("summary"):
        sender_id = req.user_id or "Anonymous_Student"
        background_tasks.add_task(send_admin_alert, sender_id, req.message, issue_meta)

    return FinolaResponse(
        reply=parsed.get("reply", "Processed."),
        action_type=parsed.get("intent", "GENERAL"),
        issue_detected=is_issue,
        diagnostics={
            "calculus": calc_results,
            "issue_meta": issue_meta
        }
    )

@app.get("/health")
def health():
    return {"status": "online", "model": OLLAMA_MODEL}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)