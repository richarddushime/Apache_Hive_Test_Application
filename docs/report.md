# MBV Climate and Ocean Intelligence Africa: Project Report

## 1. Executive Summary
This project successfully demonstrates the implementation of a multi-node distributed storage and computation environment using **Apache Hive** and **Hadoop (HDFS)**. The system is designed to simulate a production-grade big data infrastructure for "MBV Climate and Ocean Intelligence Africa," enabling the ingestion, storage, and analysis of large-scale environmental datasets (Climate and Ocean conditions).

## 2. Project Objectives
The primary goals of this simulation were:
- **Distributed Architecture**: Deploy a resilient multi-node HDFS cluster.
- **Data Engineering Workflow**: Implement a complete pipeline from data generation to analytical querying.
- **Relational Abstraction**: Use Apache Hive to provide SQL-like access to distributed data.
- **Cloud-Native Simulation**: Orchestrate the entire stack using Docker for portability and development efficiency.

## 3. System Architecture

The infrastructure is composed of 7 specialized containers working in orchestration:

### 3.1 Distributed Storage Layer (HDFS)
- **NameNode (1)**: The master node managing the file system namespace and block metadata.
- **DataNodes (2)**: Two independent worker nodes providing physical storage.
- **Replication Factor**: Set to 2, ensuring that all data is mirrored across both worker nodes for high availability.

### 3.2 Computation & Metadata Layer (Hive)
- **HiveServer2**: The SQL interface accepting JDBC/PyHive connections (Upgraded to **Apache Hive 4.0.0**).
- **Hive Metastore**: Manages schema definitions and table partitioning.
- **PostgreSQL 9.6**: Used as a robust external database for the Hive Metastore, replacing the default embedded Derby database for enterprise-ready persistence.

### 3.3 Application Layer
- **Django Application**: A Python-based interface for interacting with the data warehouse, providing RESTful access to analytical results.

## 4. Data Engineering Workflow

### 4.1 Data Synthesis
Using `data_generator.py`, the system generates synthetic datasets representing real-world sensors:
- **Climate Data**: Temperature, Rainfall, and Humidity across 5 African regions.
- **Ocean Data**: Sea Surface Temperature (SST), pH levels, and Salinity.

### 4.2 Ingestion & Storage
- Data is ingested as **External Tables** in Hive.
- **Storage Format**: `TEXTFILE` with CSV delimiter (convertible to ORC/Parquet for production optimization).
- **HDFS Placement**: Data is automatically partitioned by the NameNode and distributed across the DataNode cluster.

### 4.3 Analytical Queries
The system supports complex temporal and regional analysis via HiveQL (`analyze.hql`), including:
- Moving averages of environmental indicators.
- Anomaly detection (e.g., correlations between low pH and high SST).
- Multi-dimensional joins between climate and ocean observations.

## 5. Implementation Achievements

### ✅ Multi-Node Resilience
The cluster successfully reports **2 live DataNodes** with a total capacity of **~447GB**. This verifies that the "split-brain" distributed storage model is functioning correctly.

### ✅ Version Advancement
The stack was successfully upgraded to **Apache Hive 4.0.0**, leveraging modern performance improvements and fixed compatibility for distributed environments.

### ✅ Configuration Management
Custom `core-site.xml`, `hdfs-site.xml`, and `hive-site.xml` files were implemented to ensure proper inter-service communication and HDFS replication policies.

## 6. Challenges & Observations

### 6.1 Platform Emulation (ARM64)
Running `linux/amd64` big data images on Apple Silicon (ARM64) results in a performance overhead due to binary translation. While functional for simulation, native ARM images or cloud-based AMD64 runners are recommended for production performance.

### 6.2 HiveServer2 Initialization
Big data services have significantly longer startup times than typical microservices. HiveServer2 requires approximately 60-90 seconds to fully bind its Thrift interface after the container reports "started."

## 7. Conclusions & Future Work
This project demonstrates that a robust, multi-node Hive environment can be simulated locally with high fidelity. The "MBV Climate and Ocean Intelligence Africa" dataset is now integrated into a scalable, fault-tolerant infrastructure.

### Recommended Next Steps:
1. **Performance Tuning**: Implement `ORC` or `Parquet` storage formats with **Snappy compression**.
2. **Partitioning**: Introduce partitioning by `region` and `year/month` to optimize query scan times.
3. **Advanced Analytics**: Integrate **Apache Spark** over the existing HDFS layer for real-time stream processing of sensor data.
4. **Visualization**: Connect the Django application to a modern BI tool (e.g., Superset) for visual intelligence dashboards.

---
*Prepared by Antigravity AI for MBV Climate and Ocean Intelligence Africa*
