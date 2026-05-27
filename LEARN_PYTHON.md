# Python for Java Developers — Srikanth's Learning Guide

This guide is built around **your actual project code**. Every concept is shown
first as "how you'd write it in Java", then as "how Python does it", then as
"where it appears in your project".

---

## How to Use This Guide

Work through the modules in order. Each module has:
- **Concept** — the idea, mapped to Java
- **Your Code** — where it appears in `openagent-workspace`
- **Try It** — a small exercise to write yourself

Run Python exercises in a terminal:
```bash
python3      # starts the interactive REPL — great for experimenting
```
Or create a small `.py` file and run it:
```bash
python3 my_test.py
```

---

## Module 1 — Python Basics vs Java Basics

### Variables and Types

**Java:**
```java
String name = "Srikanth";
int age = 35;
boolean active = true;
```

**Python:**
```python
name = "Srikanth"     # no type declaration, no semicolons
age = 35
active = True         # note: capital T/F
```

Python figures out types automatically. You can still check the type:
```python
print(type(name))   # <class 'str'>
print(type(age))    # <class 'int'>
```

### Strings

```python
first = "Srikanth"
last = "Kanteti"

# Concatenation (like Java's +)
full = first + " " + last

# f-strings (like Java's String.format or template literals)
greeting = f"Hello, {first} {last}!"   # "Hello, Srikanth Kanteti!"

# Useful string methods (same as Java)
"hello".upper()          # "HELLO"
"HELLO".lower()          # "hello"
"  hello  ".strip()      # "hello"   (like Java's trim())
"hello".startswith("he") # True
```

**In your project** — `career_agent.py`, line 41:
```python
message_lower = user_message.lower()   # lowercase before checking keywords
```

### Lists (like Java ArrayList)

```python
skills = ["Java", "Python", "AEM"]

skills.append("FastAPI")     # add to end (like ArrayList.add())
skills[0]                    # "Java"  — zero-indexed, same as Java
len(skills)                  # 4      — like .size() in Java
"Java" in skills             # True   — no Java equivalent shorthand
```

### Dictionaries (like Java HashMap)

```python
person = {
    "name": "Srikanth",
    "role": "AEM Engineer",
    "years": 8
}

person["name"]               # "Srikanth"
person.get("email", "N/A")   # "N/A" if key missing (safe, like getOrDefault)
person["email"] = "x@x.com" # add a new key
```

**In your project** — `career_agent.py` returns a dict at line 168:
```python
return {
    "response": response.message.content or "Unable to generate response.",
    "tools_used": tools_used,
    "iterations": 1,
    "context_preview": context[:1000],
}
```

### ✏️ Try It — Module 1

Open a terminal and type `python3`. Then try:
```python
tools = ["get_profile", "list_skills", "get_experience"]
print(len(tools))
print("list_skills" in tools)
tools.append("get_projects")
print(tools)
```
Expected output:
```
3
True
['get_profile', 'list_skills', 'get_experience', 'get_projects']
```

---

## Module 2 — Functions

### Basic Functions

**Java:**
```java
public String greet(String name) {
    return "Hello, " + name;
}
```

**Python:**
```python
def greet(name):
    return "Hello, " + name
```

Key differences:
- `def` instead of method signature
- **Indentation defines the block** — no curly braces
- No return type declared

### Default Parameters

```python
def greet(name, prefix="Hello"):
    return f"{prefix}, {name}!"

greet("Srikanth")           # "Hello, Srikanth!"
greet("Srikanth", "Hi")     # "Hi, Srikanth!"
```

Java doesn't have default parameters — you'd need method overloading.

### Optional Parameters with `None`

**Java:**
```java
public void connect(String host, Integer timeout) {  // Integer can be null
```

**Python:**
```python
def connect(host, timeout=None):
    if timeout is None:
        timeout = 30
```

**In your project** — `career.py`, line 22:
```python
class CareerChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None   # session_id is optional, defaults to None
```

### ✏️ Try It — Module 2

Write a function that takes a tool name and returns a sentence:
```python
def describe_tool(tool_name, prefix="Tool"):
    return f"{prefix}: {tool_name}"

print(describe_tool("list_skills"))
print(describe_tool("get_profile", "Calling"))
```
Expected:
```
Tool: list_skills
Calling: get_profile
```

