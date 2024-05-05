from flask_socketio import SocketIO, join_room
from urllib.parse import urlparse
from generate_answer import gpt
from web_crawler import crawl_using_threads
import os
from flask_cors import CORS  # Import CORS extension
from web_crawler import crawl_using_threads
from urllib.parse import urlparse
from flask import Flask, request, jsonify
from google_drive_api import check_gcs_directory,upload_html_2gcd
import time
from ask_the_owner import ask_the_owner
import openai
from twilio.twiml.messaging_response import MessagingResponse



print("start_dialogix_app")
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)
def simulate_streaming():

    """
    simulate straming answer by generate random strings . 

    """
    words = ["papa", "banana", "apple", "orange", "grape", "kiwi", "peach", "melon", "strawberry", "blueberry"]
    cnt=0
    semi_final_chunk="\nRelated link:"
    final_chunk_link="\nhttps://chat.openai.com/c/ranito6."
    
    for _ in range(10):
        cnt+=1
        time.sleep(1)  # Simulate some delay between chunks
        random_word = words[_]
        yield f" #test {random_word},{cnt}"
    if final_chunk_link:
        # Yield the final chunk as a hyperlink
        yield semi_final_chunk
        yield f'<a href="{final_chunk_link}" target="_blank">{final_chunk_link}</a>'
def log_conversation(file_domain,id,user_id,question,answer):
        
        """
        write the conversation as logs. if the answer is i dont know send whatsapp message to the owner.

        """

    

@app.route('/pass_url_to_db', methods=['POST','OPTIONS'])
def pass_url_to_db():
    if request.method == 'OPTIONS':
        # Handle preflight OPTIONS request
        response = jsonify({'message': 'Preflight request successful'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
    return jsonify({'lists_of_urls': "not avillable at the moment"})


@app.route('/crawl', methods=['POST','OPTIONS'])
def start_crawl():
    if request.method == 'OPTIONS':
        # Handle preflight OPTIONS request
        response = jsonify({'message': 'Preflight request successful'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
    url = request.json['url']
    print(f'this is the url that will be crawled:{url}')
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if check_gcs_directory(domain):
        print(f'the domain: {domain} has been crawled and scraped already')
        return jsonify({'stat': 'Done',
                        'domain': domain})
    print('start crawling using threads and scrape and embed from web crawler\n')
    crawl_using_threads(url)
    print('finish crawling using threads from web crawler(use_tmp\n')
    print('finish all the process of crawling')
    return jsonify({'stat': 'Done',
                    'domain': domain})

latest_message = "no"
new_message_received = False

@app.route('/whatsappwebhook', methods=['POST', 'GET'])
def whatsapp_webhook():
    global latest_message
    global new_message_received
    
    if request.method == 'POST':
        incoming_message = request.form.get('Body')
        phone_number = request.form.get('From')
        print(f"Incoming message: {incoming_message}, From: {phone_number}")

        latest_message = incoming_message
        new_message_received = True
        return str(incoming_message)
    else:  # GET request
        if new_message_received:
            new_message_received = False
            return str(latest_message)
        else:
            return "no"





    

@app.route('/', methods=['POST','OPTIONS','GET'])
def hello_world():
    return "hi and welcome to dialogix soon the documentation will be uploaded. this belong to ranito"
@app.route('/persona', methods=['POST','OPTIONS'])
def create_persona():
    # active this command for running the html files(directory)==python -m http.server 3000
    if request.method == 'OPTIONS':
        # Handle preflight OPTIONS request
        response = jsonify({'message': 'Preflight request successful'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response, 200
    print('parsona details being send..')
    website = request.json['website']
    open_line = request.json['openLine']
    rule = request.json['rule']
    botName = request.json['botName']
    language = request.json['language']
    UserId = request.json['title']
    parsed_url = urlparse(website)
    domain = parsed_url.netloc
    print(f"thats what i got: {website} , {open_line}, {rule}, {botName}, {language}, {UserId}")
    ##need to open a dir in gcd with user id
    upload_html_2gcd(website,open_line,botName,domain,UserId)
    return jsonify({'stat': 'Done',
                    'domain': website})

@socketio.on('connect', namespace='/dialogix_gpt')
def handle_connect():
    print("Client connected")

@socketio.on('disconnect', namespace='/dialogix_gpt')
def handle_disconnect():
    print("Client disconnected")

@socketio.on('message', namespace='/dialogix_gpt')
def handle_message(message):
    print('Received message:', message)
    # Set the Origin header to "*" to allow the connection
    try:
        question = message['question']
        client_id = request.sid
        join_room(client_id)
        phoneNumber=message['phoneNumber']
        if question=="hi123":
            ask_the_owner(phoneNumber,question=question)
            socketio.emit('response', {'bot_response': "i don't know\n\nrelated link:https//testtheprogram.com"}, room=client_id,namespace='/dialogix_gpt')
            socketio.emit('stream_complete_with_IDK', {'stream_complete_with_IDK': True},room=client_id, namespace='/dialogix_gpt')
            return


        if question == "hi12" or question=="what would you do if you would be ranito?":
            #ask_the_owner(phoneNumber,question=question)
            for chunk in simulate_streaming():
                print (chunk,client_id)
                socketio.sleep(0)
                socketio.emit('response', {'bot_response': chunk}, room=client_id,namespace='/dialogix_gpt')

            socketio.emit('stream_complete', {'stream_complete': True},room=client_id, namespace='/dialogix_gpt')
            print("emited answer")
            return
        
        url = message['url']
        user_id = url
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        embed_path = f"gs://dialogix-bucket1/{domain}/embeddings.csv"
        # Call your chatbot logic to generate a response
        print(embed_path)
        bot_response = gpt(question, user_id, df_path=embed_path)

        # Iterate over the generator and send each chunk over WebSocket
        response=''
        for chunk in bot_response:
            if chunk is None:  # Check for the sentinel value
                break
            socketio.emit('response',{'bot_response': chunk},room=client_id, namespace='/dialogix_gpt')
            #add some sleep for the streaming
            response+=chunk
            socketio.sleep(0)
            
        if response=="i don't know" and phoneNumber:
            ask_the_owner(phone_number=phoneNumber,question=question)
        # Send a signal indicating that the streaming is complete
        socketio.emit('stream_complete', {'stream_complete': True},room=client_id, namespace='/dialogix_gpt')
    except Exception as ex:
        print(f"Error in WebSocket server: {ex}")

