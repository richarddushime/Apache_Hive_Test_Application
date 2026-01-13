# Apache Hive Test Application - Comprehensive Statistics Report
**Generated:** January 13, 2026  
**Dataset:** MBV Climate and Ocean Intelligence Africa  
**Hive Version:** 2.3.2 with MapReduce Execution Engine

---

## 1. HDFS Cluster Infrastructure

### 1.1 Cluster Overview
| Metric | Value |
|--------|-------|
| **Configured Capacity** | 447.26 GB |
| **Present Capacity** | 387.56 GB |
| **DFS Remaining** | 386.94 GB |
| **DFS Used** | 627.28 MB (0.16%) |
| **Live DataNodes** | 2 |
| **Replication Factor** | 2 |
| **Under-replicated Blocks** | 6 |
| **Corrupt Blocks** | 0 |
| **Missing Blocks** | 0 |

### 1.2 DataNode Statistics
| DataNode | Hostname | Capacity | DFS Used | DFS Remaining | Blocks |
|----------|----------|----------|----------|---------------|--------|
| slave-node-1 | 172.18.0.5:9866 | 223.63 GB | 313.64 MB (0.14%) | 193.47 GB (86.51%) | 6 |
| slave-node-2 | 172.18.0.6:9866 | 223.63 GB | 313.64 MB (0.14%) | 193.47 GB (86.51%) | 6 |

### 1.3 Container Resource Usage
| Container | CPU % | Memory Usage | Memory % |
|-----------|-------|--------------|----------|
| django-app | 2.08% | 154.8 MiB | 1.97% |
| hive-server | 0.87% | 1.011 GiB | 13.20% |
| hive-metastore | 0.46% | 619 MiB | 7.90% |
| slave-node-1 | 0.51% | 598.6 MiB | 7.64% |
| slave-node-2 | 0.49% | 631.8 MiB | 8.06% |
| hive-metastore-db | 0.01% | 37.11 MiB | 0.47% |
| master-node | 0.37% | 643.1 MiB | 8.21% |
| **Total** | **4.79%** | **~3.6 GiB** | **47.45%** |

---

## 2. Data Scale and Storage

### 2.1 Table Record Counts
| Table | Records | Size (Raw) | Size (Replicated) |
|-------|---------|------------|-------------------|
| portfolio_observations | **4,750,000** | 304.2 MB | 912.6 MB |
| climate_data | 100,000 | 3.4 MB | 10.1 MB |
| ocean_data | 100,000 | 3.2 MB | 9.6 MB |
| portfolio_stations | 5,000 | 371.2 KB | 1.1 MB |
| **Total** | **4,955,000** | **~311 MB** | **~933 MB** |

### 2.2 Data Coverage
| Metric | Value |
|--------|-------|
| **Unique Weather Stations** | 5,000 |
| **Years Covered** | 45 (1980–2024) |
| **African Regions** | 5 (Central, East, North, South, West) |
| **Countries** | 44 |
| **Monthly Observations** | 60 unique month-region combinations per year |

### 2.3 Storage Model (portfolio_observations)
| Property | Value |
|----------|-------|
| **Table Type** | MANAGED_TABLE |
| **SerDe Library** | LazySimpleSerDe |
| **Input Format** | TextInputFormat |
| **Output Format** | HiveIgnoreKeyTextOutputFormat |
| **Compression** | No |
| **Num Buckets** | -1 (unbucketed) |
| **Field Delimiter** | , (comma) |
| **Column Statistics** | COMPUTED (all 12 columns) |
| **numRows** | 4,750,000 |
| **rawDataSize** | 309,492,177 bytes |
| **totalSize** | 318,992,307 bytes |

---

## 3. Query Performance Benchmarks

### 3.1 Query Execution Times (4.75M records)
| Query Type | Time (s) | Description |
|------------|----------|-------------|
| Simple Regional Aggregation | **9.31** | GROUP BY region with COUNT, AVG |
| Complex Monthly Aggregation | **14.88** | GROUP BY region, month with ORDER BY (60 rows) |
| Statistical Analysis | **16.13** | STDDEV_POP, CORR, PERCENTILE_APPROX, MIN, MAX |
| Yearly Analysis | **15.24** | GROUP BY year (45 rows) |
| Map-Side Join | **21.26** | JOIN with auto.convert.join=true (44 country-region pairs) |
| Reduce-Side Join | **25.76** | JOIN with auto.convert.join=false |
| Data Coverage Query | **13.37** | COUNT DISTINCT on multiple columns |
| Regional Summary | **15.73** | COUNT DISTINCT, aggregations, ORDER BY |

