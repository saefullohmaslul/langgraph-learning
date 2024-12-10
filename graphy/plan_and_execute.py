import operator
from textwrap import dedent
from typing import Annotated, List, Tuple, Union

from langchain import hub
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

tools = [TavilySearchResults(max_results=2)]

prompt = hub.pull("ih/ih-react-agent-executor")
prompt.pretty_print()

llm = ChatGroq(model="llama-3.3-70b-versatile", stop_sequences=None)
agent_executor = create_react_agent(llm, tools, state_modifier=prompt)


class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(description="different steps to follow, should be in sorted order")


planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "For the given objective, come up with a simple step by step plan. "
            "This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. "
            "The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.",
        ),
        (
            "placeholder",
            "{messages}",
        ),
    ]
)

planner = planner_prompt | llm.with_structured_output(Plan)


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. If you need to further use tools to get the answer, use Plan."
    )


replanner_prompt = ChatPromptTemplate.from_template(
    "For the given objective, come up with a simple step by step plan. "
    "This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. "
    "The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.\n\n"
    "Your objective was this:\n"
    "{input}\n\n"
    "Your original plan was this:\n"
    "{plan}\n\n"
    "You have currently done the follow steps:\n"
    "{past_steps}\n\n"
    "Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. "
    "Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan.",
)


replanner = replanner_prompt | llm.with_structured_output(Act)


async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))

    task = plan[0]
    task_formatted = dedent(
        f"""
        For the following plan:
        {plan_str}
        
        You are tasked with executing step {1}, {task}.
        """
    )

    agent_response = await agent_executor.ainvoke({"messages": [("user", task_formatted)]})

    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
    }


async def plan_step(state: PlanExecute):
    plan: Plan = await planner.ainvoke({"messages": [("user", state["input"])]})  # type: ignore
    return {"plan": plan.steps}


async def replan_step(state: PlanExecute):
    output: Act = await replanner.ainvoke(state)  # type: ignore

    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}


def should_end(state: PlanExecute):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"


workflow = StateGraph(PlanExecute)
workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges("replan", should_end, ["agent", END])

graph = workflow.compile()
