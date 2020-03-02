ps aux | grep client.py | awk -c '{ print $2 }' | xargs kill -9
ps aux | grep client.py | awk -c '{ print $2 }' | xargs kill -9