---

## Module 3 — Control Flow

### if / elif / else

**Java:**
```java
if (score > 90) {
    grade = "A";
} else if (score > 70) {
    grade = "B";
} else {
    grade = "C";
}
```

**Python:**
```python
if score > 90:
    grade = "A"
elif score > 70:        # note: "elif" not "else if"
    grade = "B"
else:
    grade = "C"
```

### for loops

**Java:**
```java
for (String tool : toolsList) {
    System.out.println(tool);
}
```

**Python:**
```python
for tool in tools_list:
    print(tool)
```

**In your project** — `career_agent.py`, line 120:
```python
for tool_name in tools_to_call:          # loop over the list of tools to call
    try:
        if tool_name == "match_to_role":
            raw_result = await self.mcp_client.call_tool(...)
        else:
            raw_result = await self.mcp_client.call_tool(tool_name, {})
        ...
```

### `any()` — checking if any item matches

This Python shortcut appears a lot in your code:

```python
words = ["skill", "know", "expertise"]
message = "what skills do you have?"

# Long way:
found = False
for word in words:
    if word in message:
        found = True
        break

# Python shortcut with any():
found = any(word in message for word in words)
```

**In your project** — `career_agent.py`, lines 44-46:
```python
if any(word in message_lower for word in [
    "skill", "skills", "expertise", "proficient", "know",
    "technical", "capable", "stack", "technologies"
]):
    tools.append("list_skills")
```
This reads: "if ANY of these words appears in the message, add list_skills to tools."

### ✏️ Try It — Module 3

Write a function that detects if a message is about projects:
```python
def is_about_projects(message):
    project_words = ["project", "built", "created", "portfolio"]
    message_lower = message.lower()
    return any(word in message_lower for word in project_words)

print(is_about_projects("Tell me about your projects"))   # True
print(is_about_projects("What are your skills?"))         # False
```

---

## Module 4 — Classes

### Class Definition

**Java:**
```java
public class CareerAgent {
    private OllamaClient ollamaClient;

    public CareerAgent() {
        this.ollamaClient = new OllamaClient();
    }

    public String run(String message) {
        return "result";
    }
}
```

**Python:**
```python
class CareerAgent:

    def __init__(self):                    # __init__ = constructor
        self.ollama_client = get_ollama_client()   # self = this

    def run(self, message):                # every method gets self as first param
        return "result"
```

