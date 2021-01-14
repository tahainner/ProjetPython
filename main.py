"""
Created on Wed Jan  13 2020

@author: Belrhiatia, Amghar et El Amraoui
"""

import datetime as dt
from gensim.summarization.summarizer import summarize
import praw
import urllib.request
import xmltodict
import string
import stop_words
import matplotlib.pyplot as plt
import pandas as pd
from tkinter import *
from tkinter import ttk

#
# classe mère permettant de modéliser un Document (au sens large)
#

class Corpus():

    def __init__(self, name):
        self.name = name
        self.collection = {}
        self.authors = {}
        self.id2doc = {}
        self.id2aut = {}
        self.ndoc = 0
        self.naut = 0
        self.uniquechaine = ""

    def add_doc(self, doc):

        self.collection[self.ndoc] = doc
        self.id2doc[self.ndoc] = doc.get_title()
        self.ndoc += 1
        aut_name = doc.get_author()
        aut = self.get_aut2id(aut_name)
        if aut is not None:
            self.authors[aut].add(doc)
        else:
            self.add_aut(aut_name, doc)

    def add_aut(self, aut_name, doc):

        aut_temp = Author(aut_name)
        aut_temp.add(doc)

        self.authors[self.naut] = aut_temp
        self.id2aut[self.naut] = aut_name

        self.naut += 1

    def search(self, motcle):
        match = re.findall(r'([^.]*' + motcle + '[^.]*)', self.uniquechaine)
        if match:
            return match
        else:
            return "did not find"

    def concorde(self, motcle, range):
        df = pd.DataFrame(columns=('contexte gauche', 'motif trouvé', 'contexte droit'))
        i = 0
        r = re.compile(motcle)
        for match in r.finditer(self.uniquechaine):
            df.loc[i] = ["..." + self.uniquechaine[int(match.start()) - range: match.start() - 1], motcle,
                         self.uniquechaine[int(match.end()) + 1: match.end() + range] + "..."]
            i = i + 1
        return df

    def get_aut2id(self, author_name):
        aut2id = {v: k for k, v in self.id2aut.items()}
        heidi = aut2id.get(author_name)
        return heidi

    def stats(self, setmots):
        r = r'\w+[a-z]'
        stopwords_fr = set(stop_words.get_stop_words('french'))
        stopwords_en = set(stop_words.get_stop_words('english'))
        stopwords_all = stopwords_en.union(stopwords_fr)

        vocabulairedoc = dict()
        months = ["jan", "fev", "mar", "avr", "mai", "jun", "jui", "aou", "sep", "oct", "nov", "dec"]
        datedic = {
            "jan 2021": [0, 0],
            "dec 2020": [0, 0],
            "nov 2020": [0, 0],
            "oct 2020": [0, 0],
            "sep 2020": [0, 0],
            "aou 2020": [0, 0],
            "jui 2020": [0, 0],
            "jun 2020": [0, 0],
            "mai 2020": [0, 0],
            "avr 2020": [0, 0],
            "mar 2020": [0, 0],
            "fev 2020": [0, 0],
            "jan 2020": [0, 0]
        }
        for document in self.collection.values():
            doctype = document.getType()
            docdate = document.get_date()
            combineddate = months[docdate.month - 1] + " " + str(docdate.year)
            doctostr = nettoyer_texte(document.get_text())
            s = set()
            for voc in re.findall(r, doctostr):
                if voc not in stopwords_all:
                    s.add(voc)
                    if voc in setmots:
                        if combineddate in datedic.keys():
                            if doctype == "arxiv":
                                datedic[combineddate] = [datedic[combineddate][0] + 1, datedic[combineddate][1]]
                            else:
                                datedic[combineddate] = [datedic[combineddate][0], datedic[combineddate][1] + 1]
                        else:
                            if doctype == "arxiv":
                                datedic[combineddate] = [1, 0]
                            else:
                                datedic[combineddate] = [0, 1]
                    if voc in vocabulairedoc.keys():
                        if doctype == "arxiv":
                            vocabulairedoc[voc] = [vocabulairedoc[voc][0] + 1, vocabulairedoc[voc][1],
                                                   vocabulairedoc[voc][2] + 1, vocabulairedoc[voc][3],
                                                   vocabulairedoc[voc][4], vocabulairedoc[voc][5]]

                        else:
                            vocabulairedoc[voc] = [vocabulairedoc[voc][0] + 1, vocabulairedoc[voc][1],
                                                   vocabulairedoc[voc][2], vocabulairedoc[voc][3] + 1,
                                                   vocabulairedoc[voc][4], vocabulairedoc[voc][5]]
                    else:
                        if doctype == "arxiv":
                            vocabulairedoc[voc] = [1, 0, 1, 0, 0, 0]
                        else:
                            vocabulairedoc[voc] = [1, 0, 0, 1, 0, 0]

            for svoc in s:
                vocabulairedoc[svoc][1] += 1
                if doctype == "arxiv":
                    vocabulairedoc[svoc][4] += 1
                else:
                    vocabulairedoc[svoc][5] += 1

        dfvoc = pd.DataFrame.from_dict(vocabulairedoc, orient='index',
                                       columns=['termfreqallcorpus', 'docfreqallcorpus', 'arxivtermfreq',
                                                'reddittermfreq',
                                                'arxivdocfreq', 'redditdocfreq'])
        dfvoc = dfvoc.reset_index()
        dfvoc.rename(columns={'index': 'mot'}, inplace=True)

        dfworddate = pd.DataFrame.from_dict(datedic, orient='index', columns=['arxiv', 'reddit'])
        dfworddate = dfworddate.reset_index()
        dfworddate.rename(columns={'index': 'date'}, inplace=True)
        return dfvoc.head(10), dfworddate

    def get_doc(self, i):
        return self.collection[i]

    def get_coll(self):
        return self.collection

    def get_unch(self):
        return self.uniquechaine

    def set_unch(self, unch):
        self.uniquechaine = unch

    def __str__(self):
        return "Corpus: " + self.name + ", Number of docs: " + str(self.ndoc) + ", Number of authors: " + str(self.naut)

    def __repr__(self):
        return self.name


