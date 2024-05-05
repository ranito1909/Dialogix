
# Step 1
################################################################################
from flask import Flask
import os
import pandas as pd
import openai
import numpy as np
from create_context import create_context
from ast import literal_eval
from rephrase import reprhase_follow_up_Q
from flask import Flask
app = Flask(__name__)
# Regex pattern to match a URL
HTTP_URL_PATTERN = r'^http[s]{0,1}://.+$'
def generate_answer(
    df,
    question,
    messages,
    model="gpt-3.5-turbo-1106",
    max_len=1800,
    size="ada",
    max_tokens=150,
    stop_sequence=None,
    role=None,
    language=None
):
    try:
        context,most_useful_link = create_context(question, df, max_len=max_len, size=size)
        # Continue with further processing using 'context' and 'useful_link'
    except Exception as e:
        # Handle the error or exception as per your requirement
        print(f"An error occurred in creating context from genrate answer file : {e}")
        # You can also log the error, raise a more specific exception, or take other appropriate actions

    try:
        combined_message_content = f"You are the AI assistant, designed to provide helpful information and guidance on various topics. Please offer informative and concise responses based on the context provided in this conversation. If you encounter a question for which there is no specific guideline available, kindly respond with 'I don't know.'\n\nContext: {context}\n\nQuestion: {question}"
        messages.append({"role": "user", "content": combined_message_content})
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=max_tokens,
            stream=True
        )

        # Break the response into chunks and yield them
        for chunk in response:
            yield chunk.choices[0].delta.get("content", "")
        # Append the link to the final chunk and yield it
        print(combined_message_content)
        pre_final_chunk='\nRelated link:'
        final_chunk = f'\n<a href="{most_useful_link}" target="_blank">{most_useful_link}</a>'
        yield pre_final_chunk
        yield final_chunk

    except Exception as e:
        print(e)
        yield str(e)
# Route for handling incoming messages
chat_histories = {}

def gpt(incoming_msg, conversation_id, df_path):
    print("enterd the gpt func")
    df = pd.read_csv(df_path, index_col=0)
    df['embeddings'] = df['embeddings'].apply(literal_eval).apply(np.array)
    incoming_msg = incoming_msg
    conversation_id = conversation_id
    # Get chat history for the conversation or initialize if not present
    chat_history = chat_histories.get(conversation_id, [])
    if len(chat_history) == 8:
        chat_history.pop(0)
        chat_history.pop(0)
    # answer from the data
    answer=""
    for chunk in generate_answer(df, question=incoming_msg, messages=[]):
        answer+=str(chunk)
        yield chunk
    print(answer)
    chat_history.append({"role": "user", "content": incoming_msg})
    chat_history.append({"role": "assistant", "content": answer})
    chat_histories[conversation_id] = chat_history
    yield None
