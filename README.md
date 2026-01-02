# Apache_Hive_Test_Application
Analysis of a prototype or production version of a modern OLAP/OLTP( Apache Hive) database management system.

Here’s the detailed instructions on how to run the image, container, and Docker setup, including environment variables:

## Prerequisites
Before running the application, ensure you have the following installed:
- Docker (version 20.10 or later)

### Verify the Container is Running
Check the running container:
```bash
docker ps
```
You should see the container `Apache-Hive` running with the exposed ports.


## How to Run the Application with Docker Compose

If you prefer using Docker Compose, a `docker-compose.yaml` is [here](docker-compose.yaml)

Run the application using:
```bash
docker compose up --build
```


## Accessing Apache Hive

Once the container is running, you can access HiveServer2 at:
- **JDBC Connection String**: `jdbc:hive2://localhost:10000/default`
- **WebHCat**: `http://localhost:10002`
- **Metastore**: Port `9083`

## Troubleshooting

### Common Issues
1. **Port Conflict**: Ensure ports `10000`, `10002`, and `9083` are not in use by other applications.
2. **Container Not Starting**: Check logs using:
   ```bash
   docker logs Apache-Hive
   ```

3. **Environment Variable Issues**: Verify the environment variables are correctly set in the  `docker-compose.yaml` file.


Feel free to contribute or raise issues for improvements!


## License

This project is for educational purposes only.
