# Chatbot-Medical-Diagnosis

clone the repository

'''bash
project repo: https://github.com/
'''

''' bash
conda create -n medicalbot python=3.13 -y
'''

'''bash
conda activate medicalbot
'''

'''bash
pip install -r requirements.txt
'''

#from transformers import LlamaTokenizer, LlamaForCausalLM
#import torch

# Load LLaMA model and tokenizer
#model_name = "huggingface/llama-7b"  # Replace with the appropriate LLaMA model name
#tokenizer = LlamaTokenizer.from_pretrained(model_name)
#model = LlamaForCausalLM.from_pretrained(model_name)

# Generate text
#input_text = "How can I help you today?"
#inputs = tokenizer(input_text, return_tensors="pt")

# Move model to CPU (since you don't have a GPU)
#model = model.to("cpu")

# Generate response
#output = model.generate(inputs["input_ids"], max_length=50, num_return_sequences=1)
#generated_text = tokenizer.decode(output[0], skip_special_tokens=True)

#print(generated_text)

from langchain_community.llms import LlamaCpp

# Download a quantized model (e.g., Mistral-7B, ~5GB RAM usage)
#model_path = "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"

#llm = LlamaCpp(
  #  model_path=model_path,
  #  n_ctx=2048,  # Context window
  #  n_gpu_layers=40,  # Use GPU if available (set to 0 for CPU-only))
#response = llm.invoke("What are malaria symptoms?")
#print(response)