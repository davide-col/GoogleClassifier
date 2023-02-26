import pickle

def save_object(object, filename):
    """Enregistre un objet"""
    f = open(filename, 'wb')
    pickle.dump(object, f)
    f.close()

def open_file(filename):
    """Ouvre un objet enregistré"""
    f = open(filename, 'rb')
    object = pickle.load(f)
    f.close()
    return object