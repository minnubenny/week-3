import asyncio
import subprocess
import google.generativeai as genai
from typing import Dict, Any
import os

# ----------------------
# CONFIGURATION
# ----------------------

MODEL_NAME = "gemini-1.5-flash"  # Use a valid model name

def load_api_key(filepath="/home/minnu/Desktop/week 3/may 20/env3.txt") -> str:
    if not os.path.exists(filepath):
        raise FileNotFoundError("env3.txt file not found.")
    
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1]
    raise ValueError("GEMINI_API_KEY not found in env3.txt.")

# Configure Gemini API
api_key = load_api_key()
genai.configure(api_key=api_key)

# Shared state for agents to communicate
shared_context: Dict[str, Any] = {
    "code": None,
    "feedback": None,
}

# ----------------------
# TOOLS
# ----------------------

def execute_code(code: str) -> str:
    with open("temp_code.py", "w", encoding="utf-8") as f:
        f.write(code)
    result = subprocess.run(["python3", "temp_code.py"], capture_output=True, text=True)
    return result.stdout + result.stderr

def lint_code(code: str) -> str:
    with open("temp_code.py", "w", encoding="utf-8") as f:
        f.write(code)
    # Enable errors only for brevity
    result = subprocess.run(
        ["pylint", "temp_code.py", "--disable=all", "--enable=errors"], 
        capture_output=True, text=True
    )
    return result.stdout

# ----------------------
# AGENTS
# ----------------------

async def coder_agent():
    # Initial code to start with
    initial_code = """\
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
"""
    print("👤 Coder: Writing initial code...\n")
    shared_context["code"] = initial_code
    await asyncio.sleep(1)  # simulate async thinking

async def debugger_agent():
    print("🤖 Debugger: Running linter and executor...\n")

    code = shared_context.get("code", "")
    lint_feedback = lint_code(code)
    exec_feedback = execute_code(code)

    feedback = f"Linter Feedback:\n{lint_feedback}\n\nExecution Output:\n{exec_feedback}"
    shared_context["feedback"] = feedback

    print(feedback)

    # If issues found, ask Gemini to fix the code
    if lint_feedback.strip() or "Traceback" in exec_feedback:
        print("\n🤖 Debugger: Issues detected. Asking Gemini to fix the code...\n")
        prompt = f"This Python code has issues:\n{code}\n\nHere is the lint and execution feedback:\n{feedback}\nPlease fix the code and return the fixed code only."
        model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = model.generate_content(prompt)
        fixed_code = response.text.strip()
        shared_context["code"] = fixed_code
        print("🤖 Debugger: Code fixed by Gemini.\n")
    else:
        print("\n🤖 Debugger: No issues detected. Code looks good!\n")

# ----------------------
# GROUP CHAT SIMULATION
# ----------------------

async def round_robin_group_chat():
    print("👥 Starting RoundRobinGroupChat...\n")

    # Step 1: Coder writes initial code
    await coder_agent()

    # Step 2: Debugger reviews and fixes code iteratively
    max_iterations = 3
    for i in range(max_iterations):
        print(f"--- Debugger iteration {i+1} ---")
        await debugger_agent()
        await asyncio.sleep(1)  # simulate delay

        # Stop early if no issues remain
        feedback = shared_context.get("feedback", "")
        if "No issues detected" in feedback or (not feedback.strip()):
            break

    # Final output
    print("✅ Final Fixed Code:\n")
    print(shared_context["code"])

    print("\n📋 Final Feedback:\n")
    print(shared_context["feedback"])

    # Save results to files
    with open("final_code.py", "w", encoding="utf-8") as f:
        f.write(shared_context["code"])
    with open("final_feedback.txt", "w", encoding="utf-8") as f:
        f.write(shared_context["feedback"])

# ----------------------
# MAIN
# ----------------------

if __name__ == "__main__":
    asyncio.run(round_robin_group_chat())
