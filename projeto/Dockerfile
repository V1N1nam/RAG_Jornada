WORKDIR /app

ENV PYTHONPATH=/app

COPY . /app

RUN pip install -r requirements.txt

CMD ["python", "app/api.py"]