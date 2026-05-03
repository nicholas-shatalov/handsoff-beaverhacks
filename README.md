# 🏁 Project Submission: HandsOff
Track Selection: NVIDIA — Best Use of Nemotron

💡 Inspiration
Our inspiration for HandsOff is deeply personal. One of our teammates experiences tremors, which makes traditional computer interaction—using a physical mouse to hit small buttons or navigating complex menus—incredibly frustrating and often impossible. We realized that existing accessibility tools like screen readers are remarkably "brittle"; they rely on perfect underlying HTML code that often doesn't exist. We built this to empower users with motor impairments to navigate the digital world using only their voice, bypassing the need for physical precision or clean website code.

🛠️ What It Does
HandsOff is an autonomous accessibility proxy that bridges the gap between intent and action.

Audio-to-Action: The user speaks a high-level goal (e.g., "Scroll down on this page" or "Find the search bar").


Visual Perception: Instead of reading code, the agent captures a live screenshot of the desktop to "see" exactly what the user sees.


Autonomous Execution: A multi-agent system analyzes the visual layout and executes precise, physical mouse and keyboard movements on the user's behalf.

🏗️ How We Built It
We utilized a Multi-Agent Orchestration architecture with a file-based Inter-Process Communication (IPC) loop to ensure modularity and speed.


Agent 1 (The Interpreter): Listens for raw audio transcripts, cleans the text, and condenses it into a clear, one-sentence computer command (saved as user_goal.txt).


Agent 2 (The Executor): Powered by NVIDIA Nemotron-3-Nano-Omni, this agent ingests the user goal and the screenshot to plan and output structured JSON commands.


Automation Layer: This same Nemotron model drives the execution logic, translating decisions into physical cursor movements and typing via PyAutoGUI.


🚧 Challenges We Ran Into

Scoping Ruthlessly: We originally planned for a computer-vision gesture system but pivoted at 2:49 AM on Sunday to a purely Voice-to-UI pipeline to ensure a stable, polished demo.

Latency Optimization: Sending high-res captures to the cloud was slow. We optimized this by implementing a "token diet" (reducing the reasoning budget to 1024) and using PIL image compression to shrink the upload payload.


Instruction Following: We engineered a strict SYSTEM_PROMPT to force the AI to output only valid JSON without conversational filler, which was critical to prevent the automation layer from crashing.

🌟 Accomplishments That We Are Proud Of
Personal Impact: Creating a tool that directly addresses a challenge one of our own team members faces every day.


HTML-Independent Navigation: Our agent doesn't read a single line of HTML; it perceives the screen visually, making it immune to "brittle" or poorly coded websites.


Multi-Agent Coordination: Building a functional IPC loop where different models hand off tasks seamlessly through a shared file system.

📚 What We Learned
We learned that in a 24-hour sprint, simplicity is a feature. Pivoting away from complex computer vision allowed us to focus on the technical depth of the NVIDIA Nemotron reasoning chain and ensure our voice-control loop was bulletproof for judging.

🚀 What Is Next

Local Inference: Moving from cloud API calls to local NIM containers to eliminate network latency entirely.


Long-Term Memory: Implementing a "World Model" so the agent remembers previous steps in complex, multi-page workflows.


Tech Stack: Python, NVIDIA Nemotron-3-Nano-Omni, PyAutoGUI, PIL (Pillow), python-dotenv, Requests, OpenCV, NumPy, Matplotlib, Pyperclip, PyGetWindow, NVIDIA Riva Client.

AI Disclosure: We used NVIDIA Nemotron-3-Nano-Omni for native multimodal perception and multi-step reasoning. We also consulted Gemini for architectural advice and code optimization.