class Author():
    def __init__(self, name):
        self.name = name
        self.production = {}
        self.ndoc = 0

    def add(self, doc):
        self.production[self.ndoc] = doc
        self.ndoc += 1

    def __str__(self):
        return "Auteur: " + self.name + ", Number of docs: " + str(self.ndoc)

    def __repr__(self):
        return self.name


class Document():

    # constructor
    def __init__(self, date, title, author, text, url):
        self.date = date
        self.title = title
        self.author = author
        self.text = text
        self.url = url

    # getters

    def get_author(self):
        return self.author

    def get_title(self):
        return self.title

    def get_date(self):
        return self.date

    def get_source(self):
        return self.source

    def get_text(self):
        return self.text

    def __str__(self):
        return "Document " + self.getType() + " : " + self.title

    def __repr__(self):
        return self.title

    def sumup(self, ratio):
        try:
            auto_sum = summarize(self.text, ratio=ratio, split=True)
            out = " ".join(auto_sum)
        except:
            out = self.title
        return out

    def getType(self):
        pass


# classe fille permettant de modéliser un Document Reddit
#

class RedditDocument(Document):

    def __init__(self, date, title,
                 author, text, url, num_comments):
        Document.__init__(self, date, title, author, text, url)
        # ou : super(...)
        self.num_comments = num_comments
        self.source = "reddit"

    def get_num_comments(self):
        return self.num_comments

    def getType(self):
        return self.source

    def __str__(self):
        return Document.__str__(self) + " [" + str(self.num_comments) + " commentaires]"


#
# classe fille permettant de modéliser un Document Arxiv
#

class ArxivDocument(Document):

    def __init__(self, date, title, author, text, url, coauteurs):
        Document.__init__(self, date, title, author, text, url)
        self.coauteurs = coauteurs
        self.source = "arxiv"

    def get_num_coauteurs(self):
        if self.coauteurs is None:
            return (0)
        return (len(self.coauteurs) - 1)

    def get_coauteurs(self):
        if self.coauteurs is None:
            return ([])
        return (self.coauteurs)

    def getType(self):
        return self.source

    def __str__(self):
        s = Document.__str__(self)
        if self.get_num_coauteurs() > 0:
            return s + " [" + str(self.get_num_coauteurs()) + " co-auteurs]"
        return s


