PORT=7555
sudo neo4j-community-3.4.0/bin/neo4j stop
ps x | grep runserver | grep $PORT | sed 's/^ //g' | cut -d' ' -f 1 | xargs kill
