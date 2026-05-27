import asyncio

first = "Srikanth"
last = "Kanteti"
age = 33
activate = True

full_name = first + " " + last
print(full_name)

greeting = "Hello, " + full_name + "!"
print(greeting.upper())

skills = ["Java", "Python", "AEM"]

skills.append("FastAPI")     # add to end (like ArrayList.add())
skills[0]                    # "Java"  — zero-indexed, same as Java
length = len(skills)                  # 4      — like .size() in Java
"Java" in skills          # True   — like .contains() in Java
print(length)

person = {
    "name": "Srikanth",
    "role": "AEM Engineer",
    "years": 8
}

person_name = person["name"]               # "Srikanth"
person_email_new = person.get("email", "N/A")   # "N/A" if key missing (safe, like getOrDefault)
person_email = person["email"] = "x@x.com" # add a new key

print(person)
print(person_name)
print(person_email)
print(person_email_new)

tools = ["get_profile", "list_skills", "get_experience"]
print(len(tools))
print("list_skills" in tools)
tools.append("get_projects")
print(tools)

def greet(name):
    return "Hello, " + name
print(greet("Srikanth"))

def greet(name, prefix="Hello"):
    return f"{prefix}, {name}!"

print(greet("Srikanth"))
print(greet("Srikanth", prefix="Hi"))

def connect(host, timeout=None):
    if timeout is None:
        timeout = 30
    print(f"Connecting to {host} with timeout {timeout}")

print(connect("localhost"))
print(connect("localhost", timeout=10))

def describe_tool(tool_name, prefix="Tool"):
    return f"{prefix}: {tool_name}"

print(describe_tool("list_skills"))
print(describe_tool("get_profile", "Calling"))

score = 85
if score > 90:
    grade = "A"
elif score > 70:        # note: "elif" not "else if"
    grade = "B"
else:
    grade = "C"

print(f"Score: {score}, Grade: {grade}")    

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
print(f"Found skill-related word: {found}")

message_lower = "what project Skills do you have?".lower()

if any(word in message_lower for word in [
            "skill", "skills", "expertise", "proficient", "know",
            "technical", "capable", "stack", "technologies"
        ]):
            tools.append("list_skills")

if any(word in message_lower for word in [
            "experience", "worked", "company", "role", "job", "employment",
            "career", "history", "position", "years", "where", "employer",
            "background"
        ]):
            tools.append("get_experience")

print(tools)

def is_about_projects(message):
    project_words = ["project", "built", "created", "portfolio", "skills"]
    message_lower = message.lower()
    return any(word in message_lower for word in project_words)

print(is_about_projects("Tell me about your projects"))   # True
print(is_about_projects("What are your skills?"))         # False


# Define an async function with "async def"
async def fetch_data():
    await asyncio.sleep(1)    # simulates waiting for a network call
    return "done"

# Run it
result = asyncio.run(fetch_data())      # Java
print(result)
print("Finished async call")

async def simulate_ollama_call(message):
    print(f"Sending to Ollama: {message}")
    await asyncio.sleep(0)    # simulate network wait
    return f"AI says: I received '{message}'"

result = asyncio.run(simulate_ollama_call("What are my skills?"))
print(result)

class Skill:
    def __init__(self, name: str, years: int) -> None:
        self.name = name
        self.years = years

    def describe(self) -> str:
        return f"{self.name} ({self.years} years)"

print(Skill("Python", 5).describe()) 

def safe_divide(a: int, b: int) -> float:
    try:
        return a / b
    except ZeroDivisionError:
        print("Cannot divide by zero!")
        return 0.0

print(safe_divide(10, 2))    # 5.0
print(safe_divide(10, 0))    # Cannot divide by zero!  then  0.0