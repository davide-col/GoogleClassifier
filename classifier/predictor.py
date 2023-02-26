from constants import LABELS
from datetime import datetime

class Predictor :
    """Classe permettant de gérer tout ce qui est lié à la labellisation des articles
    
    Attributs:
    df (array) : Array contenant le modèle TFIDF de(s) article(s) à labelliser
    dict (dict) : Dictionnaire contenant les associations Labels/article
    """

    def __init__(self, df) :
        self.df = df
        self.dict = {'Agences de notation' : [],'Lutte contre le blanchiment d argent et le financement du terrorisme' : [],
        'MAR (abus de marché)' : [],'MiFID' : [],'Normes comptables et reportings financiers' : [],
        "Portefeuilles d'investissement" : [], 'Priips' : [],'Reglementation Volcker' : [],'Sanctions' : [], "Autres" : []}

    def predict_one(self, model, title) :
        """Fais la prédiction pour le dataset donné correspondant à un article lors de l'instanciation de 
        l'objet et enregistre l'url associés à son/ses label(s).
        
        Paramètres :
        model : modèle choisi pour la prédiction
        title (string) : titre de l'article labellisé (sert d'identifiant)

        Return :
        dict : dictionnaire contenant les différents labels en clés et le titre de l'article correspondant en valeur
        """
        prediction = model.predict(self.df)
        counter = 0
        for j, label in enumerate(LABELS) :
            if prediction[0][j] != 0 :
                self.dict[label].append(title)
            else :
                counter +=1
        
        if counter == 15 :
                self.dict["Autres"].append(title)
        return self.dict

    def predict(self, model, urls) :
        """Fais la prédiction pour le dataset donnée lors de l'instanciation de l'objet et enregistre
        les urls des articles associés à leur(s) label(s).
        
        Paramètres :
        model : modèle choisi pour la prédiction
        urls (list) : urls des articles labellisés (sert d'identifiant)

        Return :
        dict : dictionnaire contenant les différents labels en clés et les urls des articles correspondant en valeurs
        """
        prediction = model.predict(self.df)
        for i, url in enumerate(urls) :
            pred = prediction[i]
            counter = 0
            for j, label in enumerate(LABELS) :

                if pred[j] != 0 :
                    self.dict[label].append(url)
                else :
                    counter += 1

            if counter == len(LABELS) :
                self.dict["Autres"].append(url)
        return self.dict