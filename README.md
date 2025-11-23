# Apache_Hive_Test_Application
Analysis of a prototype or production version of a modern OLAP/OLTP( Apache Hive) database management system.

Here’s the detailed instructions on how to run the image, container, and Docker setup, including environment variables:

## Prerequisites
Before running the application, ensure you have the following installed:
- Docker (version 20.10 or later)
- Docker Compose (version 1.29 or later)


## How to Run the Apache Hive Image and Container

### Step 1: Pull the Apache Hive Image
To use the Apache Hive image, pull it from Docker Hub:
```bash
docker pull apache/hive:4.0.0
```

### Step 2: Run the Apache Hive Container
Run the container using the following command:
```bash
docker run -d \
  --name Apache-Hive \
  -p 10000:10000 \
  -p 10002:10002 \
  -p 9083:9083 \
  -e HIVE_HOME=/opt/hive \
  -e HADOOP_HOME=/opt/hadoop \
  -e JAVA_HOME=/usr/local/openjdk-8 \
  apache/hive:4.0.0
```

### Step 3: Verify the Container is Running
Check the running container:
```bash
docker ps
```
You should see the container `Apache-Hive` running with the exposed ports.

## Quick Start 
After a successfull installation you can use a customized script here that checks everything and starts all requirements 

1. Setup and Usage
First, make it executable:

```bash
chmod +x hive_manager.sh
```

```bash
./hive_manager.sh start 
```
(Wait about 30 seconds for initialization)

More commands here 

```bash
    echo "Usage: ./hive_manager.sh [command]"
    echo "  start    -> Start Docker + Hive + Hadoop"
    echo "  status   -> Deep health check of all components"
    echo "  test     -> Run a real MapReduce job to prove it works"
    echo "  connect  -> Open the SQL command line"
    echo "  stop     -> Pause everything"
    echo "  clean    -> Delete everything"
```

## Environment Variables

### Image Environment Variables
The following environment variables are set in the Apache Hive image:
- `HIVE_HOME=/opt/hive`  
  Path to the Hive installation directory.
- `HADOOP_HOME=/opt/hadoop`  
  Path to the Hadoop installation directory.
- `JAVA_HOME=/usr/local/openjdk-8`  
  Path to the Java installation directory.
- `SERVICE_NAME=hiveserver2`  
  Name of the Hive service.
- `PATH=/opt/hive/bin:/opt/hadoop/bin:/usr/local/openjdk-8/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`  
  System path for binaries.
- `JAVA_VERSION=8u342`  
  Java version used in the image.
- `LANG=C.UTF-8`  
  Default language setting.

### Container Environment Variables
When running the container, you can set the following environment variables:
- `HIVE_HOME=/opt/hive`  
  Path to the Hive installation directory.
- `HADOOP_HOME=/opt/hadoop`  
  Path to the Hadoop installation directory.
- `JAVA_HOME=/usr/local/openjdk-8`  
  Path to the Java installation directory.

---

## How to Run the Application with Docker Compose

If you prefer using Docker Compose, a `docker-compose.yaml` is [here](docker-compose.yaml)

Run the application using:
```bash
docker compose up --build
```

## Stopping and Removing Containers

### Stop the Container
To stop the running container:
```bash
docker stop Apache-Hive
```

### Remove the Container
To remove the container:
```bash
docker rm Apache-Hive
```

## Accessing Apache Hive

Once the container is running, you can access HiveServer2 at:
- **JDBC Connection String**: `jdbc:hive2://localhost:10000/default`
- **WebHCat**: `http://localhost:10002`
- **Metastore**: Port `9083`

---

## Troubleshooting

### Common Issues
1. **Port Conflict**: Ensure ports `10000`, `10002`, and `9083` are not in use by other applications.
2. **Container Not Starting**: Check logs using:
   ```bash
   docker logs Apache-Hive
   ```

3. **Environment Variable Issues**: Verify the environment variables are correctly set in the `docker run` or `docker-compose.yaml` file.


Feel free to contribute or raise issues for improvements!


## License

This project is for educational purposes only.
