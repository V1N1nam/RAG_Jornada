from app.services.vectorstore_service import load_vectorstore
import numpy as np

vs = load_vectorstore()

# pega o primeiro vetor
vec = vs.index.reconstruct(0)

print("Primeiros valores do embedding:")
print(vec[:10])