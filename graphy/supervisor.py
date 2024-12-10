# pylint: disable=line-too-long
import os
import uuid
from dataclasses import dataclass, fields
from datetime import datetime
from textwrap import dedent
from typing import Any, Literal, Optional, TypedDict

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    merge_message_runs,
)
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field
from trustcall import create_extractor


@dataclass(kw_only=True)
class Configuration:
    """The configurable fields for the chatbot."""

    user_id: str = "default-user"
    todo_category: str = "general"
    task_maistro_role: str = "You are a helpful task management assistant. You help you create, organize, and manage the user's ToDo list."

    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = config["configurable"] if config and "configurable" in config else {}
        values: dict[str, Any] = {f.name: os.environ.get(f.name.upper(), configurable.get(f.name)) for f in fields(cls) if f.init}
        return cls(**{k: v for k, v in values.items() if v})


class Spy:
    def __init__(self):
        self.called_tools = []

    def __call__(self, run):
        q = [run]
        while q:
            r = q.pop()
            if r.child_runs:
                q.extend(r.child_runs)
            if r.run_type == "chat_model":
                self.called_tools.append(r.outputs["generations"][0][0]["message"]["kwargs"]["tool_calls"])


def extract_tool_info(tool_calls, schema_name="Memory"):
    """Extract information from tool calls for both patches and new memories.

    Args:
        tool_calls: List of tool calls from the model
        schema_name: Name of the schema tool (e.g., "Memory", "ToDo", "Profile")
    """
    changes = []

    for call_group in tool_calls:
        for call in call_group:
            if call["name"] == "PatchDoc":
                if call["args"]["patches"]:
                    changes.append(
                        {
                            "type": "update",
                            "doc_id": call["args"]["json_doc_id"],
                            "planned_edits": call["args"]["planned_edits"],
                            "value": call["args"]["patches"][0]["value"],
                        }
                    )
                else:
                    changes.append({"type": "no_update", "doc_id": call["args"]["json_doc_id"], "planned_edits": call["args"]["planned_edits"]})
            elif call["name"] == schema_name:
                changes.append({"type": "new", "value": call["args"]})

    result_parts = []
    for change in changes:
        if change["type"] == "update":
            result_parts.append(f"Document {change['doc_id']} updated:\n" f"Plan: {change['planned_edits']}\n" f"Added content: {change['value']}")
        elif change["type"] == "no_update":
            result_parts.append(f"Document {change['doc_id']} unchanged:\n" f"{change['planned_edits']}")
        else:
            result_parts.append(f"New {schema_name} created:\n" f"Content: {change['value']}")

    return "\n\n".join(result_parts)


class Profile(BaseModel):
    """This is the profile of the user you are chatting with"""

    name: Optional[str] = Field(description="The user's name", default=None)
    location: Optional[str] = Field(description="The user's location", default=None)
    job: Optional[str] = Field(description="The user's job", default=None)
    connections: list[str] = Field(description="Personal connection of the user, such as family members, friends, or coworkers", default_factory=list)
    interests: list[str] = Field(description="Interests that the user has", default_factory=list)


class ToDo(BaseModel):
    task: str = Field(
        description="The task to be completed.",
    )
    time_to_complete: Optional[int] = Field(
        description="Estimated time to complete the task (minutes).",
    )
    deadline: Optional[datetime] = Field(
        description="When the task needs to be completed by (if applicable)",
        default=None,
    )
    solutions: list[str] = Field(
        default_factory=list,
        description=(
            "List of specific, actionable solutions "
            "(e.g., specific ideas, service providers, "
            "or concrete options relevant to completing the task)"
        ),
        min_length=1,
    )
    status: Literal["not started", "in progress", "done", "archived"] = Field(
        description="Current status of the task",
        default="not started",
    )


class UpdateMemory(TypedDict):
    """Decision on what memory type to update"""

    update_type: Literal["user", "todo", "instructions"]


