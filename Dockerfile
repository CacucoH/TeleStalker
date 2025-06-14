FROM python:3.13.2-slim
WORKDIR /app
COPY requirements.txt /app/
ENV TZ="Europe/Moscow"
RUN pip3 install --upgrade setuptools && pip3 install -r requirements.txt
COPY . .
ENTRYPOINT [ "python3", "deleter.py" ]