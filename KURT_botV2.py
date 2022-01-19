import requests
import re
from bs4 import BeautifulSoup
import threading
import datetime
import time
###########################################  BIB-Automator CBA #########################################################
disclaimer = "DISCLAIMER: Enkel stoelnummers van de zolder werken, andere bib-zalen zijn inferieur.  \\
                Run dit programma paar minuten voor 18:00, vul je gegevens in en wacht totdat je reservering is gemaakt.\\
                 Je kan meerdere stoelen ingeven indien je meerdere reserveringen wilt."
print(disclaimer)
#  Gebruiksaanwijzing:
                  
#     DISCLAIMER: Enkel stoelnummers van de zolder werken, andere bib-zalen zijn inferieur.
#                 Run dit programma paar minuten voor 18:00, vul je gegevens in en wacht totdat je reservering is gemaakt.
#                 Je kan meerdere stoelen ingeven indien je meerdere reserveringen wilt.
#                 

#
########################################################################################################################
########################################################################################################################

_r_nummer= input("\nTyp je r-nummer (bv r1234657)\n")                 # r-nummer
_wachtwoord= input("Typ je toledo-wachtwoord\n")                  # wachtwoord van toledo account
_datum = "2022-"+input("Typ je maand + datum dat je wilt reserveren (vb 01-12  => 12 januari)\n")      # datum van reservatie    (year-month-day)

_startuur = input("Typ je startuur van reservering (vb 09 => 9 uur sochtends, 21 => 9 uur savonds)\n")                # startuur van reservatie (moet altijd 2 getallen zijn!)
_einduur =  input("Typ je einduur van reservering (vb 09 => 9 uur sochtends, 21 => 9 uur savonds)\n")               # startuur van reservatie (moet altijd 2 getallen zijn!) ( max verschil tss start en eind is 8)
_StoelID =  input("Stoelnummer op zolder (vb 355 of 399 etc) \nWil je meerdere stoelen proberen typ dan de nummers achter elkaar zonder spatie maar met komma bv 355,399,351\n")             # stoel id = stoelnummer in cba
                                # vb: plaats 155 in de boekenzaal
                                # vb: plaats 227 in de Study kelder
                                # vb  je laat _StoelID = ""   --> random stoel zal gekozen worden met gekozen tijdstip & datum
stoelnmmrs = _StoelID.split(',')

########################################################################################################################
########################################################################################################################

def strip(string):
    return re.sub('<[^<]+?>', '', string)
def login(r_nummer,wachtwoord,s):
    header = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36'
    }
    s.headers = header

    get1 = s.get("https://bib.kuleuven.be/faciliteiten/reserveren")
    get2 = s.get("https://www-sso.groupware.kuleuven.be/sites/KURT/Pages/default.aspx", allow_redirects=True)

    soup = BeautifulSoup(get2.text, "lxml")

    tokennummer = soup.find('input', {'name': 'csrf_token'}).get('value')

    datapost1 = {
        "csrf_token": tokennummer,
        "shib_idp_ls_exception.shib_idp_session_ss": "",
        "shib_idp_ls_success.shib_idp_session_ss": "true",
        "shib_idp_ls_value.shib_idp_session_ss": "",
        "shib_idp_ls_exception.shib_idp_persistent_ss": "",
        "shib_idp_ls_success.shib_idp_persistent_ss": "true",
        "shib_idp_ls_value.shib_idp_persistent_ss": "",
        "shib_idp_ls_supported": "true",
        "_eventId_proceed": ""
    }
    rpost1 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s1", data=datapost1,
                    allow_redirects=True)

    soup = BeautifulSoup(rpost1.text, "lxml")
    tokennummer2 = soup.find('input', {'name': 'csrf_token'}).get('value')
    datapost2 = {
        "csrf_token": tokennummer2,
        "username": str(r_nummer),
        "password": str(wachtwoord),
        "_eventId": "proceed"
    }

    rpost2 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s2", data=datapost2,
                    allow_redirects=True)

    soup = BeautifulSoup(rpost2.text, "lxml")
    tokennummer3 = soup.find('input', {'name': 'csrf_token'}).get('value')
    datapost3 = {
        "csrf_token": tokennummer3,
        "shib_idp_ls_exception.shib_idp_session_ss": "",
        "shib_idp_ls_success.shib_idp_session_ss": "true",
        "_eventId_proceed": ""

    }
    rpost3 = s.post("https://idp.kuleuven.be/idp/profile/SAML2/Redirect/SSO?execution=e1s3", data=datapost3,
                    allow_redirects=True)

    soup = BeautifulSoup(rpost3.text, "lxml")
    samlresponseinputs = soup.find('input', {'name': 'SAMLResponse'})
    if samlresponseinputs == None:
        print("error, wss fout wachtwoord of r-nummer")
        return False
    samlresponse = samlresponseinputs.get('value')
    relaystate = soup.find('input', {'name': 'RelayState'}).get('value')
    datapost4 = {
        "RelayState": relaystate,
        "SAMLResponse": samlresponse

    }
    rpost4 = s.post("https://fs.kuleuven.be/adfs/ls/", data=datapost4)
