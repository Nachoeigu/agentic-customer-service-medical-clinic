import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from typing import Annotated, Literal, TypedDict
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
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



def format_retrieved_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


pinecone_conn = PineconeManagment()
pinecone_conn.loading_vdb(index_name = 'ovidedentalclinic')

retriever = pinecone_conn.vdb.as_retriever(search_type="similarity", 
                                    search_kwargs={"k": 2})

rag_chain = retriever | format_retrieved_docs


class MessagesState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]


from langchain_core.pydantic_v1 import constr, BaseModel, Field, validator
import re
import pandas as pd

class DateTimeModel(BaseModel):
    """
    The way the date should be structured and formatted
    """
    date: str = Field(..., description="Propertly formatted date", pattern=r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')

    @validator("date")
    def check_format_date(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$', v):
            raise ValueError("Datetime must be in the format 'YYYY-MM-DD HH:MM'")
        return v
class DateModel(BaseModel):
    """
    The way the date should be structured and formatted
    """
    date: str = Field(..., description="Propertly formatted date", pattern=r'^\d{4}-\d{2}-\d{2}$')

    @validator("date")
    def check_format_date(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError("Date must be in the format 'YYYY-MM-DD'")
        return v

    
class IdentificationNumberModel(BaseModel):
    """
    The way the DNI should be structured and formatted
    """
    dni: int = Field(..., description="identification number without dots", pattern=r'^\d{7,8}$')

    @validator("dni")
    def check_format_dni(cls, v):
        if not re.match(r'^\d{7,8}$',str(v)):
            raise ValueError("DNI must be in the format a integer value of 7 or 8 numbers without dots")
        return v
    



#All the tools to consider
@tool
def check_availability(desired_date:DateModel, specialization:Literal["general_dentist", "cosmetic_dentist", "prosthodontist", "pediatric_dentist","emergency_dentist","oral_surgeon","orthodontist"]):
    """
    Checking the database if we have availability for the specific specialization.
    The parameters should be mentioned by the user in the query
    """
    desired_date = desired_date.date
    #Dummy data
    df = pd.read_csv(f"{WORKDIR}/data/syntetic_data/availability.csv")
    rows = df[(df['date_slot'].apply(lambda x : x.split(' ')[0]) == desired_date)&(df['specialization'] == specialization)&(df['is_available'] == True)][['doctor_name','date_slot']]
    logger.info(rows)
    if len(rows) == 0:
        output = "No availability in the entire day"
    else:
        output = '\n'.join(', '.join(f"{col}: {row[col]}" for col in rows.columns) for _, row in rows.iterrows())

    return output

@tool
def reschedule_appointment(old_date:DateTimeModel, new_date:DateTimeModel, dni_number:IdentificationNumberModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Rescheduling an appointment.
    The parameters should be mentioned by the user in the query.
    """
    return True

@tool
def cancel_appointment(date:DateTimeModel, dni_number:IdentificationNumberModel, doctor_name:Literal['kevin anderson','robert martinez','susan davis','daniel miller','sarah wilson','michael green','lisa brown','jane smith','emily johnson','john doe']):
    """
    Canceling an appointment.
    The parameters should be mentioned by the user in the query.
    """
    return True

@tool
def get_catalog_specialists():
    """
    Obtain information about the doctors and specializations/services we provide.
    The parameters should be mentioned by the user in the query
    """
    with open(f"{WORKDIR}/data/catalog.json","r") as file:
        file = json.loads(file.read())
    
    return file

@tool
def set_appointment(desired_date:DateTimeModel, dni_number:IdentificationNumberModel, specialization:Literal["general_dentist", "cosmetic_dentist", "prosthodontist", "pediatric_dentist","emergency_dentist","oral_surgeon","orthodontist"]):
    """
    Set appointment with the doctor.
The parameters should be mentioned by the user in the query.
    """
    return True

@tool
def check_results(dni_number:IdentificationNumberModel):
    """
    Check if the result of the pacient is available.
    The parameters should be mentioned by the user in the query
    """
    return True

@tool
def reminder_appointment(dni_number:IdentificationNumberModel):
    """
    Returns when the pacient has its appointment with the doctor
    The parameters should be mentioned by the user in the query
    """
    return "You have for next monday at 7 am"

@tool
def retrieve_faq_info(question:str):
    """
    Retrieve documents or additional info from general questions about the medical clinic.
    Call this tool if question is regarding center:
    For example: is it open? Do you have parking? Can  I go with bike? etc...
    """
    return rag_chain.invoke(question)

tools = [cancel_appointment, get_catalog_specialists, retrieve_faq_info, set_appointment, reminder_appointment, check_availability, check_results,reschedule_appointment, reschedule_appointment]

tool_node = ToolNode(tools)

model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
#model = ChatGoogleGenerativeAI(model = 'gemini-1.5-pro-exp-0801', temperature = 0)
model = model.bind_tools(tools = tools)
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
    if (isinstance(last_message, HumanMessage))|(last_message.get("type","") == 'human'):
        return "agent"
    return "end"


def call_model(state: MessagesState):
    messages = [SystemMessage(content=f"You are helpful assistant in Ovide Clinic, dental care center in California (United States).\nAs reference, this is the CURRENT TIME: {datetime.now().strftime('%Y-%m-%d %H:%M, %A')}.\nKeep a friendly, professional tone.\n Before calling a tool, ensure the user pass all the necesarry parameters, don´t assume parameters that it didnt say explicitly.\nDon't force users to write in the way the system needs. it is your job to understand the user indication in the correct format.")] + state['messages']
    response = model.invoke(messages)
    return {"messages": [response]}

#The commented part is because it breaks the UI with the input function
def read_human_feedback(state: MessagesState):
    # if state['messages'][-1].tool_calls == []:
    #     logger.info("AI: \n"+ state['messages'][-1].content)
    #     user_msg = input("Reply: ")
    #     return {'messages': [HumanMessage(content = user_msg)]}
    # else:
    #     pass
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


checkpointer = MemorySaver()

app = workflow.compile(checkpointer=checkpointer,
                       interrupt_before=['human_feedback'])

if __name__ == '__main__':
    final_state = app.invoke(
        {"messages": [
            HumanMessage(content="Do you have availability for tomorrow morning for dentist for my 5 years old kid?")
            ]},
        config={"configurable": {"thread_id": 42}}
    )
    logger.info(final_state["messages"][-1].content)