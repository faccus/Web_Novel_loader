FROM ubuntu

RUN apt-get update && apt-get install python3-dev python3-pip -y

ADD novelfull.py .
ADD royalroad.py .
ADD telegram_bot.py .

ADD requirments.txt .
ADD credentials.json .

RUN python3 -m pip install -r requirments.txt

CMD python3 telegram_bot.py