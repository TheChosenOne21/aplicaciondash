FROM python:3.10

WORKDIR /AplicacionDash

COPY . /AplicacionDash

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 8080

CMD ["python", "app_dash.py"]