#Creazione inventario (OK)
#Creazione/Lettura codici (OK)
#Inserimento oggetto (OK)
#Indicazione posizione (OK)
#Controllo bidirezionale prodotto-scaffale (OK)
#Duplicità prodotto o sospetta tale. (OK) Mostrare Foto prodotto (OK)

import csv
import json
import cv2
import re
import pandas
import os


esiste = False

try:
    os.makedirs("Img_Inventario")
except:
    print("La directory esiste già")

#VERIFICA ESISTENZA DATABASE.
try:
    documento = open("test.csv","r",newline='') #Verifica esistenza documento
    esiste = True
    documento.close()
except:
    esiste = False  
    documento = open("test.csv","w",newline='') #Crea il file
    s = csv.writer(documento, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONE) #Per la scrittura
    s.writerow(["Codice Prodotto","Nome Prodotto","Posizione","Quantità","Immagine"])  #SOLO LA PRIMA VOLTA. CREA LE COLONNE
    documento.close()

documento = open("test.csv","r+",newline='') #Apri il file per leggere e scrivere
s = csv.writer(documento, delimiter=",", quotechar='"', quoting=csv.QUOTE_NONE) #Per la scrittura
r = csv.DictReader(documento) #Per la lettura

#Ultimi valori del codice e della posizione
testo = []
ultimo_codice = 0
ultima_posizione = "A0"

for j in r:
    ultimo_codice = j["Codice Prodotto"]
    ultima_posizione = j["Posizione"]
    testo.append(j)

#Scattare foto
def leggi_camera(codice,home):
    cam = cv2.VideoCapture(0) #Scelgo la fotocamera funzionante
    while True:
        valido,img = cam.read() #Il primo valore è booleano, indica la corretta lettura dei dati della camera; il secondo è l'immagine

        if valido:
            cv2.imshow("Finestra",img)
        else:
            print("Errore nella lettura del frame")
            
        
        if cv2.waitKey(1) == ord("s"): #Continua ad aggiornare l'immagine finché non verrà premuto il tasto per scattare la foto. Se il parametro fosse 0, l'immagine rimarrebbe immutata.
            cv2.imwrite(home+"/"+str(codice)+".png",img)
            print("Foto salvata")
            break
    cam.release()
    cv2.destroyAllWindows()

#Crea il codice oggetto e il codice posizione
def crea_codice(ultimo_codice,ultima_posizione,prodotto,nuovo_scaffale,dop,numQ,prec): #**E se volessi cambiare la lettera?
    #Elaborazione dati
    posizione_divisa = re.match(r"([a-z]+)([0-9]+)",ultima_posizione,re.I)
    lettera = posizione_divisa.groups()[0]
    lettera = "".join(set(lettera)) #Rimuove possibili lettere duplicate
    numero = int(posizione_divisa.groups()[1])
    codice = int(ultimo_codice)
    home = os.getcwd()+"/Img_Inventario"
    posizione = lettera + str(numero)
    #print("CREA:",ultimo_codice,posizione_divisa)
    if nuovo_scaffale == True:
        posizione = lettera
        numero +=1
        posizione += str(numero)
        codice = int(ultimo_codice) + 1
        quantita = numQ
        #print("ECCO:",posizione,codice)
    else:
        if dop == True: #Se l'oggetto è un duplicato e verrà sistemato assieme agli altri, bisogna aggiornare solo la quantità
            quantita = numQ + prec
            documento.seek(0)
            #AGGIORNARE ELENCO SENZA AGGIUNGERE RIGA
            for val in r:    
                if prodotto.lower().strip() == val["Nome Prodotto"].lower().strip(): #CAMBIARE LA CELLA
                    if val["Posizione"].strip() == ultima_posizione:
                        doc_panda = pandas.read_csv("test.csv")
                        doc_panda.iloc[(int(val["Codice Prodotto"])-1),3] = quantita
                        doc_panda.to_csv("test.csv",index=False)
        else:
            codice = int(ultimo_codice) + 1
            quantita = numQ
    
    immagine = home+"/"+str(codice)+".png"
    if dop != True:
        elenco = {"Codice Prodotto":codice,"Nome Prodotto":prodotto,"Posizione":posizione,"Quantità":quantita,"Immagine":immagine} #Modello elenco
        s.writerow([i for i in elenco.values()]) #Inserisce tutti i valori dell'elenco nel file
        leggi_camera(codice, home)

    return posizione, codice

