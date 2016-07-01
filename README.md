Medlemssys
==========

Medlemsregister for norske organisasjonar.

Bygd på datamodellen til Norsk Målungdom sitt gamle Access-register. Ein del
pragmatiske løysingar som fylgje av det.  Ein del hardkoda NMU-ismer, men det
forsvinn viss nokon (lag saker/issues).  All bruk eg kjenner til har klart seg
med det som er.  Vert sakte modernisert.

- Skrive i Python (Django)
- I aktiv bruk sidan 2014
- Kan lesa OCR-filer
- Admin-grensesnitt med ein del hendig filtrering


Installasjon
------------

Ein kjapp guide for å koma i gang med utvikling.

    cd medlemssys

    # Lag virtuelt Python-miljø
    virtualenv env
    . env/bin/activate
    pip install -r requirements/local.txt

    # Medlemsregisteret køyrer på postgresql som standard.
    # Du må oppretta ein database.
    createdb medlemssys

    # Set opp testdatabasa
    python manage.py migrate
    python manage.py loaddata start_data.json

    # Lag deg ein brukar
    python manage.py createsuperuser

    python manage.py runserver

No kan du gå til http://127.0.0.1:8000/admin/, logga inn og testa ut installasjonen.


Innhenting av postnummer
------------------------

Hent ned Erik Bolstad sin CSV (TSV, menmen)-fil og les han inn:

    wget http://www.erikbolstad.no/postnummer-koordinatar/txt/postnummer.csv
    python manage.py postnr_bolstad_import postnummer.csv


Importering av medlemsregisterdata
----------------------------------

Filformatet ventar NMU-format i CSV.  Ditt register er truleg annleis, men det
er heldigvis lett å skriva adaptarar.  Eventuelt å berre endra litt på namn i
CSV-filene.  T.d. har eg henta over eit register frå Mamut ein gong.


Format for lag, einaste som er nødvendig er "LLAG" (namn) og "lid" (id):

    DIST,FLAG,LLAG,lid,ANDSVAR,LOKALSATS

Format for medlemar:

    REGISTERKODE,LAGSNR,MEDLNR,FORNAMN,MELLOMNAMN,ETTERNAMN,
    TILSKRIFT1,TILSKRIFT2,POST,VERVA,VERV,LP,GJER,MERKNAD,
    KJØNN,INN,INNMEDL,UTB,UT_DATO,MI,MEDLEMINF,TLF_H,TLF_A,
    E_POST,H_TILSKR1,H_TILSKR2,H_POST,H_TLF,Ring_B,Post_B,
    MM_B,MNM_B,BRUKHEIME,FARRETOR,RETUR,REGBET,HEIMEADR,
    REGISTRERT,TILSKRIFT_ENDRA,FØDEÅR,Epost_B


For å importera med standardverdiar:

    # Usage: manage.py medlem_import [options] [ lokallag.csv [ medlem.csv [ betaling.csv ] ] ]
    ./manage.py medlem_import

Du kan setja standardfilene i settings/local.py. Instellingane heiter:

    MEDLEM_CSV
    GIRO_CSV
    LAG_CSV


Køyr testane
------------

Det er alt for få testar, men eit par. Skriv gjerne fleire, og køyr dei ved kodeendring.

    ./manage test medlem giro statistikk
