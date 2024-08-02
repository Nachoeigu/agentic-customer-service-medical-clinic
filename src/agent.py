import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, MessagesState
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated, List, Dict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
import operator
from src.vector_database.utils import PineconeManagment
import logging
import logging_config

logger = logging.getLogger(__name__)

def loading_retriever(app):
    app.loading_vdb(index_name = 'ovidedentalclinic')
    retriever = app.vdb.as_retriever(search_type="similarity", 
                                    search_kwargs={"k": 2})
    
    return retriever

def format_retrieved_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


pinecone_conn = PineconeManagment()
pinecone_conn.loading_vdb(index_name = 'ovidedentalclinic')

retriever = pinecone_conn.vdb.as_retriever(search_type="similarity", 
                                    search_kwargs={"k": 2})

rag_chain = retriever | format_retrieved_docs

class MessagesState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]

# Define the tools for the agent to use
@tool
def check_availability(desired_date=False):
    """Checking the database if the doctor has availability"""
    return True

@tool
def reschedule_appointment(old_date, new_date, dni_number):
    """Rescheduling an appointment"""
    return True

@tool
def set_appointment(date, dni_number):
    """Set appointment with the doctor"""
    return True

@tool
def check_results(dni_number):
    """Check if the result of the pacient is available"""
    return True

@tool
def reminder_appointment(dni_number):
    """Returns when the pacient has its appointment with the doctor"""
    return "You have for next monday at 7 am"

@tool
def retrieve_faq_info(question):
    """Retrieve documents from general questions about the medical clinic"""
    return rag_chain.invoke(question)

tools = [retrieve_faq_info, set_appointment, reminder_appointment, check_availability, check_results,reschedule_appointment, reschedule_appointment]

tool_node = ToolNode(tools)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
model = model.bind_tools(tools)
from langchain.prompts import ChatPromptTemplate
from datetime import datetime



def should_continue(state: MessagesState) -> Literal["tools", "human_feedback"]:
    messages = state['messages']
    last_message = messages[-1]
    if last_message.tool_calls:
        return "tools"
    return "human_feedback"

def should_continue_with_feedback(state: MessagesState) -> Literal["agent", "end"]:
    messages = state['messages']
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        return "agent"
    return "end"


def call_model(state: MessagesState):
    messages = state['messages']
    
    response = model.invoke(messages)
    return {"messages": [response]}

def read_human_feedback(state: MessagesState):
    if state['messages'][-1].tool_calls == []:
        logger.info("AI: \n"+ state['messages'][-1].content)
        user_msg = input("Reply: ")
        return {'messages': [HumanMessage(content = user_msg)]}
    else:
        pass

workflow = StateGraph(MessagesState)

workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)
workflow.add_node("human_feedback", read_human_feedback)


workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"human_feedback": 'human_feedback',
     "tools": "tools"}
)


workflow.add_conditional_edges(
    "human_feedback",
    should_continue_with_feedback,
    {"agent": 'agent',
     "end": END}
)


workflow.add_edge("tools", 'agent')
workflow.add_edge("agent", 'human_feedback')


checkpointer = MemorySaver()

app = workflow.compile(checkpointer=checkpointer)

if __name__ == '__main__':
    final_state = app.invoke(
        {"messages": [
            SystemMessage(content=f"You are helpful assistant in Ovide Clinic, dental care center in California (United States). Your job is to solve the query of this customer. As reference, the current hour is {datetime.now().strftime('%Y-%m-%d %H:%M')}"),
            HumanMessage(content="Is it open tomorrow morning?")
            ]},
        config={"configurable": {"thread_id": 42}}
    )
    logger.info(final_state["messages"][-1].content)