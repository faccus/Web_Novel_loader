FROM ubuntu

RUN apt-get update && apt-get install python3-dev python3-pip -y

ADD novelfull.py code/novelfull.py
ADD royalroad.py code/royalroad.py
ADD requirments.txt code/requirments.txt

RUN python3 -m pip install -r code/requirments.txt