import os
import pickle
import numpy as np
from typing import List
from langchain.embeddings.base import Embeddings
from sklearn.feature_extraction.text import TfidfVectorizer

class TFIDFEmbeddings(Embeddings):
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=384)
        self.fitted = False

    def _fit_and_transform(self, texts: List[str]) -> List[List[float]]:
        vectors = self.vectorizer.fit_transform(texts)
        self.fitted = True
        return vectors.toarray().tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._fit_and_transform(texts)

    def embed_query(self, text: str) -> List[float]:
        if not self.fitted:
            self.vectorizer.fit([text])
            self.fitted = True
        vector = self.vectorizer.transform([text])
        return vector.toarray()[0].tolist()

def get_embeddings() -> TFIDFEmbeddings:
    return TFIDFEmbeddings()