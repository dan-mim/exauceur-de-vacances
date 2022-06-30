# -*- coding: utf-8 -*-
"""
Created on Fri Jun 17 12:02:26 2022

@author: Daniel.mimouni

Je vais créer un programme python qui scrape Kayak pour retrouver les meilleurs prix pour des destinations. 
J'essaie de construire des fonctions réutilisabes au maximum

Version v1 : Je me débarasse de tous les bouts de codes inutiles ou commentés de la version v0
"""

#%% IMPORTATION des bibliothèques
from selenium import webdriver
#from webdriver_manager.firefox import GeckoDriverManager #si j'utilise Firefox
#from selenium.webdriver.firefox.options import Options # pour rajouter des options (comme ne pas montrer les fenetres firefox)
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import numpy as np 
import time
#relatif au temps d'attente :
from selenium.webdriver.support.wait import WebDriverWait
#from selenium.webdriver.common.by import By
from functools import partial 
import string
#pour executer des codes en parallèle
from concurrent.futures import ThreadPoolExecutor

import os
import psutil # pour avoir accès à la mémoire vive utilisée


# dates = ['2022-07-31', '2022-08-05']
# depart = ''
# recipient_email = 'dan15.will@gmail.com'

#%% FONCTION FINALE DE L'APPLICATION
"""
Cette fonction est la fonction à executer pour obtenir le scraping d'une cinquantaine d'aéroport 
à des dates choisises.

Le résultat est un mail envoyé à l'usager avec en pièce jointe un excel récapitulant tous les vols possibles.

Elle prend en entrée:
    -le mail du l'utilisateur(str), 
    -les dates(list) de depart et de retour, 
    -le lieu de départ(str) qui est 'Paris RER' si on ne précise pas que le départ peut
    être à Beauvais, 
    -l'arrivée(str) est la destination ('europe du sud' sauf si on précise 'europe du nord')
    -le temps max de trajet(float) (réglé sur 4h sauf si précisé)
    -le taux de conversion du dollard à l'euro(float) reglé sur 0.93 (juin 2022) mais
    peut être modifiée.

"""
def app_scraping_kayak(recipient_email, dates, depart='Paris RER', arrivee=['europe du sud'], temps_max=4):
    time.sleep(3)
    ## données d'entrées
    #départs:
    l_departure = ['CDG', 'ORY']
    if depart == 'Paris + Beauvais':
        l_departure = ['CDG', 'ORY', 'BVA']
    #arrivées:
    df_aeroports_arrives_all = pd.read_csv('IATA_mediterranee.txt')[5:7]
    if arrivee == ['europe du nord']:
        df_aeroports_arrives_all = pd.read_csv('IATA_europe_nord.txt')
    if arrivee == ['europe du sud', 'europe du nord']:
        df_aeroports_arrives_all = pd.concat([df_aeroports_arrives_all, pd.read_csv('IATA_europe_nord.txt')])
    #dates:
    departure_date = dates[0] # Under the format 'YYYY-MM-DD'
    arrival_date = dates[1]
    ## données intermédiaires
    #liste aéroports d'arrivées:
    aeroports_arrives = list(df_aeroports_arrives_all.code_IATA)
    #correspondances IATA avec noms aéroports
    corresp_IATA_complete = pd.read_csv('corresp_IATA_complete.csv', delimiter = ';')
    #links:
    links = make_links(l_departure, aeroports_arrives, departure_date, arrival_date)
    #directory path:
    path = os.getcwd()
    #nom du fichier resultat:
    name_result = f"Vacances en {arrivee} du {departure_date} au {arrival_date}"
    ## execution des fonctions
    #trouver la conversion de l'euro au dollard
    conv_doll_euros = find_conv_doll_euros()
    print('*'*30, conv_doll_euros)
    #scraping des pages kayak
    resultats = execution_scraping(links, aeroports_arrives, departure_date, arrival_date, temps_max)
    print(resultats)
    #mise en excel des résultats
    mise_en_excel(name_result, aeroports_arrives, links, resultats, conv_doll_euros, corresp_IATA_complete)
    #envoie du mail
    send_mail(recipient_email, departure_date, arrival_date, path, name_result)
    return(resultats)


"""
Les fonctions qui suivent sont les fonctions support de app_scraping_kayak()
"""

#%% FERMER LES COOKIES
def close_cookies(browser):
    accept_cookies_xpath = '/html/body/div[12]/div/div[3]/div/div/div/div/div[1]/div/div[2]/div[2]/div[1]/button/span'
    try:
       browser.find_element_by_xpath(accept_cookies_xpath).click()
    except NoSuchElementException:
       pass
   