model = ChatGroq(model="llama-3.3-70b-versatile", stop_sequences=None)

profile_extractor = create_extractor(
    model,
    tools=[Profile],
    tool_choice="Profile",
)

MODEL_SYSTEM_MESSAGE = dedent(
    """
    {task_maistro_role}

    You have a long term memory which keeps track of three things:
    1. The user's profile (general information about them) 
    2. The user's ToDo list
    3. General instructions for updating the ToDo list

    Here is the current User Profile (may be empty if no information has been collected yet):
    <user_profile>
    {user_profile}
    </user_profile>

    Here is the current ToDo List (may be empty if no tasks have been added yet):
    <todo>
    {todo}
    </todo>

    Here are the current user-specified preferences for updating the ToDo list (may be empty if no preferences have been specified yet):
    <instructions>
    {instructions}
    </instructions>

    Here are your instructions for reasoning about the user's messages:

    1. Reason carefully about the user's messages as presented below. 

    2. Decide whether any of the your long-term memory should be updated:
    - If personal information was provided about the user, update the user's profile by calling UpdateMemory tool with type `user`
    - If tasks are mentioned, update the ToDo list by calling UpdateMemory tool with type `todo`
    - If the user has specified preferences for how to update the ToDo list, update the instructions by calling UpdateMemory tool with type `instructions`

    3. Tell the user that you have updated your memory, if appropriate:
    - Do not tell the user you have updated the user's profile
    - Tell the user them when you update the todo list
    - Do not tell the user that you have updated instructions

    4. Err on the side of updating the todo list. No need to ask for explicit permission.

    5. Respond naturally to user user after a tool call was made to save memories, or if no tool call was made.
    """
).strip()


TRUSTCALL_INSTRUCTION = dedent(
    """
    Reflect on following interaction. 

    Use the provided tools to retain any necessary memories about the user. 

    Use parallel tool calling to handle updates and insertions simultaneously.

    System Time: {time}
    """
).strip()


CREATE_INSTRUCTIONS = dedent(
    """
    Reflect on the following interaction.

    Based on this interaction, update your instructions for how to update ToDo list items. Use any feedback from the user to update how they like to have items added, etc.

    Your current instructions are:

    <current_instructions>
    {current_instructions}
    </current_instructions>
    """
).strip()


def task_mAIstro(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Load memories from the store and use them to personalize the chatbot's response."""

    configurable = Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category
    task_maistro_role = configurable.task_maistro_role

    namespace = ("profile", todo_category, user_id)
    memories = store.search(namespace)
    if memories:
        user_profile = memories[0].value
    else:
        user_profile = None

    namespace = ("todo", todo_category, user_id)
    memories = store.search(namespace)
    todo = "\n".join(f"{mem.value}" for mem in memories)

    namespace = ("instructions", todo_category, user_id)
    memories = store.search(namespace)
    if memories:
        instructions = memories[0].value
    else:
        instructions = ""

    system_msg = MODEL_SYSTEM_MESSAGE.format(task_maistro_role=task_maistro_role, user_profile=user_profile, todo=todo, instructions=instructions)

    response = model.bind_tools([UpdateMemory], parallel_tool_calls=False).invoke([SystemMessage(content=system_msg)] + state["messages"])

    return {"messages": [response]}


def update_profile(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""

    configurable = Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category

    namespace = ("profile", todo_category, user_id)

    existing_items = store.search(namespace)

    tool_name = "Profile"
    existing_memories = [(existing_item.key, tool_name, existing_item.value) for existing_item in existing_items] if existing_items else None

    TRUSTCALL_INSTRUCTION_FORMATTED = TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat())
    updated_messages = list(merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION_FORMATTED)] + state["messages"][:-1]))

    result = profile_extractor.invoke({"messages": updated_messages, "existing": existing_memories})

    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(
            namespace,
            rmeta.get("json_doc_id", str(uuid.uuid4())),
            r.model_dump(mode="json"),
        )

    last_message: AIMessage = state["messages"][-1]  # type: ignore
    tool_calls = last_message.tool_calls
    return {"messages": [{"role": "tool", "content": "updated profile", "tool_call_id": tool_calls[0]["id"]}]}