################################## fonctions ###########################################
def nettoyer_texte(ch):
    # Mise en miniscules
    chlower = ch.lower()
    # remplacer des passages à la ligne
    ch_nobrlignes_win = chlower.replace("\r\n", "\n")
    ch_nobrlignes_unix = ch_nobrlignes_win.replace("\n", " ")
    # supprimer les tickers
    ch_no_tickers = re.sub(r'\$\w*', '', ch_nobrlignes_unix)
    # supprimer les hyperlinks
    ch_no_hyperlinks = [re.sub(r'https?:\/\/.*\/\w*', '', i) for i in ch_no_tickers]
    # Supprimer la ponctuation et remplacer les l' d' y' ou les 's 't 've avec un espace pour le filtre
    pont = string.punctuation
    pontnodot = pont.replace(".", "")
    ch_no_punctuation = [re.sub(r'[' + pontnodot + ']+', ' ', i) for i in ch_no_hyperlinks]
    # Supprimer plusieurs whitespace
    new_ch = ''.join(ch_no_punctuation)
    new_ch_nowhsp = re.sub(' +', ' ', new_ch)
    # supprimer les mot avec un seul caractere
    before_clean = re.sub(r"\b[a-zA-Z]\b", "", new_ch_nowhsp)
    # Supprimez tous les espaces au début de la phrase
    clean_sent = before_clean.lstrip(' ')
    return clean_sent


################################## Création du Corpus ##################################
def creation_corpus(termsdict):
    if termsdict == "":
        terms = "coronavirus"
    else:
        terms = termsdict.split(',')
        # transformer la list en un string avec + comme separateur
        termsquery = "+".join(terms)
    corpus = Corpus("New")

    # extraction des donnes de reddit
    reddit = praw.Reddit(client_id='GW-54GJXc5tFBA', client_secret='QPNLwzUXa6eY4hw4bx1hV6yhM-kpkA', user_agent='taha')
    hot_posts = reddit.subreddit('all').search(termsquery, limit=200)
    for post in hot_posts:
        datet = dt.datetime.fromtimestamp(post.created)
        txt = post.title + ". " + post.selftext
        txt = txt.replace('\n', ' ')
        txt = txt.replace('\r', ' ')
        doc = RedditDocument(datet,
                             post.title,
                             post.author_fullname,
                             txt,
                             post.url,
                             post.num_comments)
        corpus.add_doc(doc)

    # extraction des donnes à partir de arxiv
    url = 'http://export.arxiv.org/api/query?search_query=all:' + termsquery + '&start=0&max_results=100'
    data = urllib.request.urlopen(url).read().decode()
    docs = xmltodict.parse(data)['feed']['entry']
    for i in docs:
        datet = dt.datetime.strptime(i['published'], '%Y-%m-%dT%H:%M:%SZ')
        if datet.year < 2020:
            continue
        try:
            author = [aut['name'] for aut in i['author']][0]
        except:
            author = i['author']['name']
        txt = i['title'] + ". " + i['summary']
        txt = txt.replace('\n', ' ')
        txt = txt.replace('\r', ' ')
        try:
            coauteur = [aut['name'] for aut in i['author']][1:]
        except:
            coauteur = i['author']['name']
        doc = ArxivDocument(datet,
                            i['title'],
                            author,
                            txt,
                            i['id'],
                            coauteur)
        corpus.add_doc(doc)
    statscorpus = corpus.stats(terms)
    hist = statscorpus[1].plot.bar(x='date')
    revealdf(statscorpus[0])
    print(statscorpus)
    return statscorpus


# ==============Affichage d'histogramme===============
def show_hist():
    plt.show()


# =============Affichage des mots communs=============
def communwords(statcp):
    df_copy = statcp.loc[(statcp.arxivtermfreq > 0) & (statcp.reddittermfreq > 0)]
    revealdf(df_copy)


