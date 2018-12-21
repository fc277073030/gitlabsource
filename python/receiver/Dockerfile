FROM python:3.7-slim

RUN apt-get update
RUN apt-get install -y python-dev gcc
RUN apt-get install -y git
RUN pip install git+git://github.com/cloudevents/sdk-python 
RUN pip install requests
RUN pip install bottle

ADD receiver.py /receiver.py

CMD ["python", "-u", "/receiver.py"]
