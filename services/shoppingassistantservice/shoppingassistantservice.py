#!/usr/bin/python
#
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import boto3
from urllib.parse import unquote
from langchain_core.messages import HumanMessage
from langchain_aws import ChatBedrock, BedrockEmbeddings
from flask import Flask, request
from langchain_postgres import PGVector

# AWS Configuration
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
DB_HOST = os.environ["DB_HOST"]
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ["DB_NAME"]
DB_TABLE_NAME = os.environ["DB_TABLE_NAME"]
DB_SECRET_NAME = os.environ["DB_SECRET_NAME"]

# Get database password from AWS Secrets Manager
secrets_client = boto3.client('secretsmanager', region_name=AWS_REGION)
secret_response = secrets_client.get_secret_value(SecretId=DB_SECRET_NAME)
secret_data = json.loads(secret_response['SecretString'])
DB_USERNAME = secret_data.get('username', 'postgres')
PGPASSWORD = secret_data.get('password')

# Create PostgreSQL connection string for RDS
connection_string = f"postgresql+psycopg2://{DB_USERNAME}:{PGPASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a synchronous connection to our vectorstore using AWS RDS PostgreSQL with pgvector
vectorstore = PGVector(
    connection=connection_string,
    collection_name=DB_TABLE_NAME,
    embeddings=BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v1",
        region_name=AWS_REGION
    )
)

def create_app():
    app = Flask(__name__)

    @app.route("/", methods=['POST'])
    def talkToBedrock():
        print("Beginning RAG call with AWS Bedrock")
        prompt = request.json['message']
        prompt = unquote(prompt)

        # Step 1 – Get a room description from AWS Bedrock Claude with vision
        llm_vision = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region_name=AWS_REGION,
            model_kwargs={"max_tokens": 2000, "temperature": 0.7}
        )

        # For vision models in Bedrock, format the message with image
        vision_prompt = "You are a professional interior designer, give me a detailed description of the style of the room in this image"
        if 'image' in request.json and request.json['image']:
            # Note: Bedrock Claude vision requires base64 encoded images
            # The image URL/data should be preprocessed before calling
            message = HumanMessage(content=vision_prompt)
        else:
            message = HumanMessage(content=vision_prompt)

        response = llm_vision.invoke([message])
        print("Description step:")
        print(response)
        description_response = response.content

        # Step 2 – Similarity search with the description & user prompt
        vector_search_prompt = f""" This is the user's request: {prompt} Find the most relevant items for that prompt, while matching style of the room described here: {description_response} """
        print(vector_search_prompt)

        docs = vectorstore.similarity_search(vector_search_prompt)
        print(f"Vector search: {description_response}")
        print(f"Retrieved documents: {len(docs)}")
        # Prepare relevant documents for inclusion in final prompt
        relevant_docs = ""
        for doc in docs:
            doc_details = doc.page_content if hasattr(doc, 'page_content') else str(doc)
            print(f"Adding relevant document to prompt context: {doc_details}")
            relevant_docs += str(doc_details) + ", "

        # Step 3 – Tie it all together by augmenting our call to AWS Bedrock Claude
        llm = ChatBedrock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region_name=AWS_REGION,
            model_kwargs={"max_tokens": 2000, "temperature": 0.7}
        )
        design_prompt = (
            f" You are an interior designer that works for Online Boutique. You are tasked with providing recommendations to a customer on what they should add to a given room from our catalog. This is the description of the room: \n"
            f"{description_response} Here are a list of products that are relevant to it: {relevant_docs} Specifically, this is what the customer has asked for, see if you can accommodate it: {prompt} Start by repeating a brief description of the room's design to the customer, then provide your recommendations. Do your best to pick the most relevant item out of the list of products provided, but if none of them seem relevant, then say that instead of inventing a new product. At the end of the response, add a list of the IDs of the relevant products in the following format for the top 3 results: [<first product ID>], [<second product ID>], [<third product ID>] ")
        print("Final design prompt: ")
        print(design_prompt)
        design_response = llm.invoke(design_prompt)

        data = {'content': design_response.content}
        return data

    return app

if __name__ == "__main__":
    # Create an instance of flask server when called directly
    app = create_app()
    app.run(host='0.0.0.0', port=8080)
