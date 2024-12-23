#from admin.add import add
#from admin.create import access_collection
from reply import chat


#sample usage
#access_collection("abd441")  # function to create a vectordb collection
#add("abd544","pdf_files/India.pdf")  # to access the collection and store pdf files one by one.

# Example usage of chat functionality:
response_text, input_tokens, output_tokens = chat("What is the capital of india now and in old times?", "abd544")  # (user question , dbname / course code / collection)


print(f"Response: {response_text}")
print(f"Input Tokens: {input_tokens}, Output Tokens: {output_tokens}")