#%% CHARGER LA PAGE 
def make_url(l_departure, arrival, departure_date, arrival_date, nb_stops_max=0):
    departure1 = l_departure[0]
    departure2 = l_departure[1]
    # nb_stops_max = nombre max d'escales
    if nb_stops_max == 0: #aucune escale
        index_stop = '&fs=stops='+'0'
    if nb_stops_max == 1: #une escale max
        index_stop = '&fs=stops='+'-2'      
    if nb_stops_max == 2: #pas de limitation sur le nombre d'escales
        index_stop = ''
    url = f"https://www.kayak.com/flights/{departure1},{departure2}-{arrival}/{departure_date}/{arrival_date}?sort=bestflight_a{index_stop}"
    return(url)

def open_result(browser, url):
    try:
        browser.get(url)
        close_cookies(browser)
    except:
        pass
#%% SUPPRIMER LES TRAJETS TROP LONG
# cette fonction permet de supprimer les itinéraires qui présentent un trajet 
# trop long.
def supprimer_vol_long(a, temps_max):
    a['duree_min'] = a.duration.apply(lambda x: float(x.replace('h','.').replace('m','')))
    a = a.loc[a.duree_min < temps_max]
    l_markeur = []
    for i in range(a.shape[0]):
        markeur = 0
        vol0 = a.iloc[i].flights
        vol_m1 = vol0 + 1
        vol_p1 = vol0 + 1
        if i > 0:
            vol_m1 = a.iloc[i-1].flights
        if i < a.shape[0]-1 :
            vol_p1 = a.iloc[i+1].flights
        if vol0-vol_m1 != 0 and vol0-vol_p1 != 0 :
            markeur = 1
        if a.shape[0] == 1:
            markeur = 1
        l_markeur.append(markeur)
    a['markeur'] = l_markeur
    a = a.loc[a.markeur == 0]
    return(a)

#%% SCRAPING DE LA PAGE
def scraping_the_page(browser, departure_date, arrival_date, temps_max):
    try:
        # horaires
        xp_schedules = '//div[@class="section times"]' 
        schedules = browser.find_elements_by_xpath(xp_schedules)
        hours_a = [schedule.text.split()[0]+schedule.text.split()[1] for schedule in schedules]
        hours_b = [schedule.text.split()[3]+schedule.text.split()[4] for schedule in schedules]
        nb_flights = int(len(hours_a)/2)
        aller_retour = [departure_date, arrival_date] * nb_flights
        tab_flights = pd.DataFrame({'date' : aller_retour, 'taking off' : hours_a, 'landing' : hours_b})
        
        # durées de vol
        xp_duration = '//div[@class="section duration allow-multi-modal-icons"]' #/div[@class="top"]/span[@class="time-pair"]'
        duration0 = browser.find_elements_by_xpath(xp_duration)
        duration = [dur.text.split()[0]+dur.text.split()[1] for dur in duration0]
        tab_flights['duration'] = duration
        
        # prix de l'aller retour
        xp_prices = '//a[contains(@class,"booking-link")]/span[@class="price option-text"]/span[@class="price-text"]'
        prices = browser.find_elements_by_xpath(xp_prices)
        prices_list = [price.text.replace('$','').replace(',','') for price in prices if price.text != '']
        prices_list = list(map(int, prices_list))
        tab_prices = pd.DataFrame({'flights' : [i for i in range(nb_flights)], 'prices_dollard' : prices_list})
        # 1 trajet = 1 aler retour
        flights = sum(([i,i] for i in range(nb_flights)),[])
        tab_flights['flights'] = flights
        # Je rajoute le prix de l'aller retour au tableau de base
        tab_flights = tab_flights.merge(tab_prices, left_on='flights', right_on='flights')
        tab_flights = supprimer_vol_long(tab_flights, temps_max).reset_index()
    except:
        tab_flights = pd.DataFrame()
    # résultat
    return(tab_flights)

#%% METHODE 1 : OUVERTURE ET TRAITEMENT FENETRE PAR FENETRE
def scraping_kayak(url, arrival, departure_date, arrival_date, temps_max):
    """
    un seul url, un tableau de résultat à remplir, une seule arrivée (arrival)
    un dico de driver qu'on va remplir
    """
    # curseur:
    # En activant ces options les fenetres Firefox ne s'affichent pas
    # mais je ne sais pas pourquoi, du coup les résultats sont faux :(
    # option_browser = webdriver.FirefoxOptions() #Options() #
    # option_browser.add_argument('--headless')
    ### pour avoir Chrome dans Heroku ###
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    #chrome_options.add_argument("--no-sandbox")
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    ###    ###
    #browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())#, options=option_browser)
    # ouverture de la fenetre:
    open_result(browser, url)
    # scraping:
    start=time.time()
    time.sleep(60*1) #4.5) 
    """ 
    ce time. sleep est responsable de la stabilité du modèle
    mais aussi de sa rapidité/lenteur 
    """
    print('-'*20, arrival, ':', browser)
    res = scraping_the_page(browser, departure_date, arrival_date, temps_max)
    end = time.time()
    print('~'*30,'apres le scraping : ',np.round(end-start, 2),'s - ', arrival)
    res['arrival'] = arrival
    print('*'*20, ': ', arrival, '-- le tab de res est vide ?', res.empty)
    browser.quit()
    return(res)

