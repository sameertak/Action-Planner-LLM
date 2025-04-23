# Cafe Robot Simulator

**Cafe Robot Simulator**

---

## Use Case
This project demonstrates how a cafe service robot can be controlled via high-level natural language instructions.  
- **Scenario**: A robot stationed at the entrance (“gate”) of a cafe receives commands like “Serve coffee to Table 4, then take an order at Table 5, serve them, and return to the gate.” The system parses the instruction, issues discrete motion and action commands (move, turn, pickup, put, wait), and visualizes the robot’s path and actions in real time.

---

## How I Did It

1. **Tech Stack**  
   - **Streamlit** for interactive web UI and real-time visualization.  
   - **OpenAI’s function-calling** via `gpt-3.5-turbo` to translate user text into discrete robot commands.  
   - **Matplotlib** to render a 2D top-down view of the cafe layout (tables, counter, robot).  
   - **Python** for glue logic, function stubs, and command execution simulation.

2. **Core Components**  
   - **Function Schemas**: Defined JSON schemas for actions (`move_forward`, `turn_left`, `pickup`, etc.) so the LLM knows exactly what commands it can emit.  
   - **Executor Stubs**: Python functions that simulate robot behavior (updating position, orientation, picking/putting objects).  
   - **Streamlit Layout**:  
     - A text area for high-level user instructions.  
     - A “Run Simulation” button to start the planning/execute loop.  
     - A live matplotlib plot showing tables (T1–T10), the counter, and the robot’s path & current action.  
     - An execution trace sidebar listing each function call and its parameters.

3. **Control Loop**  
   - Initialize chat with a “system” prompt describing the environment and available actions.  
   - Append the user’s plan to the chat history.  
   - Repeatedly call the OpenAI API with `temperature=0.0` until no more function calls are returned.  
   - For each function call:  
     - Parse the name & arguments, dispatch to the executor stub.  
     - Update the robot’s simulated state (position/orientation).  
     - Append the function call and its “ok” output back into the chat history.  
     - Redraw the matplotlib figure and update the Streamlit placeholders.

## How to Use

1. **Clone & Install**  
   ```bash
   git clone https://github.com/sameertak/Action-Planner-LLM.git
   cd cafe-robot-simulator
   pip install -r requirements.txt
   ```

2. **Set Your OpenAI Key**
    ```bash
    export OPENAI_API_KEY=""
    ```

3. **Run Locally**
    ```bash
    streamlit run app.py
    ```

4. **Live Preview**

    The app is deployed at: 

** Important: This experiment is done on mini model, thus will lead to poor performance in general. Better to use larger model for better results. **
