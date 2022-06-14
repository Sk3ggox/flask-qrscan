FROM debian:bullseye-slim
RUN apt-get update -y
RUN apt-get install -y nano bash pip ffmpeg libsm6 libxext6 
WORKDIR /app
ADD ./app/ /app/
ENV STATIC_URL /static
ENV STATIC_PATH /var/www/app/static
COPY ./requirements.txt /var/www/requirements.txt
RUN pip install -r /var/www/requirements.txt
CMD ["python3", "views.py"]