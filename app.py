from flask import Flask, render_template, request, redirect, url_for, flash, session
from multiprocessing import Process, Queue
from classifier.loader import Preprocessor
from classifier.predictor import Predictor
from flask_sqlalchemy import SQLAlchemy
import json
from utils import open_file
from scrapy.crawler import CrawlerRunner
from constants import URL_ROOT, MODEL_PATH, LABELS
import scrapy
from tqdm import tqdm
from scrapy import Request
from datetime import datetime
from twisted.internet import reactor
import time 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#Script du web service

app = Flask(__name__)

app.secret_key = "Article's labelliser"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///articles.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

model = open_file(MODEL_PATH)

class Articles(db.Model) :
    _id = db.Column("id", db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    content = db.Column(db.String(10000)) #texte de l'article
    url = db.Column(db.String(300)) # lien de l'article
    label = db.Column(db.String(1000))
    date_r=db.Column(db.String(100)) # date de redaction 
    date_e=db.Column(db.String(100)) # date d'extratcion
    source=db.Column(db.String(100)) # source d'extraction

    def __init__(self, title, content, url=None, label=json.dumps(["Aucun Label"]),date_e=date_e,date_r=date_r ,source=source) :
        self.title = title
        self.content = content
        self.url = url
        self.label = label
        self.date_e=date_e
        self.date_r=date_r
        self.source=source

class ArticleSpider(scrapy.Spider): 
    name = "url_pages"

    def start_requests(self):
        urls = ['https://www.latribune.fr/Entreprises-secteurs.html']
        for url in urls:
            print(url)
            yield Request(url, self.parse)

    def parse(self, response):
        urls = response.xpath('//ul[@class = "pagination-archive pages"]/li/a/@href').extract()
        for url in tqdm(urls):
            yield Request(URL_ROOT + url, callback=self.parse_article_url)

    def parse_article_url(self, response):
        urls = response.xpath('//article[@class = "article-wrapper row clearfix "]/div/a/@href').extract()
        new_urls = []
        for url in urls : 
            found_url = Articles.query.filter_by(url=url).first()
            if found_url is None :
                new_urls.append(url)

        for url in new_urls:
            yield Request(url, callback=self.parse_article)

    def parse_article(self, response):
        title = response.xpath('//div[@class = "article-title-wrapper"]/h1/text()').get()
        url = response.url
        paragraphs = response.xpath('//div[@class = "body-article wide"]/p/text()').getall()
        date_r=response.xpath('//div[@class = "author-article-informations"]/time/text()').get()
        date_r=date_r[:28]
        content = ' '.join(paragraphs)  
        n=datetime.now()
        l=["Jan","Feb","Mars","Avr","Mai","Juin","Juill","Août","Sept","Oct","Nov","Déc"]
        l={str(i+1):l[i] for i in range(12)}
        y=n.strftime("%Y")
        id=int(n.strftime("%m"))
        m=l[str(id)]
        d=n.strftime("%d") 
        t=d+" "+m+" " +y   
        article = Articles(title=title, content=content, url=url,date_r=date_r,date_e=t,source="La tribune")
        try :
            db.session.add(article)
            db.session.commit()
        except:
            return "Error 503 : connexion à la base de donnée impossible"
def scraping_cnil():
    print('Scraping CNIL')
    dict_1 = {'publication_type': "Publications : Rapports, études et analyses",
                            'url': 'https://www.cnil.fr/fr/actualites?field_type_article_tid=All&sort_by=field_type_article_tid&sort_order=DESC&page='
                            }

    all_articles=[]
    n_pages=2
    options = webdriver.FirefoxOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--incognito")
    # to run Firefox in headless mode
    options.add_argument("--headless")
    driver=webdriver.Firefox(options=options)
    for i in tqdm(range(1,n_pages+1)):
        driver.get(dict_1['url']+str(i))
        time.sleep(0.5)
        dates = driver.find_elements("xpath",'//*[@id="block-system-main"]/div/div[2]/div/div[1]/div[2]/div/span')
        titles = driver.find_elements("xpath",'//*[@id="block-system-main"]/div/div[2]/div/div[1]/div[2]/div/h3/a')
        refs = driver.find_elements("xpath",'//*[@id="block-system-main"]/div/div[2]/div/div[1]/div[2]/div/h3/a')

        dates_text = [i.text for i in dates]
        titles_text = [i.text for i in titles]
        content_text=[]
        refs_text = [i.get_property('href') for i in refs]
        for ref in refs_text:
            driver.get(ref)
            paragraphs=driver.find_elements("xpath",'//*[@id="block-system-main"]/div/div/div/div/div/div/div/div/p')
            paragraphs=[i.text for i in paragraphs]
            content_text.append('\n'.join(paragraphs))
        all_articles += [[dates_text[i], titles_text[i], refs_text[i],content_text[i]] for i in range(len(dates_text))]
    driver.quit()
    for a in all_articles:
        l=["Jan","Feb","Mars","Avr","Mai","Juin","Juill","Août","Sept","Oct","Nov","Déc"]
        l={str(i+1):l[i] for i in range(12)}
        n=datetime.now()
        y=n.strftime("%Y")
        id=int(n.strftime("%m"))
        m=l[str(id)]
        d=n.strftime("%d") 
        t=d+" "+m+" " +y   
        article = Articles(title=a[1], content=a[3], url=a[2],date_r=a[0],date_e=t,source="CNIL")
        if a[2] not in [x.url for x in Articles.query.all()]:
            try :   
                    db.session.add(article)
                    db.session.commit()
            except:
                return "Error 503 : connexion à la base de donnée impossible"
    

def scraping_amf():
    print('Scraping AMF')
    dict_1 = {'publication_type': "Publications : Rapports, études et analyses",
                            'url': 'https://www.amf-france.org/fr/actualites-publications/publications/rapports-etudes-et-analyses'
                            }

    dict_2 = {'publication_type': "Communiqués : Communiqués de l AMF",
                                'url': 'https://www.amf-france.org/fr/actualites-publications/communiques/communiques-de-lamf'
                            }

    dict_3 = {'publication_type': "Actualités",
                        'url': 'https://www.amf-france.org/fr/actualites-publications/actualites'
                        }

    dict_4 = {'publication_type': "Communiqués : Communiqués de la Commission des sanctions",
                                'url': 'https://www.amf-france.org/fr/actualites-publications/communiques/communiques-de-la-commission-des-sanctions'
                            }

    dict_5 = {'publication_type': "Publications SPOT",
                            'url': 'https://www.amf-france.org/fr/actualites-publications/publications/syntheses-des-controles-spot'
                            }

    publication_type_list = [dict_1,
                            dict_2,
                            dict_3,
                            dict_4,
                            dict_5]


    all_articles=[]
    options = webdriver.FirefoxOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--incognito")
    # to run Firefox in headless mode
    options.add_argument("--headless")
    driver=webdriver.Firefox(options=options)
    num_pages=3
    for publication_type in tqdm(publication_type_list):
        driver.get(publication_type['url'])
        articles_list=[]
        for i in range(num_pages):
            dates = driver.find_elements("xpath",'//*[@id="DataTables_Table_0"]/tbody/tr[*]/td[1]/span')
            titles = driver.find_elements("xpath",'//*[@id="DataTables_Table_0"]/tbody/tr[*]/td[3]/a/p')
            themes = driver.find_elements("xpath",'//*[@id="DataTables_Table_0"]/tbody/tr[*]/td[2]/span')
            refs = driver.find_elements("xpath",'//*[@id="DataTables_Table_0"]/tbody/tr[*]/td[3]/a')

            dates_text = [i.text for i in dates]
            titles_text = [i.text for i in titles]
            themes_text = [i.text for i in themes]
            refs_text = [i.get_property('href') for i in refs]
            content_text = []
            for ref in refs_text:
                driver.get(ref)
                paragraphs=driver.find_elements("xpath",'//*[@id="block-amf-content"]/div[2]/div/div[2]/div/div[2]/div[3]/div/p')
                paragraphs=[i.text for i in paragraphs]
                content_text.append('\n'.join(paragraphs))
            driver.get(publication_type['url'])
            articles_list += [[dates_text[i], titles_text[i], themes_text[i], refs_text[i],content_text[i]] for i in range(len(dates_text))]
            wait = WebDriverWait(driver, 10)
            el_ = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="DataTables_Table_0"]/tbody/tr[1]/td[3]/a/p')))
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            done=0
            while done!=1:
                try:
                    el2_=wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="DataTables_Table_0_next"]')))
                    nextpage=driver.find_element("xpath",'//*[@id="DataTables_Table_0_next"]')
                    nextpage.click()
                    done=1
                except:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    try:
                        message_element = driver.find_element(By.XPATH,'//*[@id="popin-on-load"]/button')
                        message_element.click()
                    except:
                        pass
                    done=-1

        all_articles+=articles_list
    driver.quit()
    for a in all_articles:
        l=["Jan","Feb","Mars","Avr","Mai","Juin","Juill","Août","Sept","Oct","Nov","Déc"]
        l={str(i+1):l[i] for i in range(12)}
        n=datetime.now()
        y=n.strftime("%Y")
        id=int(n.strftime("%m"))
        m=l[str(id)]
        d=n.strftime("%d") 
        t=d+" "+m+" " +y   
        article = Articles(title=a[1], content=a[4], url=a[3],date_r=a[0],date_e=t,source="AMF")
        if a[3] not in [x.url for x in Articles.query.all()]:
            try : 
                db.session.add(article)
                db.session.commit()
            except:
                return "Error 503 : connexion à la base de donnée impossible"
                
