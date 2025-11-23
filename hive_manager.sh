#!/bin/bash

# --- CONFIGURATION ---
CONTAINER_NAME="Apache-Hive"
IMAGE_NAME="apache/hive:4.0.0"
HIVE_PORT="10000"
WEB_UI_PORT="10002"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# --- INTERNAL FUNCTIONS ---

function header {
    echo -e "\n${YELLOW}--- $1 ---${NC}"
}

function check_docker_status {
    if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
        echo -e "${GREEN}✔ Docker Container is RUNNING.${NC}"
        return 0
    elif [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        echo -e "${RED}✖ Docker Container is STOPPED.${NC}"
        return 1
    else
        echo -e "${RED}✖ Docker Container does not exist.${NC}"
        return 2
    fi
}

function check_hadoop_status {
    # We check Hadoop by asking it to list the root directory inside the container
    if docker exec $CONTAINER_NAME hadoop fs -ls / > /dev/null 2>&1; then
        echo -e "${GREEN}✔ Hadoop (HDFS) is ONLINE and readable.${NC}"
    else
        echo -e "${RED}✖ Hadoop File System is UNREACHABLE.${NC}"
    fi
}

function check_hive_connection {
    # We try to run a simple "SHOW DATABASES" command
    if docker exec $CONTAINER_NAME beeline -u "jdbc:hive2://localhost:10000/" -e "SHOW DATABASES;" > /dev/null 2>&1; then
        echo -e "${GREEN}✔ Hive SQL Engine is READY for queries.${NC}"
    else
        echo -e "${RED}✖ Hive Server is NOT responding yet (still starting?).${NC}"
    fi
}

# --- COMMANDS ---

function start_services {
    header "STARTING SERVICES"
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        echo "Resuming existing container..."
        docker start $CONTAINER_NAME
    else
        echo "Creating new container..."
        docker run -d -p $HIVE_PORT:$HIVE_PORT -p $WEB_UI_PORT:$WEB_UI_PORT \
        --env SERVICE_NAME=hiveserver2 \
        --name $CONTAINER_NAME $IMAGE_NAME
    fi
    
    echo "Waiting for services to initialize..."
    # A visual loading bar
    for i in {1..15}; do printf "▓"; sleep 2; done
    echo " Done."
    echo "Run './hive_manager.sh status' to verify."
}

function full_status_check {
    header "SYSTEM HEALTH CHECK"
    
    # 1. Check Container
    check_docker_status
    STATUS=$?
    
    if [ $STATUS -eq 0 ]; then
        # 2. Check Hadoop Internal
        echo -n "Checking Hadoop... "
        check_hadoop_status
        
        # 3. Check Hive Connectivity
        echo -n "Checking Hive...   "
        check_hive_connection
        
        header "ACCESS INFO"
        echo "👉 Web UI:   http://localhost:$WEB_UI_PORT"
        echo "👉 JDBC URL: jdbc:hive2://localhost:$HIVE_PORT/"
    fi
}

function run_test_job {
    header "RUNNING SMOKE TEST"
    echo "This will create a table, insert data, and select it to prove the engine works."
    
    docker exec -it $CONTAINER_NAME beeline -u "jdbc:hive2://localhost:10000/" -e "
        CREATE DATABASE IF NOT EXISTS smoke_test;
        USE smoke_test;
        CREATE TABLE IF NOT EXISTS test_data (message STRING);
        INSERT INTO test_data VALUES ('Hadoop and Hive are working!');
        SELECT * FROM test_data;
    "
}

function connect_shell {
    header "ENTERING HIVE SHELL"
    docker exec -it $CONTAINER_NAME beeline -u "jdbc:hive2://localhost:10000/"
}

function stop_services {
    header "STOPPING SERVICES"
    docker stop $CONTAINER_NAME
    echo -e "${GREEN}✔ Services stopped.${NC}"
}

function clean_all {
    header "NUCLEAR CLEAN"
    echo -e "${RED}WARNING: This deletes the container and ALL data inside it.${NC}"
    read -p "Are you sure? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker rm -f $CONTAINER_NAME
        echo -e "${GREEN}✔ System wiped clean.${NC}"
    fi
}

# --- MENU ---

case "$1" in
    start)   start_services ;;
    status)  full_status_check ;;
    test)    run_test_job ;;
    connect) connect_shell ;;
    stop)    stop_services ;;
    clean)   clean_all ;;
    *)       
        echo "Usage: ./hive_manager.sh [command]"
        echo "  start    -> Start Docker + Hive + Hadoop"
        echo "  status   -> Deep health check of all components"
        echo "  test     -> Run a real MapReduce job to prove it works"
        echo "  connect  -> Open the SQL command line"
        echo "  stop     -> Pause everything"
        echo "  clean    -> Delete everything"
        ;;
esac