Key differences:
- `__init__` instead of constructor named after the class
- `self` is explicit (Java's `this` is implicit)
- No `public`/`private` keywords — Python uses naming conventions (`_private`)

**In your project** — `career_agent.py`, lines 33-38:
```python
class CareerAgent:
    """Direct tool-calling agent for career questions."""

    def __init__(self):
        self.ollama_client = get_ollama_client()
        self.mcp_client: Optional[MCPClient] = None
```

### ✏️ Try It — Module 4

Write a simple class to represent a skill:
```python
class Skill:
    def __init__(self, name, years):
        self.name = name
        self.years = years

    def describe(self):
        return f"{self.name} ({self.years} years)"

java_skill = Skill("Java", 8)
print(java_skill.describe())   # Java (8 years)
print(java_skill.name)         # Java
```

---

## Module 5 — Async / Await

Your project uses `async/await` heavily. This is similar to Java's
`CompletableFuture` or Spring WebFlux, but much simpler to write.

### Why async?

Calling Ollama (the AI model) over the network takes time. Instead of blocking
the whole server while waiting, async lets Python do other things meanwhile.

### The syntax

```python
import asyncio

# Define an async function with "async def"
async def fetch_data():
    await asyncio.sleep(1)    # simulates waiting for a network call
    return "done"

# Run it
result = asyncio.run(fetch_data())
```

**Java equivalent (roughly):**
```java
CompletableFuture<String> future = fetchData();
String result = future.get();
```

### In your project

**`career_agent.py`, line 40:**
```python
async def _detect_tools(self, user_message: str) -> list[str]:
```
- `async def` = this function can use `await` inside
- `-> list[str]` = type hint saying it returns a list of strings

**`career_agent.py`, line 110:**
```python
async def run(self, user_message: str) -> dict:
    ...
    await self.mcp_client.start()   # wait for MCP server to start
    ...
    tools_to_call = await self._detect_tools(user_message)
```

**`career.py`, line 35:**
```python
@router.post("/chat", response_model=CareerChatResponse)
async def career_chat(request: CareerChatRequest) -> CareerChatResponse:
    result = await asyncio.wait_for(
        run_career_agent(request.message),
        timeout=120.0        # give up after 120 seconds
    )
```

### ✏️ Try It — Module 5

You can run async code in the Python REPL with `asyncio.run()`:
```python
import asyncio

async def simulate_ollama_call(message):
    print(f"Sending to Ollama: {message}")
    await asyncio.sleep(0)    # simulate network wait
    return f"AI says: I received '{message}'"

result = asyncio.run(simulate_ollama_call("What are my skills?"))
print(result)
```

---

## Module 6 — Type Hints

Python doesn't require types, but your project uses type hints for clarity.
They work like Java's type declarations — they document intent but don't
enforce at runtime.

### Basic hints

```python
def greet(name: str) -> str:          # takes str, returns str
    return f"Hello, {name}"

def add(a: int, b: int) -> int:
    return a + b
```

### Common hints from your project

```python
from typing import Optional, Any

def process(result: Any) -> str:      # Any = could be anything (like Object in Java)
    ...

def connect(url: str, timeout: Optional[int] = None):  # Optional = can be None
    ...

def get_tools() -> list[str]:         # list of strings
    ...

def get_metadata() -> dict:           # a dictionary
    ...
```

**In your project** — `career_agent.py`, line 81:
```python
def _normalize_tool_result(self, result: Any) -> str:
    """Convert MCP tool result into readable text for the LLM."""
```

### ✏️ Try It — Module 6

Rewrite your Module 4 Skill class with type hints:
```python
class Skill:
    def __init__(self, name: str, years: int) -> None:
        self.name = name
        self.years = years

    def describe(self) -> str:
        return f"{self.name} ({self.years} years)"
```

---

## Module 7 — Exception Handling

**Java:**
```java
try {
    result = riskyMethod();
} catch (TimeoutException e) {
    throw new RuntimeException("Timed out", e);
} finally {
    cleanup();
}
```

**Python:**
```python
try:
    result = risky_method()
except TimeoutError as e:
    raise RuntimeError(f"Timed out: {e}")
finally:
    cleanup()
```

**In your project** — `career.py`, lines 51-68:
```python
try:
    result = await asyncio.wait_for(
        run_career_agent(request.message),
        timeout=120.0
    )
    ...
    return CareerChatResponse(...)

except asyncio.TimeoutError:
    raise HTTPException(status_code=504, detail="Request timed out after 60 seconds")
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
```

Notice Python catches specific exceptions first (TimeoutError), then a generic
one (Exception) — same best practice as Java.

### ✏️ Try It — Module 7

```python
def safe_divide(a: int, b: int) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        print("Cannot divide by zero!")
        return 0.0

print(safe_divide(10, 2))    # 5.0
print(safe_divide(10, 0))    # Cannot divide by zero!  then  0.0
```

---

## Module 8 — Pydantic Models (Data Classes)

Your project uses **Pydantic** to define request/response shapes. It's like
Java's record classes or Lombok `@Data` — Python auto-generates validation,
`__init__`, and type checking.

### Without Pydantic (plain class):
```python
class CareerChatRequest:
    def __init__(self, message, session_id=None):
        self.message = message
        self.session_id = session_id
```

### With Pydantic (your actual code):
```python
from pydantic import BaseModel
from typing import Optional

class CareerChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
```

Pydantic automatically:
- Validates that `message` is a string
- Sets `session_id` to `None` if not provided
- Parses JSON body from HTTP requests

**In your project** — `career.py`, lines 20-32:
```python
class CareerChatRequest(BaseModel):
    """Request to chat with the career agent."""
    message: str
    session_id: Optional[str] = None

class CareerChatResponse(BaseModel):
    """Response from the career agent."""
    response: str
    tools_used: list[str]
    iterations: int
    response_time_ms: float
    context_preview: Optional[str] = None
```

### ✏️ Try It — Module 8

```python
from pydantic import BaseModel
from typing import Optional

class SkillEntry(BaseModel):
    name: str
    years: int
    category: Optional[str] = None

java = SkillEntry(name="Java", years=8, category="Backend")
python = SkillEntry(name="Python", years=1)

print(java.name)        # Java
print(python.category)  # None
print(java.model_dump()) # {'name': 'Java', 'years': 8, 'category': 'Backend'}
```

---

## Module 9 — Decorators

Decorators look strange at first but they're just a shorthand for wrapping a
function. You'll see them everywhere in FastAPI.

### The `@` syntax

```python
@router.post("/chat")
async def career_chat(request):
    ...
```

This is exactly the same as:
```python
async def career_chat(request):
    ...
career_chat = router.post("/chat")(career_chat)
```

The decorator registers `career_chat` as the handler for `POST /chat`.
You don't need to write your own decorators — just understand what the ones
in your project do.

### Decorators you'll see in your project

| Decorator | What it does |
|-----------|-------------|
| `@router.get("/path")` | Register a GET endpoint |
| `@router.post("/path")` | Register a POST endpoint |
| `@app.get("/")` | Register a root GET endpoint |

---

## Module 10 — Imports and Project Structure

### Python imports vs Java imports

**Java:**
```java
import com.company.api.routes.CareerRoute;
```

**Python:**
```python
from apps.api.app.routes.career import router
```

The pattern is `from <dotted.path> import <name>`.
The dotted path matches the folder structure exactly.

### Your project structure

```
openagent-workspace/
└── apps/
    ├── api/
    │   └── app/
    │       ├── main.py          ← entry point, like your Main class
    │       ├── agents/
    │       │   └── career_agent.py
    │       ├── routes/
    │       │   ├── career.py    ← HTTP endpoints
    │       │   └── health.py
    │       └── core/
    │           └── config.py    ← settings/config
    └── mcp/
        └── career_server.py     ← MCP tool server
```

**In `main.py`:**
```python
from apps.api.app.routes.career import router as career_router
app.include_router(career_router)
```

This is like Spring's `@ComponentScan` — register route handlers with the app.

---

## Your First Real Task

Now that you know the fundamentals, here's a real change you can make to the
project yourself:

**Add a new keyword to the skills detector.**

In `career_agent.py`, line 44, there's a list of words that trigger the
`list_skills` tool:
```python
if any(word in message_lower for word in [
    "skill", "skills", "expertise", "proficient", "know",
    "technical", "capable", "stack", "technologies"
]):
    tools.append("list_skills")
```

**Your task:** Add the words `"tools"` and `"framework"` to this list so that
questions like "what frameworks do you use?" also trigger skills lookup.

This requires:
1. Opening `career_agent.py`
2. Finding this block
3. Adding two strings to the list

That's it — one genuine Python edit, entirely by yourself.

---

## Quick Reference — Java to Python

| Java | Python |
|------|--------|
| `String s = "hi";` | `s = "hi"` |
| `int x = 5;` | `x = 5` |
| `boolean b = true;` | `b = True` |
| `null` | `None` |
| `System.out.println()` | `print()` |
| `s.length()` | `len(s)` |
| `ArrayList<String>` | `list` |
| `HashMap<String, Object>` | `dict` |
| `for (x : list)` | `for x in list:` |
| `this` | `self` |
| Constructor | `__init__` |
| `//` comment | `#` comment |
| `/** */` docstring | `"""..."""` docstring |
| `try/catch/finally` | `try/except/finally` |
| `throws Exception` | (not needed) |
| `instanceof` | `isinstance(x, Type)` |
| `x != null` | `x is not None` |
| Curly braces `{}` | Indentation (4 spaces) |
| Semicolons `;` | None (just newlines) |

---

## What to Explore Next

Once you're comfortable with Modules 1–5, these are the parts of your project
worth reading deeply:

1. **`apps/mcp/career_server.py`** — how the MCP tools are defined
2. **`apps/api/app/core/config.py`** — how environment variables are loaded
3. **`apps/api/app/core/mcp_subprocess.py`** — how the MCP server is started as a subprocess

Come back to this guide whenever you need a Java-to-Python reminder!