def scraping(q) :
    try : 
        runner = CrawlerRunner()
        print("Scraping en cours")
        print("Scraping La tribune")
        deffered = runner.crawl(ArticleSpider)

        deffered.addBoth(lambda _: reactor.stop())
        reactor.run()
        q.put(None)

    except Exception as e :
        q.put(e)

@app.route('/')
def home() :
    return render_template("home.html")

@app.route("/labelliser")
def labellise() :
    articles = Articles.query.filter_by(label='["Aucun Label"]').all()
    titles = []
    texts = []
    urls = []
    dates_e=[]
    dates_r=[]
    for article in articles :
        titles.append(article.title)
        texts.append(article.content)
        urls.append(article.url)
        dates_e.append(article.date_e)
        dates_r.append(article.date_r)
    if titles == [] :
        flash('aucun article')
        return redirect(url_for('home'))

    #Preprocessing
    loader = Preprocessor()
    loader.texts = texts
    loader.titles = titles
    df = loader.transform_vec()

    #Labellisation
    predictor = Predictor(df)
    dict = predictor.predict(model, urls)
    #Upadating database
    urls = []
    for cat in dict :
        liste = dict[cat]
        for url in liste :
            if url not in urls :
                urls.append(url)
                labels = [cat]
                for category in dict :
                    if category != cat :
                        if url in dict[category] :
                            labels.append(category)
                article = Articles.query.filter_by(url=url).first()
                labels = json.dumps(labels)
                article.label = labels
    db.session.commit()
    flash('Labellisation terminée')
    return redirect(url_for(('home')))

