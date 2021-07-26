FROM python:3

WORKDIR /jumpcutter

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN apt update && apt install -y ffmpeg

COPY jumpcutter.py .
COPY run.sh .
RUN chmod +x run.sh

ENTRYPOINT [ "/jumpcutter/run.sh" ]