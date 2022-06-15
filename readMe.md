## Starting Metier-Protocol Node
#postgres: 
- Ensure postgres is running or install postgres
- Create database `metieruser` with user `metieruser` and password `metier123` and ensure it is running on port `5432`

#metier-node:
Go to the app folder `cd src` 
run `cp config.json.example config.json`
run `pip3 install -r requirements.txt`
run `python node.py`
run `python heartbeat.py`