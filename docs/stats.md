         ▄                                                                                                                                           
     ▄ ▄ ▄  ▀▄▀                                                                                                                                      
   ▄ ▄ ▄ ▄ ▄▇▀  █▀▄ █▀█ █▀▀ █▄▀ █▀▀ █▀█                                                                                                              
  ▀████████▀    █▄▀ █▄█ █▄▄ █ █ ██▄ █▀▄                                                                                                              
   ▀█████▀                        DEBUG                                                                                                              
                                                                                                                                                     
Builtin commands:                                                                                                                                    
- install [tool1] [tool2] ...    Add Nix packages from: https://search.nixos.org/packages                                                            
- uninstall [tool1] [tool2] ...  Uninstall NixOS package(s).                                                                                         
- entrypoint                     Print/lint/run the entrypoint.                                                                                      
- builtins                       Show builtin commands.                                                                                              
                                                                                                                                                     
Checks:                                                                                                                                              
✓ distro:            Debian GNU/Linux 8 (jessie)                                                                                                     
✓ entrypoint linter: no errors (run 'entrypoint' for details)                                                                                        
                                                                                                                                                     
This is an attach shell, i.e.:                                                                                                                       
- Any changes to the container filesystem are visible to the container directly.                                                                     
- The /nix directory is invisible to the actual container.                                                                                           
                                                                                                                                      Version: 0.0.45
root@ef0cd96e0979 /opt [hive-server]
docker > ls
hadoop-2.7.4  hive
root@ef0cd96e0979 /opt [hive-server]
docker > hive
which: no hbase in (/nix/forwarding/bin:/nix/var/nix/profiles/default/bin:/nix/var/nix/profiles/default/sbin:/opt/hive/bin:/opt/hadoop-2.7.4/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin)
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.6.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop-2.7.4/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive> show databases;
OK
default
mbv_africa
Time taken: 1.364 seconds, Fetched: 2 row(s)
hive> exit()
    > q()
    > ^C#                                                                                                                                            
root@ef0cd96e0979 /opt [hive-server]
docker > beeline
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.6.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop-2.7.4/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]
Beeline version 2.3.2 by Apache Hive
beeline> show databases;
No current connection
beeline> #                                                                                                                                           
root@ef0cd96e0979 /opt [hive-server]
docker > hive
which: no hbase in (/nix/forwarding/bin:/nix/var/nix/profiles/default/bin:/nix/var/nix/profiles/default/sbin:/opt/hive/bin:/opt/hadoop-2.7.4/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin)
SLF4J: Class path contains multiple SLF4J bindings.
SLF4J: Found binding in [jar:file:/opt/hive/lib/log4j-slf4j-impl-2.6.2.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: Found binding in [jar:file:/opt/hadoop-2.7.4/share/hadoop/common/lib/slf4j-log4j12-1.7.10.jar!/org/slf4j/impl/StaticLoggerBinder.class]
SLF4J: See http://www.slf4j.org/codes.html#multiple_bindings for an explanation.
SLF4J: Actual binding is of type [org.apache.logging.slf4j.Log4jLoggerFactory]

Logging initialized using configuration in file:/opt/hive/conf/hive-log4j2.properties Async: true
Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
hive> show databases;
OK
default
mbv_africa
Time taken: 1.387 seconds, Fetched: 2 row(s)
hive> USE mbv_africa;
OK
Time taken: 0.136 seconds
hive> DESCRIBE FORMATTED portfolio_observations;
OK
# col_name            data_type           comment             
  
station_id          string                                  
observation_date    string                                  
year                int                                     
month               int                                     
temp_max            float                                   
temp_min            float                                   
temp_mean           float                                   
precipitation       float                                   
humidity            float                                   
sea_surface_temp    float                                   
ocean_salinity      float                                   
region              string                                  
  
# Detailed Table Information  
Database:           mbv_africa           
Owner:              root                 
CreateTime:         Fri Jan 02 17:46:57 UTC 2026 
LastAccessTime:     UNKNOWN              
Retention:          0                    
Location:           hdfs://master-node:9000/user/hive/warehouse/mbv_africa.db/portfolio_observations 
Table Type:         MANAGED_TABLE        
Table Parameters:  
numFiles            1                   
numRows             0                   
rawDataSize         0                   
skip.header.line.count1                   
totalSize           62835853            
transient_lastDdlTime1767376037          
  
# Storage Information  
SerDe Library:      org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe 
InputFormat:        org.apache.hadoop.mapred.TextInputFormat 
OutputFormat:       org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat 
Compressed:         No                   
Num Buckets:        -1                   
Bucket Columns:     []                   
Sort Columns:       []                   
Storage Desc Params:  
field.delim         ,                   
serialization.format,                   
Time taken: 0.309 seconds, Fetched: 42 row(s)
hive> ANALYZE TABLE portfolio_observations COMPUTE STATISTICS;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
Query ID = root_20260102184634_593c33a9-5d31-4a86-8c32-d16059f30180
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks is set to 0 since there's no reduce operator
Job running in-process (local Hadoop)
2026-01-02 18:46:38,508 Stage-0 map = 0%,  reduce = 0%
2026-01-02 18:46:39,540 Stage-0 map = 100%,  reduce = 0%
Ended Job = job_local802138552_0001
MapReduce Jobs Launched: 
Stage-Stage-0:  HDFS Read: 62835853 HDFS Write: 99 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
Time taken: 6.065 seconds
hive> 