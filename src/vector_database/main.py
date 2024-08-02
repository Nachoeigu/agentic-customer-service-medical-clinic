import os
from dotenv import load_dotenv
import sys

load_dotenv()
WORKDIR=os.getenv("WORKDIR")
os.chdir(WORKDIR)
sys.path.append(WORKDIR)

from src.vector_database.utils import PineconeManagment

def deploy_vectordatabase(index_name):
    vdb_app = PineconeManagment()
    docs = vdb_app.reading_datasource()
    vdb_app.creating_index(index_name = index_name, docs = docs)



if __name__ == '__main__':
    deploy_vectordatabase(index_name = 'ovidedentalclinic')