def update_todos(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""

    configurable = Configuration.from_runnable_config(config)

    namespace = ("todo", configurable.todo_category, configurable.user_id)

    existing_items = store.search(namespace)

    tool_name = "ToDo"
    existing_memories = [(existing_item.key, tool_name, existing_item.value) for existing_item in existing_items] if existing_items else None

    updated_messages = list(
        merge_message_runs(messages=[SystemMessage(content=TRUSTCALL_INSTRUCTION.format(time=datetime.now().isoformat()))] + state["messages"][:-1])
    )

    spy = Spy()

    todo_extractor = create_extractor(model, tools=[ToDo], tool_choice=tool_name, enable_inserts=True).with_listeners(on_end=spy)

    result = todo_extractor.invoke({"messages": updated_messages, "existing": existing_memories})

    for r, rmeta in zip(result["responses"], result["response_metadata"]):
        store.put(
            namespace,
            rmeta.get("json_doc_id", str(uuid.uuid4())),
            r.model_dump(mode="json"),
        )

    last_message: AIMessage = state["messages"][-1]  # type: ignore
    tool_calls = last_message.tool_calls

    todo_update_msg = extract_tool_info(spy.called_tools, tool_name)
    return {"messages": [{"role": "tool", "content": todo_update_msg, "tool_call_id": tool_calls[0]["id"]}]}


def update_instructions(state: MessagesState, config: RunnableConfig, store: BaseStore):
    """Reflect on the chat history and update the memory collection."""

    configurable = Configuration.from_runnable_config(config)
    user_id = configurable.user_id
    todo_category = configurable.todo_category

    namespace = ("instructions", todo_category, user_id)

    existing_memory = store.get(namespace, "user_instructions")

    system_msg = CREATE_INSTRUCTIONS.format(current_instructions=existing_memory.value if existing_memory else None)
    new_memory = model.invoke(
        [SystemMessage(content=system_msg)]
        + state["messages"][:-1]
        + [HumanMessage(content="Please update the instructions based on the conversation")]
    )

    key = "user_instructions"
    store.put(namespace, key, {"memory": new_memory.content})

    last_message: AIMessage = state["messages"][-1]  # type: ignore
    tool_calls = last_message.tool_calls

    return {"messages": [{"role": "tool", "content": "updated instructions", "tool_call_id": tool_calls[0]["id"]}]}


def route_message(
    state: MessagesState, config: RunnableConfig, store: BaseStore  # pylint: disable=unused-argument
) -> Literal[END, "update_todos", "update_instructions", "update_profile"]:  # type: ignore
    """Reflect on the memories and chat history to decide whether to update the memory collection."""

    message: AIMessage = state["messages"][-1]  # type: ignore

    if len(message.tool_calls) == 0:
        return END
    else:
        tool_call = message.tool_calls[0]
        if tool_call["args"]["update_type"] == "user":
            return "update_profile"
        elif tool_call["args"]["update_type"] == "todo":
            return "update_todos"
        elif tool_call["args"]["update_type"] == "instructions":
            return "update_instructions"
        else:
            raise ValueError


builder = StateGraph(MessagesState, config_schema=Configuration)
builder.add_node(task_mAIstro)  # type: ignore
builder.add_node(update_todos)  # type: ignore
builder.add_node(update_profile)  # type: ignore
builder.add_node(update_instructions)  # type: ignore

# Define the flow
builder.add_edge(START, "task_mAIstro")
builder.add_conditional_edges("task_mAIstro", route_message)
builder.add_edge("update_todos", "task_mAIstro")
builder.add_edge("update_profile", "task_mAIstro")
builder.add_edge("update_instructions", "task_mAIstro")

# Compile the graph
graph = builder.compile()
