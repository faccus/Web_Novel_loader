FROM python:3

ADD requirments.txt .
ADD credentials.json .

RUN python3 -m pip install -r requirments.txt

ADD telegram_bot.py .
ADD novelfull.py .
ADD royalroad.py .


CMD python3 telegram_bot.py