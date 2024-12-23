import chromadb  # Assuming you have a ChromaDB client
from .gemini import get_response, get_tokens #to get gemini response # to get total no of tokens used


def access_collection(dbname):
    # Create a persistent ChromaDB client
    client = chromadb.PersistentClient(path="C:\\Users\\abhis\\OneDrive\\Desktop\\Admin\\klaw\\db")

    """

    persist_directory="db/": This tells ChromaDB where to save its data on your computer. 
    The "db/" means it will create a folder named "db" in your current working directory to store all the information.


    """



    # Create a collection for storing your PDF data
    collection = client.get_or_create_collection(name=dbname)  # collection is a cabinet for holding all of your files.

    print("db accessed successfully")

    return collection


def chat(question, collection_name):
    """
    This function fetches relevant context from a ChromaDB collection
    and sends it along with the question to Gemini for a response.

    Parameters:
    - question (str): The user's question.
    - collection_name (str): The name of the ChromaDB collection to query.

    Returns:
    - response_text (str): The response from Gemini.
    - input_tokens (int): The number of input tokens used.
    - output_tokens (int): The number of output tokens generated.
    """
    
    # Fetch relevant context from ChromaDB
    collection = access_collection(collection_name)
    relevant_contexts = collection.query(
        query_texts= [f"{question}"], 
        n_results=5
        )  # Fetch top 5 relevant contexts
    #print(f"relevant context feteched : \n {relevant_contexts}")

    # Combine context with the question
    combined_input = f"{question}\nContext: {relevant_contexts}"

    #print (f"Combined input: {combined_input}")
    
    # Generate content using Gemini model
    response = get_response(combined_input)

    # Extract token counts
    input_tokens = get_tokens(combined_input)  
    output_tokens = get_tokens(str(response))
    
    return response.text, input_tokens, output_tokens
    #return response.text, input_tokens



