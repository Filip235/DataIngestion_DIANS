1. Download Kafka from https://kafka.apache.org/downloads
2. Download Zookeeper from https://zookeeper.apache.org/releases.html
3. Extract the downloaded zip Kafka to desktop with name kafka.
4. Open 2 Command Prompts (cmd).
5. On the first cmd type cd C:\kafka or path\to\your\kafka-folder. Then type .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties .   This starts the zookeeper.
6. On the second cmd type cd C:\kafka or path\to\your\kafka-folder. Then type .\bin\windows\kafka-server-start.bat .\config\server.properties .
7. Open third cmd and navigate to kafka folder. Then run    bin\windows\kafka-topics.bat --create --topic stock-data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
This will create topic stock-data and will store all the data from the app to this topic.
8. Download the python app from GitHub.
9. Download Postgres from https://www.postgresql.org/download/
10. Connect to the server on PGAdmin4 with user,host and password from the app.py
11. Download the stock_prices folder from GitHub and extract it to C:.....\tmp\kafka-logs
12. Finally start app.py and navigate to http://127.0.0.1:5000
13. Enjoy the program.
14. WARNING! Before closing the app, close kafka on cmd with CTRL+C. This is crucial if you want to run the app all over again, otherwise kafka will crash and the app wont start!


