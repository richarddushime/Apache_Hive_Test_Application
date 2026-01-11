            Statistics: Num rows: 1 Data size: 8 Basic stats: COMPLETE Column stats: NONE
            table:
                input format: org.apache.hadoop.mapred.SequenceFileInputFormat
                output format: org.apache.hadoop.hive.ql.io.HiveSequenceFileOutputFormat
                serde: org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe

  Stage: Stage-0
    Fetch Operator
      limit: -1
      Processor Tree:
        ListSink

Time taken: 0.646 seconds, Fetched: 45 row(s)
hive> EXPLAIN 
    > SELECT COUNT(*) 
    > FROM portfolio_observations 
    > 
    > 
    > 
    > EXPLAIN 
    > SELECT region, month, AVG(temp_mean), SUM(precipitation)
    > FROM portfolio_observations
    > GROUP BY region, month
    > ORDER BY region, month;
FAILED: ParseException line 8:0 missing EOF at 'SELECT' near 'EXPLAIN'
hive> SELECT region, month, AVG(temp_mean), SUM(precipitation)
    > FROM portfolio_observations
    > GROUP BY region, month
    > ORDER BY region, month;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
Query ID = root_20260111215212_91447eac-9eac-42e2-bdfd-e6fc9120a18a
Total jobs = 2
Launching Job 1 out of 2
Number of reduce tasks not specified. Estimated from input data size: 2
In order to change the average load for a reducer (in bytes):
  set hive.exec.reducers.bytes.per.reducer=<number>
In order to limit the maximum number of reducers:
  set hive.exec.reducers.max=<number>
In order to set a constant number of reducers:
  set mapreduce.job.reduces=<number>
Job running in-process (local Hadoop)
2026-01-11 21:52:15,175 Stage-1 map = 0%,  reduce = 0%
2026-01-11 21:52:20,307 Stage-1 map = 100%,  reduce = 0%
2026-01-11 21:52:21,365 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_local231198576_0008
Launching Job 2 out of 2
Number of reduce tasks determined at compile time: 1
In order to change the average load for a reducer (in bytes):
  set hive.exec.reducers.bytes.per.reducer=<number>
In order to limit the maximum number of reducers:
  set hive.exec.reducers.max=<number>
In order to set a constant number of reducers:
  set mapreduce.job.reduces=<number>
Job running in-process (local Hadoop)
2026-01-11 21:52:23,279 Stage-2 map = 100%,  reduce = 100%
Ended Job = job_local1665478539_0009
MapReduce Jobs Launched: 
Stage-Stage-1:  HDFS Read: 7619531821 HDFS Write: 800 SUCCESS
Stage-Stage-2:  HDFS Read: 3835044336 HDFS Write: 400 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
Central130.5218594847047022701818.099501148
Central230.4877597698263222484386.399545692
Central330.484309299442072717772.700014353
Central430.527928838437192624077.8999829814
Central530.4990802335804472714896.0000113994
Central630.4942991532600022614356.799951814
Central730.4719834295169752708747.6999802515
Central830.4424522841496032713065.999947086
Central930.4778572355066862637231.0000624508
Central1030.504330884089592729157.700087033
Central1130.487284678157412606947.6002441123
Central1230.4983159174173762708866.9998030663
East126.4855736008157872656809.400027089
East226.521693129641642423296.499951318
East326.5259125241564362650727.500295013
East426.5260909397064962544999.899667807
East526.5214606405759282643870.199975379
East626.5290190291762152540992.90031226
East726.465479512243412633155.500029102
East826.4945896367556522623252.200071603
East926.516784328443722553906.3998027667
East1026.534565145778252636715.200159639
East1126.5201118409955332565579.4007416964
East1226.4884293875347332641665.6003707945
North124.51509962152431798636.2000044733
North224.49210862565441730065.2000094056
North324.502889906257153797761.0999489203
North424.524911227524193777559.3000724837
North524.501355414136263799866.9000971094
North624.505969719898687771292.3000116497
North724.51422322958152796160.8999468163
North824.496313316420203798387.300045982
North924.51942749868348771183.6999426261
North1024.511978329031198796954.200181663
North1124.45116065486446771631.599781774
North1224.544954622841257794240.2998407185
South120.532178250148828787007.1000847593
South220.50030688086158732456.7001374438
South320.508886189941187790764.4998875037
South420.544551078193415761903.1001228839
South520.47648157821212797271.8001711369
South620.485748269312595763602.8002239093
South720.507139773145138791896.300163053
South820.551875808922798792657.2999979705
South920.50847239232773764111.5001370683
South1020.46255345301472790040.4998904467
South1120.483752553654618771198.4001446292
South1220.472469087945896796059.2999611795
West129.516748111908036835562.0000504181
West229.499405113426416754028.7000755519
West329.51837600579687837918.499950558
West429.48433865958065807588.2999580279
West529.472599842601046835738.4999792129
West629.533860849905643809983.7000084668
West729.54647899544555824115.6000789031
West829.4963114342346833911.7002391964
West929.50733682982904805403.4000506178
West1029.47512459167695837849.7000440136
West1129.49686024595985810588.1001109481
West1229.515099857930938835084.9000449628
Time taken: 10.715 seconds, Fetched: 60 row(s)
hive> SELECT 
    >     s.country, 
    >     o.year, 
    >     AVG(o.sea_surface_temp) as avg_sst
    > FROM portfolio_observations o
    > JOIN portfolio_stations s ON o.station_id = s.station_id
    > WHERE s.is_active = true
    > GROUP BY s.country, o.year;
