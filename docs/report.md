# Portfolio: Multi-Node Hive & Climate Intelligence Platform
**MBV Climate and Ocean Intelligence Africa**

## 1. Executive Summary
This project presents a production-grade simulation of a distributed big data ecosystem. By orchestrating a multi-node **Apache Hadoop** and **Apache Hive** cluster within **Docker**, we've built a scalable foundation for "MBV Climate and Ocean Intelligence Africa." The system integrates a robust data engineering pipeline (ORC/Snappy/Partitioning) with a Django-based analytical application, enabling both climate pattern discovery and benchmark-driven Hive performance optimization.

---

## 2. Integrated System Architecture

The platform is designed as a modular 7-container stack, ensuring high availability and separation of concerns.

### 2.1 The Distributed Storage Engine (Hadoop HDFS)
We implemented a **3-Node Cluster** following the Master/Slave architecture specified in the seminar requirements:
- **`master-node` (NameNode)**: Orchestrates the filesystem namespace and manages block locations (`hdfs://master-node:9000`).
- **`slave-node-1` & `slave-node-2` (DataNodes)**: Provide distributed physical storage with a **Replication Factor of 2**, ensuring zero data loss if a slave fails.
- **Port Visibility**: HDFS UI is accessible at `localhost:9870`, providing real-time telemetry on cluster health.

### 2.2 The SQL Data Warehouse (Apache Hive 4.0.0)
The Hive layer translates complex analytical requests into distributed computation tasks:
- **HiveServer2**: The gateway for JDBC and PyHive connections, configured with `NOSASL` for simplified integration.
- **Hive Metastore**: Decoupled from the compute layer to allow independent scaling.
- **External PostgreSQL Persistence**: Uses `postgres:9.6` for industry-standard metadata storage, ensuring schema definitions survive container restarts.

### 2.3 The Application Layer (Django Framework)
The application serves two critical functions:
1.  **Climate Dashboard**: Visualizes data points from the `africa_climate_observations` table.
2.  **Hive Assessment Tool**: A specialized benchmarking suite that runs cross-join and aggregation scenarios to identify performance bottlenecks.

---

## 3. Advanced Data Engineering & Optimizations

To demonstrate portfolio-grade engineering, we implemented storage-layer optimizations that reduce I/O and increase query speed:

| Feature | Implementation | Benefit |
| :--- | :--- | :--- |
| **Storage Format** | **ORC (Optimized Row Columnar)** | Drastic reduction in disk footprint and faster column-level scans. |
| **Compression** | **SNAPPY** | High-performance compression optimized for big data workloads. |
| **Partitioning** | **By `year` and `region`** | Enables "Partition Pruning," skipping 90%+ of data during regional or annual queries. |
| **Bucketing** | **By `station_id` (32 Buckets)** | Optimizes "Map-Side Joins" when correlating observations with station metadata. |

---

## 4. Key Configuration & Integration Points

### 4.1 Hive Gateway Alignment (`hive-site.xml`)
The system is tuned for the Docker environment using explicit bindings:
```xml
<property>
    <name>hive.server2.thrift.bind.host</name>
    <value>0.0.0.0</value>
</property>
<property>
    <name>hive.server2.authentication</name>
    <value>NOSASL</value>
</property>
```

### 4.2 Application-to-Hive Connectivity
The Django application uses a custom `HiveConnectionManager` (via PyHive) to bridge the relational metadata in HDFS with the application's models. This allows for:
- **Dynamic Schema Discovery**: Listing Hive tables directly in the app.
- **ETL Telemetry**: Logging every query's execution time for performance assessment.

---

## 5. Challenges & Engineering Decisions

### 5.1 Platform Emulation Overhead
Deploying `linux/amd64` images on **Apple Silicon (ARM64)** introduces emulation latency. We addressed this by increasing service timeouts and optimizing JVM memory flags (`HADOOP_CLIENT_OPTS`) to ensure stability during the 60-second HiveServer2 initialization window.

### 5.2 Hive 4.0.0 JDBC Driver
We manually injected the `postgresql-42.7.2.jar` driver into the `/opt/hive/lib` directories via Docker volumes to resolve initial Metastore connectivity issues without requiring custom image builds.

---

## 6. Conclusion
The "MBV Climate and Ocean Intelligence Africa" platform effectively bridges the gap between raw environmental sensor data and actionable intelligence. By simulating a real-world distributed cluster, the project demonstrates proficiency in **Big Data Architecture**, **Container Orchestration**, and **Full-Stack Data Integration**.

---
*Developed for the Databases for Big Data Seminar | Africa Climate Initiative 2024*
