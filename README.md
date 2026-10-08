# FinREST & Finola SLM Engine

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Ollama](https://img.shields.io/badge/SLM-Llama_3.2_3B-orange.svg)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FinREST** is an offline-first financial safety and compliance runtime powered by quantized Small Language Models (SLMs) and deterministic arithmetic bounds. 

It is engineered specifically to protect international university students under **Subclass 500 visa conditions (Condition 8104/8105 work hour caps)** while providing real-time liquidity analysis and automated system issue triage via its embedded support intelligence, **Finola**.

---

## 🏛️ Architecture & System Topology

FinREST decouples fuzzy language reasoning from deterministic financial rules to eliminate LLM arithmetic hallucinations while retaining natural interaction.

┌────────────────────────────────────────────────────────────────────────┐
│                        Client Consumers                                │
│       [ BudgetWise AI Desktop (PyQt5) ]  │  [ Web Dashboard (JS SDK) ] │
└────────────────────────────────────┬───────────────────────────────────┘
│ pip install finrest (REST / JSON)
▼
┌────────────────────────────────────────────────────────────────────────┐
│                     FinREST Gateway (FastAPI)                          │
├────────────────────────────────────────────────────────────────────────┤
│  1. Deterministic Financial & Policy Calculus Engine                   │
│     • Labor shift conversion: Hours = Price / Award_Wage               │
│     • Visa Condition 8104/8105 Compliance: (Hours + Worked) <= 48h/fn  │
│     • Emergency Vault Threshold Validation: (Bal - Price) >= Vault     │
│     • Daily SafeSpend Velocity: Rem_Bal / Remaining_Cycle_Days         │
│                                                                        │
│  2. Asynchronous Diagnostic & Triage Worker                            │
│     • Classifies OCR, DB, and UI anomalies                             │
│     • Background dispatch via SMTP to Administrator                    │
└────────────────────────────────────┬───────────────────────────────────┘
│ Pre-conditioned JSON Payload
▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Local Inference Layer (Ollama)                     │
│                       Model: Llama 3.2 (3B / 1B)                       │
│     • Formulates contextual responses within strict math bounds        │
│     • Deterministic temperature (0.10) with JSON schema enforcement    │
└────────────────────────────────────────────────────────────────────────┘


---

## ⚙️ Core Engineering Principles

### 1. Deterministic Math Prior to Model Inference
LLMs are notoriously prone to floating-point and arithmetic hallucinations. FinREST never asks the language model to perform division, balance subtractions, or visa limit calculations. All financial math is evaluated in pure Python prior to model invocation and passed as verified facts into the prompt context.

### 2. Regulatory Compliance Enforcement (Subclass 500 Visa)
Australian student visas restrict secondary employment to **48 hours per fortnight** during study terms. If an affordability query requires labor shifts that exceed the student's remaining allowable fortnightly hours, the engine flags a `VISA_HOURS_RISK` verdict regardless of whether the user has sufficient immediate cash.

### 3. Automated Error Interception & Admin Triage
Finola simultaneously scans input text for runtime errors (e.g., OCR bill-parsing crashes, UI freezes). When detected, the request completes without delay while an asynchronous background task (`BackgroundTasks`) forwards a structured incident report to engineering support.

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.9+
* [Ollama](https://ollama.com/) running locally with Llama 3.2:
  ```bash
  ollama run llama3.2
