# Start your image Apache Hive Test Application
FROM node:apache/hive:4.0.0

# The /app directory should act as the main application directory
WORKDIR /Apache_Hive_Test_Application


EXPOSE 8080

# Start the app using python manage.py runserver command
CMD [ "python", "manage.py", "runserver", "0.0.0.0:8080" ]