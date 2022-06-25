# exausseur-de-vacances
This is the first web app I am developping. 
It often happens that I know when I can have some hollidays but I never know where to go. This usually depends on the price flights. This app proposes all the best destination options.

app.py needs to be run for the website to work (under the web adress 'localhost:5000' if in local).
The 2 documents that begin with 'IATA' are the destinations that will be checked. If you want to check/compare more destinations you need to add their IATA codes in these files or in a new one.

What the app does: it takes your infos (when you are available and what part of europe you would be keen to visit) and it compares all the destinations from the IATA file.  For each destination a kayak webpage is scraped and the data are collected : 'price of the fllights, durations, hours...'. Then the data from all the destinations are compared and ranked.
Finally a mail is sent to the user with an excel file with the ranked destinations.