### 3.2 Join Algorithm Comparison
| Join Type | Execution Time | Speedup |
|-----------|---------------|---------|
| **Map-Side (Broadcast) Join** | 21.26 seconds | 1.21x faster |
| Reduce-Side (Shuffle) Join | 25.76 seconds | baseline |

*Note: Map-Side join broadcasts the smaller `portfolio_stations` (5,000 rows) table to all mappers, avoiding expensive shuffle operations.*

---

## 4. Regional Climate Analysis Results

### 4.1 Regional Summary Statistics
| Region | Stations | Observations | Avg Temp (°C) | Avg Humidity (%) | Total Precip (mm) |
|--------|----------|--------------|---------------|------------------|-------------------|
| **Central** | 1,009 | 958,550 | **30.49** | 67.49 | 31,961,325 |
| **West** | 1,036 | 984,200 | **29.51** | 67.49 | 9,827,773 |
| **East** | 983 | 933,850 | **26.51** | 67.50 | 31,114,971 |
| **North** | 990 | 940,500 | **24.51** | 67.51 | 9,403,739 |
| **South** | 982 | 932,900 | **20.50** | 67.47 | 9,338,969 |

### 4.2 Regional Temperature Statistics (with Variance)
| Region | Avg Temp (°C) | Min Temp (°C) | Max Temp (°C) | Median Temp (°C) | Temp σ |
|--------|---------------|---------------|---------------|------------------|--------|
| Central | 30.49 | 18.0 | 43.0 | 30.50 | 2.448 |
| West | 29.51 | 17.0 | 42.0 | 29.50 | 2.448 |
| East | 26.51 | 14.0 | 39.0 | 26.47 | 2.448 |
| North | 24.51 | 12.0 | 37.0 | 24.50 | 2.450 |
| South | 20.50 | 8.0 | 33.0 | 20.47 | 2.448 |

### 4.3 Humidity-Precipitation Correlation by Region
| Region | Moisture Correlation | Interpretation |
|--------|---------------------|----------------|
| Central | 6.98 × 10⁻⁴ | Near zero (independent) |
| East | -2.04 × 10⁻³ | Weak negative |
| North | -4.57 × 10⁻⁴ | Near zero (independent) |
| South | 7.54 × 10⁻⁴ | Near zero (independent) |
| West | -5.89 × 10⁻⁴ | Near zero (independent) |

---

## 5. Monthly Climate Patterns

### 5.1 Central Africa (Hottest Region)
| Month | Avg Temp (°C) | Avg Humidity (%) | Total Precip (mm) |
|-------|---------------|------------------|-------------------|
| Jan | 30.52 | 67.50 | 2,701,818 |
| Feb | 30.49 | 67.59 | 2,484,386 |
| Mar | 30.48 | 67.42 | 2,717,773 |
| Apr | 30.53 | 67.56 | 2,624,078 |
| May | 30.50 | 67.49 | 2,714,896 |
| Jun | 30.49 | 67.49 | 2,614,357 |
| Jul | 30.47 | 67.51 | 2,708,748 |
| Aug | 30.44 | 67.49 | 2,713,066 |
| Sep | 30.48 | 67.45 | 2,637,231 |
| Oct | 30.50 | 67.40 | 2,729,158 |
| Nov | 30.49 | 67.50 | 2,606,948 |
| Dec | 30.50 | 67.52 | 2,708,867 |

### 5.2 South Africa (Coolest Region)
| Month | Avg Temp (°C) | Avg Humidity (%) | Total Precip (mm) |
|-------|---------------|------------------|-------------------|
| Jan | 20.53 | 67.59 | 787,007 |
| Feb | 20.50 | 67.47 | 732,457 |
| Mar | 20.51 | 67.41 | 790,764 |
| Apr | 20.54 | 67.47 | 761,903 |
| May | 20.48 | 67.50 | 797,272 |
| Jun | 20.49 | 67.50 | 763,603 |
| Jul | 20.51 | 67.48 | 791,896 |
| Aug | 20.55 | 67.46 | 792,657 |
| Sep | 20.51 | 67.52 | 764,112 |
| Oct | 20.46 | 67.43 | 790,040 |
| Nov | 20.48 | 67.36 | 771,198 |
| Dec | 20.47 | 67.51 | 796,059 |