FAILED: SemanticException [Error 10002]: Line 7:8 Invalid column reference 'is_active'
hive> SELECT 
    >     s.country, 
    >     o.year, 
    >     AVG(o.sea_surface_temp) as avg_sst
    > FROM portfolio_observations o
    > JOIN portfolio_stations s ON o.station_id = s.station_id
    > WHERE s.is_active = true
    > GROUP BY s.country, o.year;
FAILED: SemanticException [Error 10002]: Line 7:8 Invalid column reference 'is_active'
hive> SET hive.auto.convert.join=true;
hive> SELECT 
    >     s.country, 
    >     o.year, 
    >     AVG(o.sea_surface_temp) as avg_sst
    > FROM portfolio_observations o
    > JOIN portfolio_stations s ON o.station_id = s.station_id
    > WHERE s.is_active = true
    > GROUP BY s.country, o.year;
FAILED: SemanticException [Error 10002]: Line 7:8 Invalid column reference 'is_active'
hive> SET hive.vectorized.execution.enabled = true;
hive> SET hive.vectorized.execution.reduce.enabled = true;
hive> SELECT 
    >     region,
    >     STDDEV_POP(temp_max - temp_min) as temp_variance,
    >     CORR(humidity, precipitation) as moisture_correlation
    > FROM portfolio_observations
    > GROUP BY region;
WARNING: Hive-on-MR is deprecated in Hive 2 and may not be available in the future versions. Consider using a different execution engine (i.e. spark, tez) or using Hive 1.X releases.
Query ID = root_20260111215417_63aed36d-27ce-48a5-880b-2bab294696e5
Total jobs = 1
Launching Job 1 out of 1
Number of reduce tasks not specified. Estimated from input data size: 2
In order to change the average load for a reducer (in bytes):
  set hive.exec.reducers.bytes.per.reducer=<number>
In order to limit the maximum number of reducers:
  set hive.exec.reducers.max=<number>
In order to set a constant number of reducers:
  set mapreduce.job.reduces=<number>
Job running in-process (local Hadoop)
2026-01-11 21:54:21,243 Stage-1 map = 0%,  reduce = 0%
2026-01-11 21:54:32,607 Stage-1 map = 17%,  reduce = 0%
2026-01-11 21:54:38,824 Stage-1 map = 100%,  reduce = 0%
2026-01-11 21:54:42,946 Stage-1 map = 100%,  reduce = 100%
Ended Job = job_local267613870_0010
MapReduce Jobs Launched: 
Stage-Stage-1:  HDFS Read: 8895533817 HDFS Write: 800 SUCCESS
Total MapReduce CPU Time Spent: 0 msec
OK
Central2.4477876341746326.982609690562719E-4
East2.4477432438417464-0.0020415585721984776
North2.449550480539478-4.5659051489623566E-4
South2.4483209258259437.544897429723668E-4
West2.4482114666570127-5.891513884874755E-4
Time taken: 25.673 seconds, Fetched: 5 row(s)
hive> SELECT 
    >     c.region,
    >     c.date,
    >     c.rainfall,
    >     o.salinity
    > FROM mbv_africa.climate_data c
    > JOIN mbv_africa.ocean_data o ON (c.date = o.date AND c.region = o.region)
    > WHERE c.rainfall > 100 AND o.salinity < 33
    > ORDER BY c.rainfall DESC;
