# -*- coding: utf-8 -*-
"""
Created on Sun Jun 19 22:36:40 2022

@author: Daniel.mimouni
"""

from flask import Flask, render_template, request, flash
from threading import Thread
from app_kayak_web_v1 import *

app = Flask(__name__)
app.secret_key = "jqegmqhre156"

@app.route("/")
def index():
	return render_template("index1.html")

@app.route("/formulaire", methods=['POST', 'GET'])
def find_the_perfect_trip():
    #email
    recipient_email = str(request.form['email'])
    #dates
    departure_date = request.form['date1']
    arrival_date = request.form['date2']
    dates = [departure_date, arrival_date]
    #départ depuis :
    depart = request.form.getlist("Aeroport de depart")[0]
    if depart == 'autre aeroport':
        depart = request.form['IATA_depart']
    #region de destination
    arrivee1 = request.form.getlist('Region de destination')[0]
    arrivee2 = ''
    arrivee = [arrivee1]
    len_arrivee = len(request.form.getlist('Region de destination'))
    if len_arrivee > 1:
        arrivee2 = request.form.getlist('Region de destination')[1]
        arrivee = [arrivee1] + [arrivee2]
        arrivee2 = "et l'"+ arrivee2
    #temps max
    temps_max = int(request.form['temps maximum de trajet'])
    #flash:
    # flash(recipient_email)
    # flash(dates)
    # flash(depart)
    # flash(arrivee)
    # flash(temps_max)
    # flash(conv_doll_euros)
    #fonction python
    print('~'*20)
    print(recipient_email, dates, depart, arrivee, temps_max)
    print('~'*20)
    arguments = {'recipient_email':recipient_email, 'dates':dates,
                               'depart':depart, 'arrivee':arrivee, 'temps_max':temps_max}
    #app_scraping_kayak(recipient_email, dates, depart, arrivee, temps_max)
    #app_scraping_kayak(recipient_email, dates, depart, arrivee, temps_max)
    thread = Thread(target=app_scraping_kayak, kwargs=arguments) #Thread(target=find_conv_doll_euros, kwargs={})
    thread.start()
    name_result = f"Vacances en ['{arrivee}'] du {departure_date} au {arrival_date}"
    print(name_result, recipient_email, dates[0], dates[1], os.getcwd(), name_result)
    #send_mail(recipient_email, dates[0], dates[1], os.getcwd(), name_result)
    #app_scraping_kayak(recipient_email, dates) #, depart, arrivee, temps_max, conv_doll_euros)
    return render_template("index2.html", recipient_email=recipient_email, 
                           departure_date=departure_date, arrival_date=arrival_date,
                           depart=depart, arrivee1=arrivee1, arrivee2=arrivee2,
                           temps_max=temps_max)


# @app.after_response
# def test():
#     conv_doll_euros = find_conv_doll_euros()
#     return
# def test():
#     conv_doll_euros = find_conv_doll_euros()
#     return(conv_doll_euros)

# @app.route('/formulaire/<string:page_name>')
# def test():
#     conv_doll_euros = find_conv_doll_euros()
#     return(conv_doll_euros)

@app.route("/nouvelle", methods=['POST', 'GET'])
def nouvelle_recherche():
    return render_template("index1.html")

app.run()