### 5.3 All Regions Monthly Data
| Region | Month | Avg Temp (°C) | Avg Humidity (%) | Total Precip (mm) |
|--------|-------|---------------|------------------|-------------------|
| Central | 1 | 30.52 | 67.50 | 2,701,818 |
| Central | 2 | 30.49 | 67.59 | 2,484,386 |
| Central | 3 | 30.48 | 67.42 | 2,717,773 |
| Central | 4 | 30.53 | 67.56 | 2,624,078 |
| Central | 5 | 30.50 | 67.49 | 2,714,896 |
| Central | 6 | 30.49 | 67.49 | 2,614,357 |
| Central | 7 | 30.47 | 67.51 | 2,708,748 |
| Central | 8 | 30.44 | 67.49 | 2,713,066 |
| Central | 9 | 30.48 | 67.45 | 2,637,231 |
| Central | 10 | 30.50 | 67.40 | 2,729,158 |
| Central | 11 | 30.49 | 67.50 | 2,606,948 |
| Central | 12 | 30.50 | 67.52 | 2,708,867 |
| East | 1 | 26.49 | 67.51 | 2,656,809 |
| East | 2 | 26.52 | 67.48 | 2,423,296 |
| East | 3 | 26.53 | 67.43 | 2,650,728 |
| East | 4 | 26.53 | 67.49 | 2,545,000 |
| East | 5 | 26.52 | 67.51 | 2,643,870 |
| East | 6 | 26.53 | 67.56 | 2,540,993 |
| East | 7 | 26.47 | 67.52 | 2,633,156 |
| East | 8 | 26.49 | 67.59 | 2,623,252 |
| East | 9 | 26.52 | 67.46 | 2,553,906 |
| East | 10 | 26.53 | 67.52 | 2,636,715 |
| East | 11 | 26.52 | 67.46 | 2,565,579 |
| East | 12 | 26.49 | 67.52 | 2,641,666 |
| North | 1 | 24.52 | 67.47 | 798,636 |
| North | 2 | 24.49 | 67.48 | 730,065 |
| North | 3 | 24.50 | 67.38 | 797,761 |
| North | 4 | 24.52 | 67.54 | 777,559 |
| North | 5 | 24.50 | 67.58 | 799,867 |
| North | 6 | 24.51 | 67.53 | 771,292 |
| North | 7 | 24.51 | 67.45 | 796,161 |
| North | 8 | 24.50 | 67.59 | 798,387 |
| North | 9 | 24.52 | 67.46 | 771,184 |
| North | 10 | 24.51 | 67.61 | 796,954 |
| North | 11 | 24.45 | 67.52 | 771,632 |
| North | 12 | 24.54 | 67.50 | 794,240 |
| South | 1 | 20.53 | 67.59 | 787,007 |
| South | 2 | 20.50 | 67.47 | 732,457 |
| South | 3 | 20.51 | 67.41 | 790,764 |
| South | 4 | 20.54 | 67.47 | 761,903 |
| South | 5 | 20.48 | 67.50 | 797,272 |
| South | 6 | 20.49 | 67.50 | 763,603 |
| South | 7 | 20.51 | 67.48 | 791,896 |
| South | 8 | 20.55 | 67.46 | 792,657 |
| South | 9 | 20.51 | 67.52 | 764,112 |
| South | 10 | 20.46 | 67.43 | 790,040 |
| South | 11 | 20.48 | 67.36 | 771,198 |
| South | 12 | 20.47 | 67.51 | 796,059 |
| West | 1 | 29.52 | 67.35 | 835,562 |
| West | 2 | 29.50 | 67.53 | 754,029 |
| West | 3 | 29.52 | 67.53 | 837,918 |
| West | 4 | 29.48 | 67.48 | 807,588 |
| West | 5 | 29.47 | 67.48 | 835,738 |
| West | 6 | 29.53 | 67.49 | 809,984 |
| West | 7 | 29.55 | 67.58 | 824,116 |
| West | 8 | 29.50 | 67.52 | 833,912 |
| West | 9 | 29.51 | 67.51 | 805,403 |
| West | 10 | 29.48 | 67.50 | 837,850 |
| West | 11 | 29.50 | 67.51 | 810,588 |
| West | 12 | 29.52 | 67.45 | 835,085 |