#CREA UN OGGETTO IN UNO SCAFFALE NUOVO O ESISTENTE
def crea_oggetto(ultimo_codice,ultima_posizione):
    prodotto = input("Inserire nome oggetto: ")
    print(prodotto)
    doppione = False
    quantita_precedente = 0
    documento.seek(0) #Leggi dall'inizio. Permette molteplici letture.
    for riga in r: #Controllo oggetti simili in magazzino
        if prodotto.strip().lower() in str(riga).strip().lower():
            doppione = True
            quantita_precedente = int(riga["Quantità"])
            ultima_posizione = riga["Posizione"]
            print("Ci sono già dei prodotti simili in lista:",riga,quantita_precedente)
            img_duplicato = cv2.imread(riga["Immagine"])
            cv2.imshow("Finestra Duplicato",img_duplicato)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    print(quantita_precedente)
    nuovo = input("Vuoi aggiungere l'oggetto ad un nuovo scaffale? (y[Default]/n)")
    try:
        q = int(input("Inserire quantità di oggetti aggiunti [Default=1]:"))
    except:
        #print("Quantità di default")
        q = 1
    if nuovo.lower() == "y":
        nuovo = True
    elif nuovo.lower() == "n":
        documento.seek(0)
        posizioni_totali = []
        for colonna in r: 
            posizioni_totali.append(colonna["Posizione"])
        posizioni_totali = list(dict.fromkeys(posizioni_totali)) #Rimuove le posizioni uguali
        pos_scelta = input("Dove vuoi posizionare l'oggetto?"+' '.join(map(str, posizioni_totali))+": ")
        if pos_scelta in posizioni_totali:
            ultima_posizione = pos_scelta
        else:
            print("La posizione non esiste. Creane una nuova")
        nuovo = False
    else:
        nuovo = True 
    crea_codice(ultimo_codice,ultima_posizione,prodotto,nuovo_scaffale=nuovo,dop=doppione,numQ=q,prec=quantita_precedente)

#RICERCA VALORI
def ricerca(r,chiave,**kwargs): 

    #Ottieni le variabili fornite
    codice_prodotto = kwargs.get("item")
    nome_prodotto = kwargs.get("nome")
    scaffale = kwargs.get("scaf")
    trovato = False

    #Cercare un codice, un nome o un luogo?
    if scaffale != None:
        oggetto_ricerca = scaffale       

    if codice_prodotto != None:
        oggetto_ricerca = codice_prodotto

    elif nome_prodotto != None:
        oggetto_ricerca = nome_prodotto       

    documento.seek(0)
    for i in r:    
        if oggetto_ricerca.lower().strip() == i[chiave].lower().strip():
            trovato = True
            if i["Posizione"].strip() == "":
                print("Posizione non conosciuta")
            else:
                print("---------------------------")
                print(f'Codice Prodotto: {i["Codice Prodotto"]},\nNome Prodotto: {i["Nome Prodotto"]},\nPosizione: {i["Posizione"]},\nQuantità: {i["Quantità"]}')
                print("---------------------------")
    if trovato != True:
        print("Ricerca fallita, non è stato trovato nulla.")

#Scelta modalità
def opzioni(r):

    spazio_campione = ["Inserire nuovo oggetto (0[Default])","Cercare oggetto (1)","Analisi scaffale (2)"]
    documento.seek(0)    
    indici_numeri = []
    for valore in r:
        ultimo_codice = valore["Codice Prodotto"]
        ultima_posizione = valore["Posizione"]
        if ultima_posizione != "Posizione":
            posizione_divisa = re.match(r"([a-z]+)([0-9]+)",ultima_posizione,re.I)
            #print(posizione_divisa[0],posizione_divisa[1])
            numero = posizione_divisa[0]
            lettera = posizione_divisa[1]
            indici_numeri.append(numero)
            
    if ultima_posizione == "Posizione":
        ultima_posizione = "A0"
    else:
        n_max = max(indici_numeri) #Scaffale più grande
        ultima_posizione = lettera+n_max
        #print(ultima_posizione)
    if ultimo_codice == "Codice Prodotto":
        ultimo_codice = 0
        
    #print(ultimo_codice,ultima_posizione)
    try:
        scelta = int(input("Cosa vuoi fare:\n" +'\n'.join(map(str, spazio_campione))+"\n? "))
        
        if scelta == 0:
            crea_oggetto(ultimo_codice,ultima_posizione)

        elif scelta == 1:
            try:
                mod = int(input("Vuoi cercare per codice (0) o per nome (1[Default]) del prodotto? "))
                if mod == 0:
                    chiave = "Codice Prodotto"
                    codice_prodotto = input("Inserire codice prodotto: ")
                    ricerca(r,chiave,item=codice_prodotto)
                elif mod == 1:
                    chiave = "Nome Prodotto"
                    nome_prodotto = input("Inserire nome prodotto: ")
                    ricerca(r,chiave,nome=nome_prodotto)
                else:
                    chiave = "Nome Prodotto"
                    nome_prodotto = input("Inserire nome prodotto: ")
                    ricerca(r,chiave,nome=nome_prodotto)
            except:
                chiave = "Nome Prodotto"
                nome_prodotto = input("Inserire nome prodotto: ")
                ricerca(r,chiave,nome=nome_prodotto)
        
        elif scelta == 2:
            chiave = "Posizione"
            scaffale = input("Inserire nome scaffale: ")
            ricerca(r,chiave,scaf=scaffale)

        else:
            print("Devi inserire il numero della modalità che vuoi usare, numero compreso tra 0 e 3")    
    except Exception as e:
        #print("Devi inserire il numero della modalità che vuoi usare, numero compreso tra 0 e 3",e)
        crea_oggetto(ultimo_codice,ultima_posizione)
        
if __name__ == "__main__":
    try:
        while True:
            opzioni(r)
    finally:
        print("Uscendo..")
    
