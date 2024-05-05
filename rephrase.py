
import openai

def is_welcoming_message(text):
    # List of common welcoming messages
    welcoming_messages = ["hello", "hi", "hey", "howdy", "greetings"]

    # Check if the text is a welcoming message (case-insensitive)
    return text.lower() in welcoming_messages


def reprhase_follow_up_Q(chat_history, question, model='gpt-3.5-turbo-instruct', max_len=1800, size="ada", max_tokens=150, stop_sequence=None):
    chat_history_text = '\n'.join(
        [f"{item['role']}: {item['content']}" for item in chat_history])
    if is_welcoming_message(question):
        return question

    try:
        # Create the prompt
        prompt = (
            f"Rephrase the following question to make it clear and able to stand alone without needing prior context. "
            f"Ensure that the language of the original question is retained. Use the provided chat history for reference:\n\n"
            f"Chat History:\n{chat_history_text}\n\n"
            f"Original Question: {question}\n\n"
            f"Rephrased Question:"
        )
        # Call the OpenAI API
        response = openai.Completion.create(
            prompt=prompt,
            temperature=0.2,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            stop=stop_sequence,
            model=model,
        )

        answer = response["choices"][0]["text"].strip()

        if answer != "I don't know.":
            return answer
        else:
            print(f"Rephrased question is: {question}")
            return question
    except Exception as e:
        print(e)

