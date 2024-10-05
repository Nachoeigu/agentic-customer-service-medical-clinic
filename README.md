# agentic-customer-service-medical-dental-clinic
This software contains an agent based on LangGraph &amp; LangChain for solving general client queries and it could be implemented in whatever channel of this medical clinic (Whatsapp, Telegram, Instagram, etc).

# AI Autonomous Agent
It is highly autonomous and it is able to handle different types of secretary tasks like: give general information about the clinic, cancel, reschedule and set appointments, check doctor availability, review if your results are ready, which services the dental clinic offers, etc.


# Workflow

![image](https://github.com/user-attachments/assets/bcdac740-5a3a-42aa-8d8e-c8410a2bf675)


## Some use cases:


This is a casual chat where the agent books and reschedule books easily:

https://github.com/user-attachments/assets/cd4d9983-c2c3-4844-9bcb-4314c6137bbf

Here I provided a wrong ID number and we can see how it handle errors quite good. Also, I provided a demo of how it handle general questions with a RAG approach.

https://github.com/user-attachments/assets/d36e5a0b-0d49-4cb8-a7e4-7d68ef206c9c


# How to use

1) Set the following ENV variables

WORKDIR (The root path to the repository)
XXX_API_KEY (LLM provider you want to use)
PINECONE_API_KEY

2) If it is your first time, execute the main.py file inside the vector_database directory. This will create the Vector Database.

3) Execute the get_availability.py file inside the syntetic_data directory in order to have data up to date

4) Run the app executing agent.py / Run the app using LangGraph Studio