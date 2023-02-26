import pandas as pd
from utils import open_file
import re
from constants import VEC_PATH

class Preprocessor :
    """Classe permettant de gérer le preprocessing des articles
    
    Attributs:
    texts (list) : liste des contenus des articles
    titles (list) : liste des titres des articles
    vec (TfidfVectorizer) : Vectorizer 
    """

    def __init__(self, article=["title", "content"]) :
        self.texts = article[1]
        self.titles = article[0]
        self.vec = open_file(VEC_PATH)

    def transform_one_vec(self) :
        """Nettoie et vectorize les données pour un seul article (utile pour la route "/bdd/ajouter_articles")
        
        Return :
        df (array) : Tfidf de l'article
        """
        docs = [self.titles + self.texts]
        print(docs)
        docs = self.clean(docs)
        df = self.vec.transform(docs)
        return df

    def transform_vec(self) :
        """Nettoie et vectorize les données pour une liste d'articles
        
        Return :
        df (array) : Tfidf du corpus
        """
        docs = []
        for i in range(len(self.titles)) :
            docs.append(self.titles[i] + " " + self.texts[i])
        docs = self.clean(docs)
        df = self.vec.transform(docs)
        return df

    def clean(self, docs) :
        """Nettoyage d'un texte

        Arguments: 
        docs (list(str)) :  liste de textes a nettoyer

        Returns:
        texts (list) : liste des textes nettoyés
        """
        texts = []
        for text in docs :
            text = text.lower()
            text = re.sub(r'http+', ' ', text)
            text = re.sub(r'\d+', ' ', text)
            text = re.sub(r'\W+', ' ', text)
            text = re.sub(r'_+', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            texts.append(text)
            
        return texts