def get_stoelid(StoelID,s):
    IDname = "CBA - Zolder Seat " + StoelID
    dat = {
        "ResourceName": IDname
    }
    req = s.get(
        "https://www-sso.groupware.kuleuven.be/sites/KURT/_vti_bin/KURTService/KURTService.svc/CallWebservice?webserviceUrl=/GetResourceID?ResourceName=" + IDname)
    return strip(req.json())
def make_random_reservation(r_nummer,datum,startuur,einduur,s):
    params = (
        ('webserviceUrl',
         '/QuickReservation4?CurrentUID=' + str(r_nummer) + '&PID2=201401&SelectedBeginDatestring=' + str(
             datum) + ' ' + str(startuur) + ':00:00&SelectedEndDatestring=' + str(datum) + ' ' + str(
             einduur) + ':00:00&Subject=bm8gc3ViamVjdA==&Body=&OtherUsers=&Answer=&ImpersonatedUID=&SessionID='),
    )
    response = s.get(
        'https://www-sso.groupware.kuleuven.be/sites/KURT/_vti_bin/KURTService/KURTService.svc/CallWebservice',
        params=params)
    return response
def make_specific_reservation(r_nummer,datum,startuur,einduur,idnummer,s):
    params = (
        ('webserviceUrl',
         '/CreateReservation4?CurrentUID=' + r_nummer + '&SelectedResourceID=' + idnummer + '&SelectedBeginDatestring=' + datum + ' ' + startuur + ':00:00&SelectedEndDatestring=' + datum + ' ' + einduur + ':00:00&Subject=bm8gc3ViamVjdA==&Body=&OtherUsers=&Answer=&ImpersonatedUID=&SessionID='),
    )
    response = s.get(
        'https://www-sso.groupware.kuleuven.be/sites/KURT/_vti_bin/KURTService/KURTService.svc/CallWebservice',
        params=params)
    return response
def main(r_nummer,wachtwoord,datum,startuur,einduur,StoelID):
    with requests.Session() as s:

        login(r_nummer,wachtwoord,s)
        idnummer = get_stoelid(StoelID, s)

        time_to_launch = datetime.time(18,0,0,50000)
        if datetime.datetime.now().time()<time_to_launch:
            print(f"""program is waiting until its 18:00, please sit back and relax, everything will now be done for you""")
        while datetime.datetime.now().time() < time_to_launch:
            time.sleep(0.05)


        if len(str(StoelID)) == 0:
            response = make_random_reservation(r_nummer,datum,startuur,einduur,s)
            time.sleep(0)
        else:
            response = make_specific_reservation(r_nummer,datum,startuur,einduur,idnummer,s)

            text = strip(response.json())

            for i in range(4):
                if text[2:7]=="ERROR":

                    response = make_specific_reservation(r_nummer, datum, startuur, einduur, idnummer, s)
                    text = strip(response.json())
            print(text)







threads = []
for i in stoelnmmrs:
    threads.append(threading.Thread(target=main,args=(_r_nummer,_wachtwoord,_datum,_startuur,_einduur,i)))
for i in threads:
    i.start()
for i in threads:
    i.join()

a = input("Done, druk op enter om af te sluiten!")