NoViableAltException(80@[80:1: selectItem : ( ( tableAllColumns )=> tableAllColumns -> ^( TOK_SELEXPR tableAllColumns ) | ( expression ( ( ( KW_AS )? identifier ) | ( KW_AS LPAREN identifier ( COMMA identifier )* RPAREN ) )? ) -> ^( TOK_SELEXPR expression ( identifier )* ) );])
at org.apache.hadoop.hive.ql.parse.HiveParser_SelectClauseParser$DFA13.specialStateTransition(HiveParser_SelectClauseParser.java:4624)
at org.antlr.runtime.DFA.predict(DFA.java:80)
at org.apache.hadoop.hive.ql.parse.HiveParser_SelectClauseParser.selectItem(HiveParser_SelectClauseParser.java:1615)
at org.apache.hadoop.hive.ql.parse.HiveParser_SelectClauseParser.selectList(HiveParser_SelectClauseParser.java:1176)
at org.apache.hadoop.hive.ql.parse.HiveParser_SelectClauseParser.selectClause(HiveParser_SelectClauseParser.java:950)
at org.apache.hadoop.hive.ql.parse.HiveParser.selectClause(HiveParser.java:42096)
at org.apache.hadoop.hive.ql.parse.HiveParser.atomSelectStatement(HiveParser.java:36720)
at org.apache.hadoop.hive.ql.parse.HiveParser.selectStatement(HiveParser.java:36987)
at org.apache.hadoop.hive.ql.parse.HiveParser.regularBody(HiveParser.java:36633)
at org.apache.hadoop.hive.ql.parse.HiveParser.queryStatementExpressionBody(HiveParser.java:35822)
at org.apache.hadoop.hive.ql.parse.HiveParser.queryStatementExpression(HiveParser.java:35710)
at org.apache.hadoop.hive.ql.parse.HiveParser.execStatement(HiveParser.java:2284)
at org.apache.hadoop.hive.ql.parse.HiveParser.statement(HiveParser.java:1333)
at org.apache.hadoop.hive.ql.parse.ParseDriver.parse(ParseDriver.java:208)
at org.apache.hadoop.hive.ql.parse.ParseUtils.parse(ParseUtils.java:77)
at org.apache.hadoop.hive.ql.parse.ParseUtils.parse(ParseUtils.java:70)
at org.apache.hadoop.hive.ql.Driver.compile(Driver.java:468)
at org.apache.hadoop.hive.ql.Driver.compileInternal(Driver.java:1317)
at org.apache.hadoop.hive.ql.Driver.runInternal(Driver.java:1457)
at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1237)
at org.apache.hadoop.hive.ql.Driver.run(Driver.java:1227)
at org.apache.hadoop.hive.cli.CliDriver.processLocalCmd(CliDriver.java:233)
at org.apache.hadoop.hive.cli.CliDriver.processCmd(CliDriver.java:184)
at org.apache.hadoop.hive.cli.CliDriver.processLine(CliDriver.java:403)
at org.apache.hadoop.hive.cli.CliDriver.executeDriver(CliDriver.java:821)
at org.apache.hadoop.hive.cli.CliDriver.run(CliDriver.java:759)
at org.apache.hadoop.hive.cli.CliDriver.main(CliDriver.java:686)
at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
at sun.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:62)
at sun.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
at java.lang.reflect.Method.invoke(Method.java:498)
at org.apache.hadoop.util.RunJar.run(RunJar.java:221)
at org.apache.hadoop.util.RunJar.main(RunJar.java:136)
FAILED: ParseException line 3:6 cannot recognize input near 'c' '.' 'date' in selection target
hive> SHOW LOCKS;
FAILED: Execution Error, return code 1 from org.apache.hadoop.hive.ql.exec.DDLTask. show Locks LockManager not specified
hive> 