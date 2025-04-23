import os
import json
import time
import streamlit as st
import matplotlib.pyplot as plt
from openai import OpenAI
import random

# ——————————————————————————————————————————————————————————————
# 1. Initializing OpenAI
# ——————————————————————————————————————————————————————————————
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ——————————————————————————————————————————————————————————————
# 2. Defining Functions
# ——————————————————————————————————————————————————————————————
functions = [
    {
        "type": "function",
        "name": "move_forward",
        "description": "Move the robot forward by a certain distance (meters).",
        "parameters": {
            "type": "object",
            "properties": {
                "distance": {"type": "number"}
            },
            "required": ["distance"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "move_backward",
        "description": "Move the robot backward by a certain distance (meters).",
        "parameters": {
            "type": "object",
            "properties": {
                "distance": {"type": "number"}
            },
            "required": ["distance"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "wait",
        "description": "Pause the robot's actions for a certain duration (seconds).",
        "parameters": {
            "type": "object",
            "properties": {
                "duration": {"type": "number"}
            },
            "required": ["duration"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "pickup",
        "description": "Pick up an object by ID/name.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"}
            },
            "required": ["object_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "put",
        "description": "Put down an object at a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"},
                "location": {"type": "string"}
            },
            "required": ["object_id", "location"],
            "additionalProperties": False
        }
    },
]

# ——————————————————————————————————————————————————————————————
# 4. Creating simple, status based functions. 
# ——————————————————————————————————————————————————————————————

def move_forward(distance):   return {"status": "ok"}
def move_backward(distance):  return {"status": "ok"}
def turn_left(angle):         return {"status": "ok"}
def turn_right(angle):        return {"status": "ok"}
def wait(duration):           return {"status": "ok"}
def pickup(object_id):        return {"status": "picked"}
def put(object_id, location): return {"status": "placed"}

executor = {
    "move_forward": move_forward,
    "move_backward": move_backward,
    "turn_left": turn_left,
    "turn_right": turn_right,
    "wait": wait,
    "pickup": pickup,
    "put": put,
}

# ——————————————————————————————————————————————————————————————
# 4. Streamlit layout
# ——————————————————————————————————————————————————————————————
st.title("☕ Cafe Robot Simulator")

table_num = random.randint(1, 10)

if "plan" not in st.session_state:
    st.session_state.plan = f"Serve Coffee from Counter to Table {random.randint(1,10)}."

# 2. Bind the textarea to that state
plan = st.text_area(
    "Enter a high-level instruction:",
    value=st.session_state.plan,
    key="plan",        # <-- ties edits back into session_state["plan"]
    height=100
)

model_choice = st.selectbox(
    "Choose your model:",
    options=["gpt-3.5-turbo", "gpt-4"],
    index=0,  # default to gpt-3.5-turbo
    help="Which OpenAI model to use for the plan parser."
)

def describe_action(fn, args):
    if fn == "move_forward":
        return f"Moving forward {args['distance']} m"
    if fn == "move_backward":
        return f"Moving backward {args['distance']} m"
    if fn == "turn_left":
        return f"Turning left {args['angle']}°"
    if fn == "turn_right":
        return f"Turning right {args['angle']}°"
    if fn == "wait":
        return f"Waiting for {args['duration']} s"
    if fn == "pickup":
        return f"Picking up '{args['object_id']}'"
    if fn == "put":
        return f"Putting '{args['object_id']}' at {args['location']}"
    return fn


viz_ph = st.empty()
fig, ax = plt.subplots(figsize=(8,2))
ax.hlines(0, -1, 12, linewidth=1, color="gray")

# draw tables
for x in range(1,11):
    ax.scatter(x, 0, marker="s", s=80, color="lightgray", zorder=1)
    ax.text(x, 0.15, f"T{x}", ha="center")

# draw counter
ax.scatter(11, 0, marker="*", s=200, color="orange", zorder=2)
ax.text(11, 0.15, "Counter", ha="center")

# robot pointer at start (x=0)
ax.scatter(0, 0, marker='>', s=200, color="blue", zorder=3)

ax.set_title("Idle – robot at entry gate (x=0)", pad=10)
ax.set_xlim(-1,12)
ax.set_ylim(-1,1)
ax.axis("off")
viz_ph.pyplot(fig)


if st.button("Run Simulation"):
    if not model_choice:
        st.error("Select a model")
    with st.spinner("Running simmulation..."):
        # placeholders
        action_ph = st.empty()
        trace_ph  = st.empty()
        # viz_ph    = st.empty()
        current_x  = 0.0
        pos_history = [current_x]

        # chat setup
        messages = [
            {"role":"system", 
             "content": """
                You are a cafe robot:
                Start at x=0 (gate). Counter at x=11. Tables at x=1…10.
                To serve: go to counter, pickup(item), go to table N, put(item, "Table N").
                Never move forward from the counter.
                Use mathematical calculation, to decide backward or forward.
                Return to gate when all orders are put to the table done.
            """ },
            {"role":"user", "content": plan}
        ]

        trace = []
        orientation = '>'  # default pointing east

        # loop one function-call at a time
        while True:
            resp = client.responses.create(
                model=model_choice,
                input=messages,
                tools=functions,
                temperature=0.0
            )
            call = next((m for m in resp.output if m.type=="function_call"), None)
            if not call:
                break

            fn = call.name
            args = json.loads(call.arguments)
            executor[fn](**args)
            trace.append({"fn": fn, "args": args})

            # update orientation based on movement
            if fn == "move_forward":
                orientation = '>'
                current_x += args["distance"]
                pos_history.append(current_x)
            elif fn == "move_backward":
                orientation = '<'
                current_x -= args["distance"]
                pos_history.append(current_x)

            # feed back
            messages.append({"type": "function_call", "name": fn, "call_id": call.call_id, "arguments": json.dumps(args)})
            messages.append({
                "type":       "function_call_output",
                "call_id":    call.call_id,
                "output":     json.dumps({"status": "ok"})
            })

            # — execution trace
            md = "\n".join(
                f"{i+1}. `{t['fn']}`({', '.join(f'{k}={v}' for k,v in t['args'].items())})"
                for i,t in enumerate(trace)
            )
            trace_ph.markdown("**Execution Trace:**\n\n" + md)
                
            fig, ax = plt.subplots(figsize=(8,2))
            ax.set_title(f"Current action: {describe_action(fn, args)}", pad=10)

            ax.hlines(0, -1, 12, linewidth=1, color="gray")

            # tables
            for x in range(1,11):
                ax.scatter(x, 0, marker="s", s=80, color="lightgray", zorder=1)
                ax.text(x, 0.15, f"T{x}", ha="center")

            # counter as a star
            ax.scatter(11, 0, marker="*", s=200, color="orange", zorder=2)
            ax.text(11, 0.15, "Counter", ha="center")

            # path
            xs = pos_history
            ys = [0]*len(xs)
            ax.plot(xs, ys, marker="o", linestyle="-", zorder=1)

            # robot pointer at last pos
            current_x = xs[-1]
            ax.scatter(current_x, 0, marker=orientation, s=200, color="blue", zorder=3)

            ax.set_xlim(-1,12)
            ax.set_ylim(-1,1)
            ax.axis("off")
            viz_ph.pyplot(fig)

    st.success("✅ Simulation complete!")