@app.route("/scraper")
def scraper() :
    print("Debut scraping", str(datetime.now().time()))
    try :
        q = Queue()
        p = Process(target=scraping, args=(q,))
        p.start()
        result = q.get()
        p.join()
        if result is not None:
            raise result
        scraping_amf()
        scraping_cnil()
        print('Scraping terminé', str(datetime.now().time()))
        return redirect(url_for("labellise"))
    except :
        return "Error 500 : Scraping impossible"

@app.route("/bdd", methods=['GET', 'POST'])
def consulter_bdd() :
    if request.method == 'POST' :
        labels = request.form.keys()
        query = Articles.query.all()
        articles = []
        for article in query :
            article_labels = json.loads(article.label)
            for lab in article_labels :
                if lab in labels :
                    articles.append(article)
        articles = list(reversed(articles))
        return render_template("bdd.html", articles=articles, length=len, json_module=json, LABELS=LABELS)
    articles = list(reversed(Articles.query.all()))
    return render_template("bdd.html", articles=articles, length=len, json_module=json, LABELS=LABELS)

@app.route("/bdd/ajouter_article", methods=['POST', 'GET'])
def classifier() :
    if request.method == 'POST' :
        content = request.form['content']
        title = request.form['title']
        date_r = request.form["date de rédaction"]
        date_e = request.form["date d'extraction"]
        source=request.form["source"]
        found_article = Articles.query.filter_by(title=title).first()
        if not found_article :
            art = Articles(title, content, url=f"/articles/{title}",date_e=date_e,date_r=date_r,source=source)
            db.session.add(art)
            db.session.commit()

        article = [title, content]

        #Preprocessing
        loader = Preprocessor(article=article)
        df = loader.transform_one_vec()

        #Classifying
        predictor = Predictor(df)
        dict = predictor.predict_one(model, title)

        #Upadating database
        labels = []
        for key in dict :
            if dict[key] != [] :
                labels.append(key)

        article = Articles.query.filter_by(title=title).first()
        label = json.dumps(labels)
        article.label = label
        db.session.commit()
        
        flash('article ajouté')
        return redirect(url_for("consulter_bdd"))

    return render_template("ajout_article.html")

@app.route("/bdd/empty")
def empty() :
    articles = Articles.query.all()
    for article in articles :
        db.session.delete(article)
    try :
        db.session.commit()
    except :
        return "Error 503 : connexion à la base de donnée impossible"
    flash("Base de données vidée")
    return redirect(url_for('home'))

@app.route("/bdd/update", methods=['GET', 'POST'])
def modifier_label() :
    if request.method == 'POST' :
        if "title" in request.form :
            title = request.form['title']
        else :
            title = session['title']

        article = Articles.query.filter_by(title=title).first()

        if article is None : 
            return "Error 422 : Article not found"

        labels = list(request.form.keys())
        print('labels')
        print(labels)
        print(request.form)
        flash("L'article a été modifié", "info")
        article.label = json.dumps(labels)
        try :
            db.session.commit()
        except :
            return "Error 503 : connexion à la base de donnée impossible"
        return redirect(url_for("consulter_bdd"))

    title = request.args['title']
    session['title'] = title
    return render_template("update.html")

@app.route("/bdd/delete", methods=['GET'])
def delete() :
    title = request.args['title']
    article = Articles.query.filter_by(title=title).first()
    if article is None : 
        return "Error 422 : Article not found"
    try :
        db.session.delete(article)
        db.session.commit()
    except :
        return "Error 503 : connexion à la base de donnée impossible"
    flash("L'article a été supprimé")
    return redirect(url_for("consulter_bdd"))

if __name__ == "__main__" :
    db.create_all()
    app.run(debug=True, port=8000)