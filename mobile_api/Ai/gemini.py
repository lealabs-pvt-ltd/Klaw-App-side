#print("klaw app successfully made")

#program that contains function to get responses from gemini

import google.generativeai as genai
import os
from dotenv import load_dotenv


from vertexai.preview import tokenization # for counting the no of tokens

# Load environment variables from .env file
load_dotenv()

genai.configure(api_key = os.getenv("GOOGLE_API_KEY"))


model_name = "gemini-1.5-flash"

model = genai.GenerativeModel(model_name)

"""

this function is responsible for sending the gemini response. 
the input parameter is the question itself. 
the output or the return is the response

"""

def get_response(user_input):

    response = model.generate_content(user_input)
    #print(response.text)

    return response


def get_tokens(contents):
    tokenizer = tokenization.get_tokenizer_for_model(model_name)

    result = tokenizer.count_tokens(contents)
    total_tokens = result.total_tokens

    #print(f"{result.total_tokens = :,}")

    

    return total_tokens