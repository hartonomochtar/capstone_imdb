from flask import Flask, render_template 
import pandas as pd
import requests
from bs4 import BeautifulSoup 
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

import re
def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

app = Flask(__name__) #don't change this code

def scrap(url):
    #This is fuction for scrapping
    url_get = requests.get(url)
    soup = BeautifulSoup(url_get.content,"html.parser")
    
    #Find the key to get the information
    table = soup.find('div', attrs={"class": "lister-list"}) 
    tr = table.find_all('div', attrs={"class": "lister-item mode-advanced"}) 

    temp = [] #initiating a tuple

    for i in range(0, len(tr)):
        row = table.find_all('div', attrs={"class": "lister-item mode-advanced"})[i]
        title = row.h3.a.string.strip()
            
        if row.find('span', attrs={'class': 'genre'}) == None : 
            genre = None
        else: genre = row.find('span', attrs={'class': 'genre'}).string.strip()
                
        if row.find('span', attrs={'name': 'nv'}) == None :
            votes = None
        else: votes = row.find('span', attrs={'name': 'nv'}).string.replace(',','').strip()
            
        if row.find('div', attrs={'class': "inline-block ratings-imdb-rating"}) == None :
            imdb_rating = None
        else: imdb_rating = row.find('div', attrs={'class': "inline-block ratings-imdb-rating"}).strong.string.strip()
            
        if row.find('span', attrs={'class': 'runtime'}) == None :
            runtime = None
        else: runtime = row.find('span', attrs={'class': 'runtime'}).string.strip()
            
        if row.find('div', attrs={'class': "inline-block ratings-metascore"}) == None : 
            meta_score = None
        else: 
            meta_score = row.find('div', attrs={'class': "inline-block ratings-metascore"}).span.string.strip()
        
        if row.find_all('p', attrs={'class':'text-muted'})[1] == None:
            synopsis = None
        else:
            synopsis = remove_html_tags(str(row.find_all('p', attrs={'class':'text-muted'})[1])).strip()
            
        temp.append([title, genre, runtime, imdb_rating, meta_score, votes, synopsis])

    df = pd.DataFrame(temp, columns = ('title', 'genre', 'runtime', 'imdb_rating', 'meta_score', 'votes', 'synopsis'))
    
    #data wranggling -  try to change the data type to right data type
    df[['imdb_rating', 'meta_score']] = df[['imdb_rating', 'meta_score']].astype('float64')
    df['votes'] = df['votes'].astype('int64')
    df.meta_score = df.meta_score.fillna('')
    df.runtime = df.runtime.fillna('')
    #end of data wranggling
    
    #for getting the next page
    next_pg = soup.find('a', attrs={'class': 'lister-page-next next-page'})['href']

    return df, next_pg

@app.route("/")
def index():
    url = 'http://imdb.com/search/title/?release_date=2019-01-01,2019-12-31'
    df = pd.DataFrame()
    max_page = 2
    pd.set_option('display.max_colwidth', 100)
    for i in range (0, max_page):
        res = scrap(url)
        df = df.append(res[0])
        header = 'http://imdb.com'
        url = header + res[1]

    #This part for rendering matplotlib
    fig = plt.figure(figsize=(5,5),dpi=300)
    df.groupby(['title']).sum()[['imdb_rating']].sort_values('imdb_rating', ascending=False).head(7).plot.bar()
    
    #Do not change this part
    plt.savefig('plot1',bbox_inches="tight")
    plt.tight_layout()
    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result = str(figdata_png)[2:-1]
    #This part for rendering matplotlib
    
    df = df.sort_values('imdb_rating', ascending=False).reset_index().drop('index', axis=1)
    df = df.head(100)
    df.index = df.index+1

    #this is for rendering the table
    df = df.to_html(classes=["table table-bordered table-striped table-dark table-condensed"])

    return render_template("index.html", table=df, result=result)


if __name__ == "__main__": 
    app.run()
