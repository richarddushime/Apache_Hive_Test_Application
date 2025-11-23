Noaa datasets 


Climate Data Projects with Apache Hive
1. Global Surface Climate Data – Trend Analysis & Forecasting

Summary: Use large-scale historical weather station data to analyze climate trends and forecast variables like temperature or precipitation. For example, NOAA’s datasets provide over 100,000 stations worldwide (GHCN-Daily)
ncei.noaa.gov
 or ~14,000 active stations (ISD)
registry.opendata.aws
 with records going back over a century. One can load these into Hive to compute long-term trends (e.g. warming rates), seasonal patterns, and anomalies. The pipeline involves ingesting raw ASCII or fixed-width files into Hive tables, cleaning (QA/QC flags), and computing aggregates (daily→monthly→annual summaries). This project tests Hive’s ability to handle very large structured data (~hundreds of GB), and the resulting data feeds a model for forecasting or anomaly detection in climate.

Datasets (public links): NOAA GHCN-Daily or ISD. For example, the Integrated Surface Database (ISD) contains hourly global weather observations (~600 GB uncompressed)
registry.opendata.aws
. GHCN-Daily offers daily max/min temperature and precipitation from >100,000 stations
ncei.noaa.gov
. (Data can be downloaded via NOAA/FTP in bulk or API.)

Hive ETL Tasks: Define a table schema (e.g. StationID, Date, TempMax, TempMin, Precip, …). Partition the table by year (and possibly by country/region or station). Store in a columnar format like ORC or Parquet with compression to speed queries. Transform raw data by parsing fixed-width formats, filtering invalid values, and joining station metadata (latitude/longitude). Compute derived fields (e.g. monthly mean temperature) using Hive SQL. Techniques: bucket by station ID for faster joins, use vectorized ORC reads and predicate pushdown, create indexes or use Hive’s cost-based optimizer. Optimize performance by tuning memory (hive.exec.reducers), enabling dynamic partitioning, and using column statistics.

ML Model & Use Case: Develop a forecasting model (e.g. time-series regression like ARIMA or LSTM, or gradient-boosted trees on features) to predict future temperature/precipitation trends, or a classification model to flag extreme events (anomaly detection). For example, predict next-season temperature anomalies or classify months as “heatwave” vs normal.

Evaluation Metrics: For forecasting: RMSE or MAE on predicted vs actual temperature. For classification: accuracy, precision/recall, or ROC AUC if detecting extreme events. Compare against climatological baselines.

Portfolio Value: Demonstrates end-to-end big-data engineering on a massive, real-world climate dataset. Highlights Hive skills (schema design, partitioning, ORC usage) and ML integration. Climate trend forecasting is highly relevant for climate change studies and environmental planning. The project shows ability to handle messy raw data at scale and build models for scientifically important targets.

2. Country-Level CO₂ Emissions – Analysis & Forecasting

Summary: Analyze and model national greenhouse gas emissions to study climate change drivers. Use global CO₂/GHG inventories by country (structured time-series). For instance, the Global Carbon Project provides a country-year CO₂ emissions dataset (1970–2024)
zenodo.org
, and the EDGAR database offers GHG emission series for all countries (1970–2023)
edgar.jrc.ec.europa.eu
. In Hive, one can load emissions tables, join with socio-economic data (e.g. GDP, population), and derive trends or per-capita measures. The goal is to build a predictive model of future emissions or to classify countries by compliance with targets.

Datasets (public links): The Global Carbon Project (Zenodo) offers a “fossil CO₂ emissions” CSV by country
zenodo.org
. The Emissions Database for Global Atmospheric Research (EDGAR) provides historical GHG totals by country
edgar.jrc.ec.europa.eu
. These are usually available as CSV or TSV files on official sites.

Hive ETL Tasks: Define a table schema such as CountryCode, Year, CO2_Emissions, CH4_Emissions, etc.. Partition by year (and/or country group) to improve query pruning. Use Parquet/ORC format for compression and fast analytics. Transformations include cleaning country names/codes to standard ISO format, computing per-capita emissions (join with population data), and aggregating by region. Performance techniques: use bucketing on country code if joining multiple tables (e.g. GDP), enable cost-based optimizer, and use vectorized ORC scanning with Z-order clustering on time to speed range queries.

ML Model & Use Case: Build a forecasting model (e.g. time-series models like Prophet or LSTM) to predict next-year emissions per country or by sector, or a regression model to estimate emissions based on GDP/population. Alternatively, a classification model could label countries as “on-track” or “off-track” for emission targets based on historical trends.

Evaluation Metrics: For forecasting: RMSE, MAE, or MAPE against held-out years of emissions data. For classification: accuracy/F1 on held-out labels (target attainment). Use cross-validation over time or countries.

Portfolio Value: This showcases Hive for policy-relevant data engineering (massive country-year tables). It includes joins, aggregations, and large-scale ETL – exactly what employers want. Modeling emissions ties directly to climate policy and sustainability work. The project combines socio-economic and climate data, making it interdisciplinary and impactful.

3. Sea Surface Temperature (SST) – Anomaly Detection & ENSO Prediction

