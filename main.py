import os
import re
import time
import json
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any

import requests
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="FinREST Finola Intelligence Core",
    description="Deterministic financial calculus and Australian Subclass 500 visa compliance engine.",
    version="0.2.3",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVER_START_TIME = time.time()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Triage & Notification Config
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "hazrapopi96@gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "hazrapopi96@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Telemetry & Incident In-Memory Storage
INCIDENT_LOG: List[Dict[str, Any]] = []
METRICS: Dict[str, Any] = {
    "total_requests": 0,
    "successful_inferences": 0,
    "failed_inferences": 0,
    "latencies_ms": []
}

AU_BASE_MIN_WAGE = 24.10
FORTNIGHT_MAX_HOURS = 48.0


def record_incident(event_type: str, reason: str) -> None:
    """Logs system events, downtime reasons, and inference degradation."""
    INCIDENT_LOG.insert(0, {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "type": event_type,
        "reason": reason
    })
    if len(INCIDENT_LOG) > 20:
        INCIDENT_LOG.pop()

class UserFinancialContext(BaseModel):
    current_balance: float = Field(default=1200.0, description="Available liquid AUD balance")
    emergency_vault: float = Field(default=500.0, description="Minimum reserve threshold")
    hourly_wage: float = Field(default=AU_BASE_MIN_WAGE, description="Current wage in AUD/hour")
    hours_worked_this_fortnight: float = Field(default=0.0, description="Hours logged this fortnight")
    days_left_in_cycle: int = Field(default=7, description="Days left until next pay cycle")


def get_default_context() -> UserFinancialContext:
    return UserFinancialContext()


class ChatMessage(BaseModel):
    role: str
    content: str


class FinolaRequest(BaseModel):
    user_id: Optional[str] = Field(default="Student_User", description="Active user handle")
    message: str = Field(description="User prompt or purchase question")
    context: Optional[UserFinancialContext] = Field(default_factory=get_default_context)
    history: List[ChatMessage] = Field(default_factory=list)


class FinolaResponse(BaseModel):
    reply: str
    action_type: str
    issue_detected: bool
    diagnostics: Dict[str, Any]

def send_admin_alert(user_id: str, original_msg: str, issue_meta: dict) -> None:
    """Sends background email alert if a client issue/bug report is triaged."""
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
    except Exception as e:
        record_incident("EMAIL_ALERT_FAILURE", str(e))


def run_financial_calculus(msg: str, ctx: UserFinancialContext) -> Optional[Dict[str, Any]]:
    """Calculates wage hours, visa hours compliance, and buffer protection."""
    price_matches = re.findall(r"\$\s*(\d+(?:\.\d{1,2})?)|(\d+(?:\.\d{1,2})?)\s*(?:aud|dollars)", msg, re.IGNORECASE)
    cost = None
    if price_matches:
        for match in reversed(price_matches):
            val = match[0] or match[1]
            if val:
                cost = float(val)
                break
    else:
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


# --- API Routes ---

@app.get("/")
def root():
    """Root endpoint to verify operational status without triggering a 404."""
    uptime_sec = int(time.time() - SERVER_START_TIME)
    return {
        "service": "FinREST Finola Intelligence Core",
        "status": "online",
        "uptime_seconds": uptime_sec,
        "version": "0.2.3",
        "endpoints": {
            "health": "/health",
            "incidents": "/telemetry/incidents",
            "chat": "/v1/chat/finola",
            "docs": "/docs"
        }
    }


@app.get("/health")
def health():
    """Health endpoint returning uptime, active model, and average latency."""
    uptime_sec = int(time.time() - SERVER_START_TIME)
    avg_latency = (
        round(sum(METRICS["latencies_ms"]) / len(METRICS["latencies_ms"]), 1)
        if METRICS["latencies_ms"] else 0.0
    )
    return {
        "status": "online",
        "uptime_seconds": uptime_sec,
        "model": OLLAMA_MODEL,
        "telemetry": {
            "total_requests": METRICS["total_requests"],
            "avg_latency_ms": avg_latency,
            "failed_inferences": METRICS["failed_inferences"]
        }
    }


@app.get("/telemetry/incidents")
def get_incidents():
    """Returns logged incidents, downtime reasons, and connection errors."""
    return {
        "incidents": INCIDENT_LOG,
        "total_logged": len(INCIDENT_LOG)
    }


@app.post("/v1/chat/finola", response_model=FinolaResponse)
def execute_finola(req: FinolaRequest, background_tasks: BackgroundTasks):
    start_t = time.time()
    METRICS["total_requests"] += 1

    ctx = req.context if req.context is not None else get_default_context()
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
        METRICS["successful_inferences"] += 1

    except requests.exceptions.RequestException as req_err:
        METRICS["failed_inferences"] += 1
        record_incident("OLLAMA_OFFLINE", f"Failed to connect to local Ollama host: {str(req_err)}")
        parsed = {
            "reply": "Local inference engine offline. Operating in deterministic rule-based calculus mode.",
            "intent": "AFFORDABILITY" if calc_results else "GENERAL",
            "issue_metadata": {"detected": False, "category": None, "severity": None, "summary": None}
        }

    except json.JSONDecodeError:
        reply_match = re.search(r'"reply":\s*"([^"]+)', raw_content)
        parsed = {
            "reply": reply_match.group(1) if reply_match else "Calculations processed successfully.",
            "intent": "AFFORDABILITY" if calc_results else "GENERAL",
            "issue_metadata": {"detected": False, "category": None, "severity": None, "summary": None}
        }

    duration_ms = round((time.time() - start_t) * 1000, 1)
    METRICS["latencies_ms"].append(duration_ms)
    if len(METRICS["latencies_ms"]) > 100:
        METRICS["latencies_ms"].pop(0)

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
            "issue_meta": issue_meta,
            "latency_ms": duration_ms
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)