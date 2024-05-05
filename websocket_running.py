
import json
import websockets
from urllib.parse import urlparse
from semi import gpt
from scrape_and_embed import scrape_and_embed
from web_crawler import crawl_using_threads
import os
import requests
import re
import urllib.request
from bs4 import BeautifulSoup
from collections import deque
from html.parser import HTMLParser
from urllib.parse import urlparse
import os
import pdfCrawl
import threading
from queue import Queue
from seperate_words import separate_text_file
import concurrent
import concurrent.futures
import openai
import pandas as pd
import tiktoken
from websockets import WebSocketServerProtocol, InvalidOrigin, Headers,Origin
from typing import Optional, Sequence, cast
async def handle_connection(websocket, path):
    print(path)
    # Set the Origin header to "*" to allow the connection
    websocket.request_headers['Origin'] = "*"
    if path=='/dialogix_gpt':
        try:
            while True:
                data = await websocket.recv()
                message = json.loads(data)
                question = message['question']
                if question=="hi12":
                    await websocket.send(json.dumps({'bot_response': "hi whatou are the AI assistant, designed to provide helpful information and guidance on various topics. Please offer informative and concise responses based on the context provided in this conversation. If you encounter a question for which there is no specific guideline available, kindly respond with 'I don't know.'?"}))
                    break
                url =  message['url']
                #url="https://jillparis.com/"
                user_id = url
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                embed_path = f'processed/embeddings{domain}.csv'
                # Call your chatbot logic to generate a response
                bot_response = gpt(question, user_id, df_path=embed_path)

                # Iterate over the generator and send each chunk over WebSocket

                for chunk in bot_response:
                    if chunk is None:  # Check for the sentinel value

                        break
                    await websocket.send(json.dumps({'bot_response': chunk}))

                # Send a signal indicating that the streaming is complete
                await websocket.send(json.dumps({'stream_complete': True}))
        except Exception as ex:
            print(f"Error in WebSocket server: {ex}")
    if path == '/dialogix_crawl':
        async def scrape_and_embed(domain):
            ################################################################################
            # Step 5
            ################################################################################

            def remove_newlines(serie):
                serie = serie.str.replace('\n', ' ')
                serie = serie.str.replace('\\n', ' ')
                serie = serie.str.replace('  ', ' ')
                serie = serie.str.replace('  ', ' ')
                return serie

            ################################################################################
            # Step 6
            ################################################################################

            # Create a list to store the text files
            texts = []

            # Get all the text files in the text directory
            for file in os.listdir("text/" + domain + "/"):
                # Open the file and read the text
                with open("text/" + domain + "/" + file, "r", encoding="UTF-8") as f:
                    text = f.read()
                    # Omit the first 11 lines and the last 4 lines, then replace -, _, and #update with spaces.
                    texts.append((file[:-4].replace('_', '/'), text))
                    #await websocket.send(json.dumps({'url_response': (texts[-1][0])}))

                    # Create a dataframe from the list of texts
            df = pd.DataFrame(texts, columns=['fname', 'text'])

            # Set the text column to be the raw text with the newlines removed
            df['text'] = df.fname + ". " + remove_newlines(df.text)
            scraped_path = f'processed/scraped{domain}.csv'
            df.to_csv(scraped_path)
            ################################################################################
            # Step 7
            ################################################################################

            # Load the cl100k_base tokenizer which is designed to work with the ada-002 model
            tokenizer = tiktoken.get_encoding("cl100k_base")

            df = pd.read_csv(scraped_path, index_col=0)
            df.columns = ['title', 'text']

            # Tokenize the text and save the number of tokens to a new column
            df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

            # Visualize the distribution of the number of tokens per row using a histogram
            df.n_tokens.hist()

            ################################################################################
            # Step 8
            ################################################################################

            max_tokens = 8191

            # Function to split the text into chunks of a maximum number of tokens

            def split_into_many(text, max_tokens=max_tokens):
                # Split the text into sentences
                sentences = text.split('. ')

                # Get the number of tokens for each sentence
                n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]

                chunks = []
                tokens_so_far = 0
                chunk = []

                # Loop through the sentences and tokens joined together in a tuple
                for sentence, token in zip(sentences, n_tokens):
                    # If the number of tokens so far plus the number of tokens in the current sentence is greater
                    # than the max number of tokens, then add the chunk to the list of chunks and reset
                    # the chunk and tokens so far

                    if tokens_so_far + token > max_tokens:
                        # Check if adding this chunk would exceed 8192 tokens

                        chunks.append(". ".join(chunk) + ".")
                        chunk = []
                        tokens_so_far = 0

                    # If the number of tokens in the current sentence is greater than the max number of
                    # tokens, go to the next sentence
                    if token > max_tokens:
                        continue

                    # Otherwise, add the sentence to the chunk and add the number of tokens to the total
                    chunk.append(sentence)
                    tokens_so_far += token + 1

                # Add the last chunk to the list of chunks
                if chunk:
                    chunks.append(". ".join(chunk) + ".")

                return chunks

            shortened = []
            cnt_tokens = 0
            # Loop through the dataframe
            for row in df.iterrows():
                # If the text is None, go to the next row
                if row[1]['text'] is None:
                    continue

                # If the number of tokens is greater than the max number of tokens, split the text into chunks
                if row[1]['n_tokens'] > max_tokens:
                    shortened += split_into_many(row[1]['text'])

                # Otherwise, add the text to the list of shortened texts
                else:
                    shortened.append(row[1]['text'])
            ################################################################################
            # Step 9
            ################################################################################
            df['text'] = pd.Series(shortened)
            df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

            df.n_tokens.hist()
            ################################
            # step to mange rate limit errors
            ###############################
            ################################################################################
            # Step 10
            ################################################################################

            # Note that you may run into rate limit issues depending on how many files you try to embed
            # Please check out our rate limit guide to learn more on how to handle this: https://platform.openai.com/docs/guides/rate-limits

            def get_embedding(text):
                try:
                    return openai.Embedding.create(input=text, engine='text-embedding-ada-002')['data'][0]['embedding']
                except Exception as e:
                    print(f"Error generating embedding for '{text}': {e}")
                    return None

            ###there are adjustments need to be made with this pool because when the data excedded 8192 tokens there is rate limit error.
            with concurrent.futures.ThreadPoolExecutor() as executor:
                embeddings = list(executor.map(get_embedding, shortened))

            df['embeddings'] = pd.Series(embeddings)
            embed_path_concurrent = f'processed/embeddings{domain}.csv'
            df.to_csv(embed_path_concurrent)
        data_path = 'text'
        print("enter to crawling path")
        try:
            while True:
                data = await websocket.recv()
                message = json.loads(data)
                url = message['url']
                print(f'This is the URL that will be crawled: {url}')
                parsed_url = urlparse(url)
                domain = parsed_url.netloc
                final_path = f"{data_path}/{domain}"
                print(final_path)
                if os.path.isdir(final_path) :
                    print(f'the path: {final_path} has been crawled already')
                    await websocket.send(json.dumps({'stat': 'Done','domain': domain}))

                else:
                    print('start crawling using threads from web crawler\n')
                    crawl_using_threads(url)
                    print('finish crawling using threads from web crawler\n')
                    print('start scrape and embed  from scrape and embed\n')
                    await scrape_and_embed(domain)
                    print('finish all the process of crawling')
                    print('Finish crawling and streaming from web crawler\n')
                    await websocket.send(json.dumps({'stat': 'Done',
                                                     'domain': domain}))

        except Exception as ex:
            print(f"Error in WebSocket server: {ex}")


start_server = websockets.serve(
    handle_connection,
    "127.0.0.1",
    80
)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