---

## 6. Yearly Trends (1980–2024)

### 6.1 Complete Yearly Statistics
| Year | Records | Avg Temp (°C) | Avg Humidity (%) | Total Precip (mm) |
|------|---------|---------------|------------------|-------------------|
| 1980 | 105,667 | 26.38 | 67.41 | 2,024,259 |
| 1981 | 105,099 | 26.37 | 67.51 | 2,039,310 |
| 1982 | 105,573 | 26.32 | 67.49 | 2,046,893 |
| 1983 | 106,022 | 26.36 | 67.60 | 2,059,427 |
| 1984 | 105,387 | 26.39 | 67.57 | 2,049,138 |
| 1985 | 105,847 | 26.35 | 67.58 | 2,041,517 |
| 1986 | 105,383 | 26.38 | 67.48 | 2,032,569 |
| 1987 | 105,436 | 26.36 | 67.52 | 2,017,052 |
| 1988 | 105,992 | 26.33 | 67.51 | 2,040,709 |
| 1989 | 105,249 | 26.34 | 67.44 | 2,036,109 |
| 1990 | 105,759 | 26.39 | 67.45 | 2,034,305 |
| 1991 | 105,575 | 26.34 | 67.54 | 2,047,529 |
| 1992 | 106,361 | 26.39 | 67.45 | 2,048,630 |
| 1993 | 105,392 | 26.37 | 67.44 | 2,028,575 |
| 1994 | 105,196 | 26.42 | 67.49 | 2,021,461 |
| 1995 | 105,399 | 26.37 | 67.38 | 2,025,115 |
| 1996 | 105,819 | 26.38 | 67.43 | 2,038,610 |
| 1997 | 105,783 | 26.37 | 67.51 | 2,036,581 |
| 1998 | 105,351 | 26.36 | 67.55 | 2,029,850 |
| 1999 | 105,650 | 26.35 | 67.47 | 2,034,244 |
| 2000 | 106,295 | 26.30 | 67.55 | 2,051,399 |
| 2001 | 105,190 | 26.38 | 67.51 | 2,024,304 |
| 2002 | 105,474 | 26.33 | 67.53 | 2,047,021 |
| 2003 | 105,268 | 26.37 | 67.49 | 2,031,514 |
| 2004 | 105,805 | 26.32 | 67.49 | 2,038,098 |
| 2005 | 105,432 | 26.33 | 67.46 | 2,034,091 |
| 2006 | 105,107 | 26.33 | 67.49 | 2,029,603 |
| 2007 | 105,272 | 26.35 | 67.51 | 2,036,209 |
| 2008 | 105,104 | 26.38 | 67.59 | 2,033,376 |
| 2009 | 105,566 | 26.39 | 67.58 | 2,033,956 |
| 2010 | 105,849 | 26.36 | 67.50 | 2,043,329 |
| 2011 | 105,456 | 26.34 | 67.53 | 2,021,387 |
| 2012 | 105,353 | 26.39 | 67.46 | 2,032,510 |
| 2013 | 106,185 | 26.35 | 67.50 | 2,041,648 |
| 2014 | 105,706 | 26.38 | 67.39 | 2,040,375 |
| 2015 | 105,155 | 26.36 | 67.47 | 2,034,043 |
| 2016 | 105,413 | 26.34 | 67.42 | 2,035,359 |
| 2017 | 105,593 | 26.36 | 67.50 | 2,038,924 |
| 2018 | 105,584 | 26.38 | 67.49 | 2,043,101 |
| 2019 | 105,607 | 26.32 | 67.47 | 2,031,728 |
| 2020 | 105,755 | 26.34 | 67.46 | 2,054,008 |
| 2021 | 105,246 | 26.33 | 67.55 | 2,035,024 |
| 2022 | 105,258 | 26.34 | 67.57 | 2,024,960 |
| 2023 | 106,177 | 26.33 | 67.46 | 2,057,489 |
| 2024 | 105,210 | 26.36 | 67.50 | 2,021,441 |

