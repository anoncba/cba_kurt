import requests
import re
from bs4 import BeautifulSoup
import threading
import datetime
import time
###########################################  BIB-Automator CBA #########################################################
disclaimer = "DISCLAIMER: Dit programma zal enkel van 18:00 tot 24:00 instant een reservering maken.\n" \
             "Voor 18:00 zal het programma spinnen tot exact 18:00, hierdoor zal de kurt-reservering zo vroeg mogelijk worden gemaakt.\n" \
             "Beste is dus om net voor 18:00 gegevens in te vullen zodat het een halve minuut kan spinnen en exact om 18:00. " \
             "een reservering maakt"
print(disclaimer)
#  Gebruiksaanwijzing:
#     Stap 0: pip install lxml in terminal,
#             check bij imports of er iets rood onderlijnt is
#               In pycharm: hover hierover met je muis en install dit
#               Anders: pip install ...      (vb pip install requests)
#     stap 1: Vul je gegevens hieronder in
#     stap 1: Run dit programma iets voor 18 uur
#             dit script zal exact om 18 reservatie maken voor gekozen plek op tijdsstip,
#             bij eventuele errors check console
#     DISCLAIMER: dit programma is geen garantie op bibplek, enkel een hulpmiddel om het leven gemakkelijk te maken
#                 dit programma werkt enkel tussen 18 en 24 uur, dit zorgt ervoor dat je programma voor 18 kunt runnen
#                 en exact op 18 kan reserveren
#
########################################################################################################################
########################################################################################################################

_r_nummer=   input("\nTyp je r-nummer (bv r1234657)\n")                 # r-nummer
_wachtwoord= input("Typ je toledo-wachtwoord\n")                  # wachtwoord van toledo account
_datum =     "2022-"+input("maand plus datum dat je wilt reserveren (vb 01-12  => 12 januari)\n")      # datum van reservatie    (year-month-day)

_startuur =  input("startuur van reservering (vb 09 => 9 uur sochtends, 21 => 9 uur savonds)\n")                # startuur van reservatie (moet altijd 2 getallen zijn!)
_einduur =   input("einduur van reservering (vb 09 => 9 uur sochtends, 21 => 9 uur savonds)\n")               # startuur van reservatie (moet altijd 2 getallen zijn!) ( max verschil tss start en eind is 8)
_StoelID =   input("stoelnummer in de cba (vb 155 of 227 etc) druk enter zonder iets te typen als je een random plek wilt\n")             # stoel id = stoelnummer in cba
                                # vb: plaats 155 in de boekenzaal
                                # vb: plaats 227 in de Study kelder
                                # vb  je laat _StoelID = ""   --> random stoel zal gekozen worden met gekozen tijdstip & datum
########################################################################################################################
########################################################################################################################

def strip(string):
    return re.sub('<[^<]+?>', '', string)
def main(r_nummer,wachtwoord,datum,startuur,einduur,StoelID):
    with requests.Session() as s:
        header = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'
        }
        s.headers=header

        get1 = s.get("https://bib.kuleuven.be/faciliteiten/reserveren")
        get2 = s.get("https://www-sso.groupware.kuleuven.be/sites/KURT/Pages/default.aspx",allow_redirects=True)

        soup = BeautifulSoup(get2.text, "lxml")


        tokennummer = soup.find('input', {'name': 'csrf_token'}).get('value')

        datapost1={
            "csrf_token":tokennummer,
            "shib_idp_ls_exception.shib_idp_session_ss":"",
            "shib_idp_ls_success.shib_idp_session_ss":"true",
            "shib_idp_ls_value.shib_idp_session_ss":"",
            "shib_idp_ls_exception.shib_idp_persistent_ss":"",
            "shib_idp_ls_success.shib_idp_persistent_ss":"true",
            "shib_idp_ls_value.shib_idp_persistent_ss":"",
            "shib_idp_ls_supported":"true",
            "_eventId_proceed":""
        }
        rpost1 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s1",data=datapost1,allow_redirects=True)

        soup = BeautifulSoup(rpost1.text, "lxml")
        tokennummer2 = soup.find('input', {'name': 'csrf_token'}).get('value')
        datapost2 = {
            "csrf_token": tokennummer2,
            "username": str(r_nummer),
            "password": str(wachtwoord),
            "_eventId": "proceed"
        }


        rpost2 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s2",data=datapost2,allow_redirects=True)

        soup = BeautifulSoup(rpost2.text, "lxml")
        tokennummer3 = soup.find('input', {'name': 'csrf_token'}).get('value')
        datapost3 = {
            "csrf_token":tokennummer3,
            "shib_idp_ls_exception.shib_idp_session_ss":"",
            "shib_idp_ls_success.shib_idp_session_ss":"true",
            "_eventId_proceed":""



        }
        rpost3 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s3", data=datapost3,
                        allow_redirects=True)

        soup = BeautifulSoup(rpost3.text, "lxml")
        samlresponseinputs = soup.find('input', {'name': 'SAMLResponse'})
        if samlresponseinputs == None:
            print("error, wss fout wachtwoord of r-nummer")
            return
        samlresponse = samlresponseinputs.get('value')
        relaystate = soup.find('input', {'name': 'RelayState'}).get('value')
        datapost4 ={
            "RelayState":relaystate,
            "SAMLResponse":samlresponse

        }
        rpost4 = s.post("https://fs.kuleuven.be/adfs/ls/",data=datapost4)
        if datetime.datetime.now().hour<18:
            print("program is waiting until its 18:00")
        while datetime.datetime.now().hour<18:
            time.sleep(0.1)
        print("Making reservation ...")
        if len(str(StoelID)) == 0:





            params = (
                ('webserviceUrl',
                 '/QuickReservation4?CurrentUID='+str(r_nummer)+'&PID2=201401&SelectedBeginDatestring='+str(datum)+' '+str(startuur)+':00:00&SelectedEndDatestring='+str(datum)+' '+str(einduur)+':00:00&Subject=bm8gc3ViamVjdA==&Body=&OtherUsers=&Answer=&ImpersonatedUID=&SessionID='),
            )
            response = s.get('https://www-sso.groupware.kuleuven.be/sites/KURT/_vti_bin/KURTService/KURTService.svc/CallWebservice',  params=params)

        else:



        #voor specifieke stoel
            params = (
                ('webserviceUrl',
                '/CreateReservation4?CurrentUID='+str(r_nummer)+'&SelectedResourceID='+str(int(StoelID)+301075)+'&SelectedBeginDatestring='+str(datum)+' '+str(startuur)+':00:00&SelectedEndDatestring='+str(datum)+' '+str(einduur)+':00:00&Subject=bm8gc3ViamVjdA==&Body=&OtherUsers=&Answer=&ImpersonatedUID=&SessionID='),
            )
            response = s.get('https://www-sso.groupware.kuleuven.be/sites/KURT/_vti_bin/KURTService/KURTService.svc/CallWebservice', params=params)
        print(strip(response.json()))




t1 = threading.Thread(target=main,args=(_r_nummer,_wachtwoord,_datum,_startuur,_einduur,_StoelID))
# t2 = threading.Thread(target=main,args=(_r_nummer2,_wachtwoord2,_datum,_startuur,_einduur,_StoelID2))

t1.start()
# t2.start()
t1.join()
# t2.join()
a = input("done")

