# Chatbot-Medical-Diagnosis

clone the repository

'''bash
project repo: https://github.com/
'''

''' bash
conda create -n medical_demo python=3.11 -y
'''

'''bash
conda activate medical_demo
'''

'''bash
pip install -r requirements.txt
'''



#from langchain_community.llms import LlamaCpp

# Download a quantized model (e.g., Mistral-7B, ~5GB RAM usage)
#model_path = "TheBloke/Mistral-7B-Instruct-v0.1-GGUF"

#llm = LlamaCpp(
  #  model_path=model_path,
  #  n_ctx=2048,  # Context window
  #  n_gpu_layers=40,  # Use GPU if available (set to 0 for CPU-only))
#response = llm.invoke("What are malaria symptoms?")
#print(response)