#%% CREATION D'UNE LISTE DE LIENS URL
def make_links(l_departure, aeroports_arrives, departure_date, arrival_date):
    links = []
    for arrival in aeroports_arrives:
        url = make_url(l_departure, arrival, departure_date, arrival_date) #url a scraper
        links.append(url)
    return(links)

#%% EXECUTION AVEC CONCURRENT FUTURES
def execution_scraping(links, aeroports_arrives, departure_date, arrival_date, temps_max):
    n = len(links)
    with ThreadPoolExecutor() as executor:
        # submit tasks and process results
        resu = {}
        i = 0
        for res in executor.map(scraping_kayak, links, aeroports_arrives, [departure_date]*n, [arrival_date]*n, [temps_max]*n):
            arrival = aeroports_arrives[i]
            resu[arrival] = res
            i = i + 1
    return(resu)

#%% MISE EN FORME DU TABLEAU DE RESULTATS
def mise_en_excel(name_result, aeroports_arrives, links, resultats, conv_doll_euros, corresp_IATA_complete):
    #tableau des correspondances avec les url:
    correspondance_url = pd.DataFrame({'arrival': aeroports_arrives, 'url': links})
    #tableau de résultats:
    tab_resultat = pd.DataFrame()
    for arrival in resultats.keys():
        tab_resultat = pd.concat([tab_resultat,resultats[arrival]])
    
    # Je convertis les prix en dollards en euro    
    tab_resultat['prices_euros'] = tab_resultat.prices_dollard.apply(lambda x : int(x*conv_doll_euros))
    tab_resultat = tab_resultat[['date', 'taking off', 'landing', 'duration', 'prices_dollard', 'prices_euros','arrival', 'flights']]
    # ajout de l'url de chaque recher au tableau :
    tab_resultat = tab_resultat.merge(correspondance_url, left_on='arrival', right_on='arrival')
    tab_resultat = tab_resultat.merge(corresp_IATA_complete, left_on='arrival', right_on='IATA')
    tab_resultat = tab_resultat.sort_values(['prices_dollard','flights']).drop('flights', axis=1)
    tab_resultat = tab_resultat[['date', 'taking off', 'landing', 'duration', 'prices_dollard', 'prices_euros','arrival', 'city', 'country', 'url']].drop_duplicates()
    tab_resultat.to_excel(f'{name_result}.xlsx')

#%% SEND MAIL
def send_mail(recipient_email, departure_date, arrival_date, path, name_result):
    #template
    template = """
    Très cher voyageur,
    
    J'espère que vous profiterez bien de vos vacances !
    Voici, ci-joint, un liste des meilleurs vols autour des dates que vous avez choisi ({dates}).
    
    
    Cordialement,
    Votre agent de voyage préféré
    
    Dan
    """
    
    from Dmail.esp import Gmail
    
    #user = "Daniel"
    dates1 = f"{departure_date} to {arrival_date}"
    email_address = "projets.dan@gmail.com"
    password = "etgixigjnxvolwdk"
    recipient_email = "dan15.will@gmail.com"
    
    # Creating the email body
    message = template.format(dates=dates1)
    attached = path+f"\{name_result}.xlsx"
    
    # Sending the email
    with Gmail(email_address, password) as email:
        email.send(message, recipient_email,
                    subject=f"[Kayak] Best flight deals on the {dates1}", attachments=attached)
    
#%%
def find_conv_doll_euros():
    ### pour Heroku ###
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    ###    ###
    #browser = webdriver.Firefox(executable_path=GeckoDriverManager().install())#, options=option_browser)
    url = "https://www.google.com/search?client=firefox-b-d&q=un+dollard+en+euro"
    # ouverture de la fenetre:
    open_result(browser, url)
    #gestion des cookies
    accept_cookies_xpath = '//*[@id="L2AGLb"]'
    try:
       browser.find_element_by_xpath(accept_cookies_xpath).click()
    except NoSuchElementException:
       pass
    #récuperation du taux de conversion
    xp_conversion = '//span[@data-precision="2"]' 
    conversion = browser.find_elements_by_xpath(xp_conversion)
    resultat = conversion[0].text.replace(',', '.')
    conv_doll_euros = float(resultat)
    browser.quit()
    return(conv_doll_euros)
    
#%% Execution

# start_time = time.time()
# app_scraping_kayak(recipient_email, dates, depart)
# end = time.time()
# print('*'*80)
# print("TOTAL TIME : ", round((end - start_time)/60,2), " minutes")
# #print('tableau résultat : ', len(resultat_1.keys())) 
# print('*'*80)


#send_mail("dan15.will@gmail.com", "2022-07-24", "2022-07-28", r"C:\Users\Daniel.mimouni\Desktop\programme_perso\web_scraping\site_web\01_flask_web_app", "corresp_days")





















