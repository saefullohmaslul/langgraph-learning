from langchain_groq import ChatGroq
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition


def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First number.
        b: Second number.

    Returns:
        int: The product of the two numbers.
    """
    return a * b


llm = ChatGroq(model="llama3-8b-8192", stop_sequences=None)
llm_with_tools = llm.bind_tools([multiply])


def tool_calling_llm(state: MessagesState):
    """Tool calling LLM node.

    Args:
        state (MessagesState): The current state of the assistant.

    Returns:
        MessagesState: The updated state of the assistant.
    """
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges("tool_calling_llm", tools_condition)
builder.add_edge("tools", END)

graph = builder.compile()
