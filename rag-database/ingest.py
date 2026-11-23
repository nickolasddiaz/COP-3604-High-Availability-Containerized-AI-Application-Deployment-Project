from PyPDF2 import PdfReader 
from pdfplumber import pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from sentence_transformers import SentenceTransformer, util
import time
from gpt4all import GPT4All  

from numba import jit, cuda
import numpy as np

"""
    Build with "docker build -t rag-db-image ."
    
    Run with "docker run -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=rag-db \
    -p 5432:5432 rag-db-image"
    
    Build and run with "docker build -t rag-db-image . && \
    docker run -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=rag-db \
    -p 5432:5432 rag-db-image"
    
    Open contianer with "docker compose up"
    Close container with "docker compose down"

    If these are not the imports that you use
    then please update the Dockerfile to have
    the correct imports in requirements.txt
    
    Also, if you use sentence_transformers
    then add it to requirements.txt
"""

print("NOT YET IMPLEMENTED")