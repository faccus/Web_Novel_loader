FROM python

ADD novelfull.py code/novelfull.py
ADD royalroad.py code/royalroad.py
ADD requirments.txt code/requirments.txt

RUN python3 -m pip install -r requirments