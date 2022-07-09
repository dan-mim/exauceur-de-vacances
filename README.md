# exausseur-de-vacances
This is the first web app I am developping. It often happens that I know when I can have some hollidays but I never know where to go. This usually depends on the price flights. This app proposes all the best destination option.

The difference between this branche and the other is that in the version, the website runs the scraping in background and send a message byy itself while the client can do other requests.

app_kayak_web_v1.py can be deployed on Heroku because it uses GOOGLE_CHROME_BIN and CHROMEDRIVER_PATH 
while app_kayak_web_v2_Chrome_theading.py only works on a local computer.
Edit : app_kayak_web_v1.py and more generally this whole Chrome-driver branch cannot be deployed because the method uses too much RAM.
Refer to the branch Chrome-driver-no-threading for deployement.


I used http://kaffeine.herokuapp.com/ to prevent my website from idling (the heroku dynos from idling).