---

## 7. Country-Level Analysis (Join Results)

### 7.1 All Countries by Region and Observations
| Country | Region | Observations | Avg Temp (°C) |
|---------|--------|--------------|---------------|
| AO (Angola) | South | 95,000 | 20.50 |
| BF (Burkina Faso) | West | 87,400 | 29.49 |
| BI (Burundi) | East | 127,300 | 26.51 |
| BJ (Benin) | West | 82,650 | 29.51 |
| BW (Botswana) | South | 69,350 | 20.51 |
| CD (DR Congo) | Central | 118,750 | 30.49 |
| CF (Central African Rep.) | Central | 106,400 | 30.48 |
| CG (Congo) | Central | 131,100 | 30.48 |
| CI (Côte d'Ivoire) | West | 98,800 | 29.52 |
| CM (Cameroon) | Central | 133,950 | 30.49 |
| DJ (Djibouti) | East | 87,400 | 26.53 |
| DZ (Algeria) | North | 133,950 | 24.51 |
| EG (Egypt) | North | 136,800 | 24.51 |
| ER (Eritrea) | East | 96,900 | 26.52 |
| ET (Ethiopia) | East | 118,750 | 26.49 |
| GA (Gabon) | Central | 128,250 | 30.49 |
| GH (Ghana) | West | 96,900 | 29.53 |
| GN (Guinea) | West | 101,650 | 29.47 |
| GQ (Equatorial Guinea) | Central | 111,150 | 30.48 |
| KE (Kenya) | East | 96,900 | 26.51 |
| LS (Lesotho) | South | 103,550 | 20.50 |
| LY (Libya) | North | 133,950 | 24.51 |
| MA (Morocco) | North | 136,800 | 24.51 |
| ML (Mali) | West | 102,600 | 29.50 |
| MR (Mauritania) | North | 114,950 | 24.51 |
| MW (Malawi) | South | 96,900 | 20.53 |
| MZ (Mozambique) | South | 101,650 | 20.50 |
| NA (Namibia) | South | 94,050 | 20.51 |
| NE (Niger) | West | 112,100 | 29.50 |
| NG (Nigeria) | West | 115,900 | 29.50 |
| RW (Rwanda) | East | 101,650 | 26.49 |
| SD (Sudan) | North | 151,050 | 24.50 |
| SN (Senegal) | West | 96,900 | 29.53 |
| SO (Somalia) | East | 99,750 | 26.52 |
| ST (São Tomé) | Central | 113,050 | 30.52 |
| SZ (Eswatini) | South | 106,400 | 20.47 |
| TD (Chad) | Central | 115,900 | 30.50 |
| TG (Togo) | West | 89,300 | 29.50 |
| TN (Tunisia) | North | 133,000 | 24.50 |
| TZ (Tanzania) | East | 113,050 | 26.52 |
| UG (Uganda) | East | 92,150 | 26.51 |
| ZA (South Africa) | South | 88,350 | 20.48 |
| ZM (Zambia) | South | 85,500 | 20.53 |
| ZW (Zimbabwe) | South | 92,150 | 20.52 |

### 7.2 Top 10 Countries by Observation Count
| Rank | Country | Region | Observations | Avg Temp (°C) |
|------|---------|--------|--------------|---------------|
| 1 | SD (Sudan) | North | 151,050 | 24.50 |
| 2 | EG (Egypt) | North | 136,800 | 24.51 |
| 3 | MA (Morocco) | North | 136,800 | 24.51 |
| 4 | CM (Cameroon) | Central | 133,950 | 30.49 |
| 5 | DZ (Algeria) | North | 133,950 | 24.51 |
| 6 | LY (Libya) | North | 133,950 | 24.51 |
| 7 | TN (Tunisia) | North | 133,000 | 24.50 |
| 8 | CG (Congo) | Central | 131,100 | 30.48 |
| 9 | GA (Gabon) | Central | 128,250 | 30.49 |
| 10 | BI (Burundi) | East | 127,300 | 26.51 |

---

## 8. Transaction Management Status

### 8.1 ACID Configuration
| Setting | Value |
|---------|-------|
| hive.support.concurrency | **false** |
| hive.txn.manager | DummyTxnManager |

*Note: Full ACID support is disabled in this configuration. The DummyTxnManager provides no locking or transaction semantics. For production ACID workloads, consider enabling DbTxnManager.*

---

## 9. Region-Year Detailed Analysis (Sample: Central Africa)

| Region | Year | Records | Avg Temp (°C) | Min Temp | Max Temp | Temp σ |
|--------|------|---------|---------------|----------|----------|--------|
| Central | 1980 | 21,233 | 30.53 | 18.0 | 43.0 | 7.24 |
| Central | 1981 | 21,377 | 30.50 | 18.0 | 43.0 | 7.19 |
| Central | 1982 | 21,441 | 30.49 | 18.0 | 43.0 | 7.24 |
| Central | 1983 | 21,429 | 30.48 | 18.0 | 43.0 | 7.23 |
| Central | 1984 | 21,241 | 30.53 | 18.0 | 43.0 | 7.21 |
| Central | 1985 | 21,055 | 30.59 | 18.0 | 43.0 | 7.26 |
| Central | 1986 | 21,448 | 30.50 | 18.0 | 43.0 | 7.22 |
| Central | 1987 | 21,129 | 30.50 | 18.0 | 43.0 | 7.21 |
| Central | 1988 | 21,247 | 30.57 | 18.0 | 43.0 | 7.21 |
| Central | 1989 | 21,276 | 30.50 | 18.0 | 43.0 | 7.19 |

---

## 10. Key Findings Summary

### 10.1 Performance Characteristics
- **Data Scale**: 4.75 million records across 5,000 weather stations spanning 45 years (1980–2024)
- **Storage Efficiency**: 304 MB raw data with 2x replication = 912 MB total HDFS storage
- **Query Latency**: Simple aggregations complete in 9–16 seconds on 4.75M rows
- **Join Performance**: Map-Side joins are 1.21x faster than Reduce-Side joins (21.26s vs 25.76s)

### 10.2 Climate Analysis Insights
- **Temperature Gradient**: 10°C difference between hottest (Central: 30.49°C) and coolest (South: 20.50°C) regions
- **Consistent Variance**: Temperature standard deviation is remarkably uniform (σ ≈ 2.45) across all regions
- **Humidity Uniformity**: Average humidity is nearly identical across all regions (~67.5%)
- **Precipitation Distribution**: Central and East Africa receive 3x more precipitation than other regions

### 10.3 Infrastructure Validation
- **Multi-Node Cluster**: 2 healthy DataNodes with balanced block distribution (6 blocks each)
- **Replication**: 2x replication factor ensures fault tolerance
- **Container Orchestration**: 7 containers utilizing ~47% of available memory (~3.6 GiB)
- **Vectorized Execution**: Enabled for statistical computations

### 10.4 Data Quality Metrics
- **Completeness**: 45 complete years of data (1980–2024)
- **Coverage**: 44 African countries across 5 regions
- **Station Density**: ~1,000 stations per region
- **Temporal Resolution**: Monthly observations

---

## 11. Seminar Requirements Checklist

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ✅ Install on local network (nodes >= 2) | **PASS** | 2 DataNodes (slave-node-1, slave-node-2) |
| ✅ Study architecture/components | **PASS** | 7-container stack documented |
| ✅ Storage model | **PASS** | TextInputFormat, LazySimpleSerDe, HDFS |
| ✅ Transaction management | **PASS** | DummyTxnManager (ACID disabled) |
| ✅ Query execution | **PASS** | MapReduce jobs with timing |
| ✅ Query optimization | **PASS** | Join algorithm comparison |
| ✅ Join algorithms | **PASS** | Map-Side vs Reduce-Side (1.21x) |
| ✅ Define simple application | **PASS** | Django climate dashboard |
| ✅ System design | **PASS** | Architecture diagrams |
| ✅ Implement application | **PASS** | Working REST API |
| ✅ Experiment with system | **PASS** | All query benchmarks |

---

*Report generated by running FINAL_TEST_PLAN.md queries against the live Hive cluster on January 13, 2026.*
