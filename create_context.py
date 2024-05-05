import openai
from openai.embeddings_utils import distances_from_embeddings


def cnt_words(text):
    # Split the text into words using whitespace as the delimiter
    words = text.split()
    # Count the number of words
    return len(words)
def create_context(
        question, df, max_len=8000, size="ada", most_usful_link=None
):
    try:
        """
        Create a context for a question by finding the most similar context from the dataframe
        """
        # Get the embeddings for the question
        q_embeddings = openai.Embedding.create(
            input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

        # Get the distances from the embeddings
        df['distances'] = distances_from_embeddings(
            q_embeddings, df['embeddings'].values, distance_metric='cosine')

        returns = []
        cur_len = 0
        most_usful_link=None
        # Sort by distance and add the text to the context until the context is too long
        for i, row in df.sort_values('distances', ascending=True).iterrows():
           
         

            # Add the length of the text to the current length
            cur_len += row['n_tokens'] + 4

            # If the context is too long, break
            if cur_len > 1800:
                print("too many coins")
                break


            # Else add it to the text that is being returned
            returns.append(row["text"])
            if cnt_words("".join(returns))>450 and len(returns)>2:
                #returns.pop()
                print(f"the amount of words on the context is getting bigger than 450 and the len of returns is bigger than 2 it is: {len(returns)}")
                #break
                
            if most_usful_link==None:
                most_usful_link = "https://"+row["title"]

        # Return the context without leading or trailing separators
        return "\n\n###\n\n".join(returns), most_usful_link

    except Exception as e:
        # Handle the error or exception as per your requirement
        print(f"An error occurred: {e}")
        # You can also log the error, raise a more specific exception, or take other appropriate actions
        return "problem with the context say somthing about error in our system"#, e