# ===========Affichage des Mots specifique=============
def motspecifique(statcp):
    df_copy = statcp.loc[(statcp.arxivtermfreq == 0) | (statcp.reddittermfreq == 0)]
    revealdf(df_copy)


# ================window form and style===============
root = Tk()
root.title("Projet python")
style = ttk.Style()
style.theme_use('vista')


def revealdf(df):
    tv1.delete(*tv1.get_children())
    tv1["column"] = list(df.columns)
    tv1["show"] = "headings"
    for column in tv1["columns"]:
        tv1.heading(column, text=column)

    df_rows = df.to_numpy().tolist()
    for row in df_rows:
        tv1.insert("", "end", values=row)


# ==================Frame config : root =====================

F1 = ttk.Frame(root, borderwidth=2)
F1.grid(row=0, column=0, columnspan=3)
F1.config(width=200, height=200)

F2 = ttk.Frame(root, borderwidth=2)
F2.grid(row=1, column=0, columnspan=3)

F3 = ttk.Frame(root, borderwidth=2)
F3.grid(row=2, column=0, columnspan=3)

F4 = ttk.Frame(root, borderwidth=2)
F4.grid(row=3, column=0, columnspan=3)

F5 = ttk.Frame(root, borderwidth=2)
F5.grid(row=3, column=2, columnspan=3)

# ==================Entry config : F1 =======================

Terms_label = Label(F1, text="Terms recherché   :")
Terms_label.grid(row=1, column=0, sticky='snew')
Terms_entry = ttk.Entry(F1)
Terms_entry.grid(row=1, column=1, columnspan=4, sticky='snew', padx=20, pady=10)
Terms_entry.config(width=60)

# ==================Button config : F2 ======================

Bu0 = ttk.Button(F2, text='Afficher les Statistiques')
Bu0.grid(row=1, columnspan=3, ipadx=5, ipady=5, padx=15, pady=15)
Bu0.config(command=lambda: creation_corpus(Terms_entry.get()), width=90)

Bu1 = ttk.Button(F2, text='Mots communs')
Bu1.grid(row=2, column=0, sticky='snew', ipadx=5, ipady=5, padx=15, pady=15)
Bu1.config(command=lambda: communwords(creation_corpus(Terms_entry.get())[0]), width=40)

Bu2 = ttk.Button(F2, text='Mots specifiques')
Bu2.grid(row=2, column=1, sticky='snew', ipadx=5, ipady=5, padx=15, pady=15)
Bu2.config(command=lambda: motspecifique(creation_corpus(Terms_entry.get())[0]), width=40)

# ==================Treeview config : F3 ======================
col = (
'mot', 'termfreqallcorpus', 'docfreqallcorpus', 'arxivtermfreq', 'reddittermfreq', 'arxivdocfreq', 'redditdocfreq')
treescrolly = Scrollbar(F3, orient="vertical")
treescrollx = Scrollbar(F3, orient="horizontal")
treescrollx.pack(side="bottom", fill="x")
treescrolly.pack(side=RIGHT, fill=Y)
tv1 = ttk.Treeview(F3, columns=col, height=7)
for i in range(7):
    tv1.column(col[i], width=60, anchor='e')
tv1.pack()
tv1.configure(xscrollcommand=treescrollx.set, yscrollcommand=treescrolly.set)
treescrolly.config(command=tv1.yview)
treescrollx.config(command=tv1.xview)

# ==================Button Affichage histogramme : F4 ======================
Bu3 = ttk.Button(F4, text='Afficher Histogramme')
Bu3.grid(row=0, column=0, sticky=E)
Bu3.config(command=lambda: plt.show())
# ==================Label : F5 ======================
my_name = Label(F5, text=" ")
my_name.grid(row=0, column=0, sticky=W)
# >end Button config

root.rowconfigure(1, weight=1)
root.rowconfigure(2, weight=1)
root.rowconfigure(3, weight=1)
root.columnconfigure(0, weight=1)
root.columnconfigure(1, weight=1)
root.geometry("750x600")
root.resizable(False, False)
root.mainloop()
