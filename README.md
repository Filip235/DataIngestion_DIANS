# DIANS_DataIngestion1.
1.Download Kafka from https://kafka.apache.org/downloads

2. Download Zookeeper from https://zookeeper.apache.org/releases.html
3. 
4. Extract the downloaded zip Kafka to desktop with name kafka.
5. Open 2 Command Prompts (cmd).
6. On the first cmd type cd C:\kafka or path\to\your\kafka-folder. Then type .\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties .   This starts the zookeeper.
7. On the second cmd type cd C:\kafka or path\to\your\kafka-folder. Then type .\bin\windows\kafka-server-start.bat .\config\server.properties .
8. Open third cmd and navigate to kafka folder. Then run    bin\windows\kafka-topics.bat --create --topic stock-data --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
This will create topic stock-data and will store all the data from the app to this topic.
9. Download the python app from GitHub.
10. Download Postgres from https://www.postgresql.org/download/
11. Connect to the server on PGAdmin4 with user,host and password from the app.py
12. Download the stock_prices folder from GitHub and extract it to C:.....\tmp\kafka-logs
13. Finally start app.py and navigate to http://127.0.0.1:5000
14. Enjoy the program.
15. WARNING! Before closing the app, close kafka on cmd with CTRL+C. This is crucial if you want to run the app all over again, otherwise kafka will crash and the app wont start!


