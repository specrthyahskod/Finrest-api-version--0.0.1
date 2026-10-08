# FinREST & Finola SLM Engine

[![PyPI version](https://img.shields.io/pypi/v/finrest.svg)](https://pypi.org/project/finrest/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/SLM-Llama_3.2-orange.svg)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FinREST** is an offline-first financial safety and policy runtime powered by quantized Small Language Models (SLMs) and deterministic arithmetic bounds.

It is engineered specifically to protect international university students under **Subclass 500 visa conditions (Condition 8104/8105 work hour limits)** while providing real-time liquidity protection and automated issue triage via its embedded support intelligence, **Finola**.

---

## 🏛️ Architecture & System Topology

FinREST decouples fuzzy language reasoning from deterministic financial rules to eliminate LLM arithmetic hallucinations while retaining natural interaction.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Client Consumers                                │
│       [ BudgetWise AI Desktop (PyQt5) ]  │  [ Web Dashboard (JS SDK) ] │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ pip install finrest
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    FinREST Gateway (FastAPI)                           │
├────────────────────────────────────────────────────────────────────────┤
│  1. Deterministic Financial & Policy Calculus Engine                   │
│     • Labor shift conversion: Hours = Price / Award_Wage               │
│     • Visa Condition 8104/8105: (Hours + Fortnight_Worked) <= 48h      │
│     • Emergency Vault Threshold: (Balance - Price) >= Vault            │
│     • Daily SafeSpend Velocity: Remaining_Bal / Cycle_Days             │
│                                                                        │
│  2. Asynchronous Diagnostic & Triage Worker                            │
│     • Intercepts OCR, DB, and UI anomalies                             │
│     • Background dispatch via SMTP to Administrator                    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Pre-conditioned JSON Payload
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Local Inference Layer (Ollama)                      │
│                      Model: Llama 3.2 (3B / 1B)                        │
│     • Formulates contextual responses within verified bounds           │
│     • Deterministic temperature (0.10) with JSON schema enforcement    │
└────────────────────────────────────────────────────────────────────────┘

⚙️ Core Engineering Principles
Deterministic Math Prior to Inference: Floating-point operations, labor hour conversions, and visa caps are computed in Python first. The language model receives concrete facts to explain, never raw math to calculate.

Subclass 500 Visa Guardrails: Evaluates student fortnightly work caps (48 hours/fortnight). If a purchase requires working hours that would exceed allowable limits, the engine raises an immediate VISA_HOURS_RISK flag.

Automated System Triage: User inputs reporting system failures (e.g. OCR parsing failures) are triaged into structured metadata and forwarded asynchronously to administrators via SMTP.

---

🚀 Quickstart & Server Setup
1. Prerequisites
Python 3.9+

---

Ollama running locally:

Bash
ollama run llama3.2
2. Run the Gateway Server
Clone the repository and install server dependencies:

Bash
git clone [https://github.com/specrthyahskod/BudgetWise-AI.git](https://github.com/specrthyahskod/BudgetWise-AI.git)
cd BudgetWise-AI/finrest-api
pip install fastapi uvicorn pydantic requests
Launch the FastAPI backend:

Bash
python main.py
The API documentation is accessible at http://127.0.0.1:8000/docs.

📦 Python Client SDK (finrest)
Installation
Install directly from official PyPI:

Bash
pip install finrest==0.1.1
Python SDK Usage
Python
from finrest import FinREST, UserFinancialContext

# Connect to the FinREST gateway
client = FinREST("[http://127.0.0.1:8000](http://127.0.0.1:8000)")

# Check gateway status
print("Gateway status:", client.health())

# Define student's liquidity and visa parameters
context = UserFinancialContext(
    current_balance=1100.00,             # AUD liquid funds
    emergency_vault=500.00,              # Locked buffer
    hourly_wage=25.00,                   # Base hourly wage
    hours_worked_this_fortnight=38.0,    # Logged hours this fortnight (cap: 48h)
    days_left_in_cycle=5                 # Days until next cycle
)

# Dispatch inquiry
response = client.chat(
    message="Can I buy Sony headphones for $350? Also the receipt OCR failed.",
    context=context
)

print("Finola Reply:", response.reply)
print("Calculus Verdict:", response.diagnostics["calculus"]["verdict"])
print("Labor Hours Needed:", response.diagnostics["calculus"]["hours_needed"])
print("Issue Triaged:", response.issue_detected)
🔌 API Specification
POST /v1/chat/finola
Request Payload
JSON
{
  "user_id": "student_01",
  "message": "Can I buy a tablet for $450?",
  "context": {
    "current_balance": 1200.0,
    "emergency_vault": 500.0,
    "hourly_wage": 24.10,
    "hours_worked_this_fortnight": 32.0,
    "days_left_in_cycle": 7
  },
  "history": []
}
Response Payload
JSON
{
  "reply": "Purchasing this leaves you with $750, safely above your emergency reserve. However, funding this purchase requires 18.7 hours of work, exceeding your remaining 16 allowable visa hours for this fortnight.",
  "action_type": "AFFORDABILITY",
  "issue_detected": false,
  "diagnostics": {
    "calculus": {
      "cost": 450.0,
      "hours_needed": 18.7,
      "remaining_visa_hours": 16.0,
      "post_balance": 750.0,
      "daily_safespend": 107.14,
      "verdict": "VISA_HOURS_RISK"
    },
    "issue_meta": {
      "detected": false,
      "category": null,
      "severity": null,
      "summary": null
    }
  }
}

---

📄 License
This project is licensed under the MIT License.
