FROM python:slim

RUN pip install kubernetes
RUN pip install python-gitlab

COPY controller.py /controller.py

CMD ["python", "-u", "controller.py"]
