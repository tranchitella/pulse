# pull official base image
FROM python:3.12-slim

# create the app user
RUN addgroup --system app && adduser --system --group app

# Set the working directory
ENV APP_HOME=/app
RUN mkdir $APP_HOME
RUN mkdir $APP_HOME/staticfiles
RUN mkdir $APP_HOME/mediafiles
WORKDIR $APP_HOME

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# install system dependencies
RUN apt-get update && apt-get install -y netcat-openbsd

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# Copy the entrypoint   
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh

# Copy the Django application code
COPY ./manage.py $APP_HOME
COPY ./pulse $APP_HOME/pulse

# chown all the files to the app user
RUN chown -R app:app $APP_HOME

# change to the app user
USER app

# Expose the port the app runs on
EXPOSE 8000

# run entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
