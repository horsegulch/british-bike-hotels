
##  Test 1

This table summarizes the metrics extracted from the test GPX files and the resulting difficulty score calculated by the algorithm.

|                            |                   |              |         |             |             |             |                      |
| -------------------------- | ----------------- | ------------ | ------- | ----------- | ----------- | ----------- | -------------------- |
| **GPX Filename**           | **Distance (km)** | **TEGa (m)** | **PDD** | **MCg (%)** | **ACg (%)** | **ADg (%)** | **Difficulty Score** |
| Dales_Climbers_Classic.gpx | 195.17            | 3504.44      | 0.502   | 26.78       | 6.86        | 5.87        | **292.64**           |
| Easy Coastal.gpx           | 25.07             | 98.70        | 0.526   | 5.26        | 0.00        | 0.00        | **8.34**             |
| Medium Hills.gpx           | 45.71             | 436.70       | 0.484   | 20.28       | 6.16        | 4.53        | **18.86**            |
| Hard Surrey.gpx            | 83.83             | 1051.31      | 0.518   | 22.65       | 5.43        | 4.61        | **50.53**            |
| Easy Long.gpx              | 64.65             | 218.90       | 0.526   | 5.76        | 0.00        | 4.34        | **26.83**            |
| The Rider.gpx              | 139.10            | 3724.74      | 0.497   | 39.54       | 7.32        | 6.74        | **153.27**           |

- **TEGa:** Uses the smoothed elevation value (window size 7).
    
- **MCg:** Max gradient over ~100m segments (min distance 50m).
    
- **ACg:** Avg gradient of "Significant Climbs" (>=250m, >=3%, factor >=3500).
    
- **ADg:** Avg gradient of "Significant Descents" (>=500m, <=-3%).
    
- **Difficulty Score:** Uncapped final score.
    
## Test 2

### Changes:

DISTANCE_DIFFICULTY_COEFFICIENT_A - Reduced from 0.005 to 0.004
LINEAR_UF_SLOPE - Increased from 0.7 to 0.75
### GPX Test Results Comparison:

This table compares the final calculated difficulty scores from two separate runs of the script (`gpx_difficulty_v2.py`) on the same set of GPX files. Differences in scores indicate parameter changes between runs.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|
|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|
|Easy Coastal.gpx|8.34|7.74|
|Medium Hills.gpx|18.86|17.04|
|Hard Surrey.gpx|50.53|43.82|
|Easy Long.gpx|26.83|22.70|
|The Rider.gpx|153.27|134.55|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in both runs, only the final difficulty calculation differed due to parameter changes._

## Test 3

### Changes:
DISTANCE_DIFFICULTY_COEFFICIENT_A - Reduced from 0.004 to 0.0035
LINEAR_UF_SLOPE - Increased from 0.75 to 0.8

### GPX Test Resilts Comparison:

This table compares the final calculated difficulty scores from three separate runs of the script (`gpx_difficulty_v2.py`) on the same set of GPX files. Differences in scores indicate parameter changes between runs.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|
|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|
|Easy Coastal.gpx|8.34|7.74|7.43|
|Medium Hills.gpx|18.86|17.04|15.94|
|Hard Surrey.gpx|50.53|43.82|39.81|
|Easy Long.gpx|26.83|22.70|20.57|
|The Rider.gpx|153.27|134.55|121.82|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

## Test 4

### Changes:
DISTANCE_BASE_ADDITION - Increased from 5.0 to 10.0
Other parameters as per V3

### GPX Test Results Comparison:

This table compares the final calculated difficulty scores from four separate runs of the script (`gpx_difficulty_v2.py`) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|
|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|
|Easy Long.gpx|26.83|22.70|20.57|25.81|
|The Rider.gpx|153.27|134.55|121.82|130.19|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

## Test 5
### Changes:
DISTANCE_BASE_ADDITION - Increased from 10.0 to 15.0
Other paramaters as per V3

### GPX Test Results Comparison:

This table compares the final calculated difficulty scores from five separate runs of the script (`gpx_difficulty_v2.py`) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|
|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`

## Test 6
### Changes:
BASE_ADD reduced from 15 to 10
Dist_COEFF reduced from 0.0035 to 0.003

### GPX Test Results Comparison

This table compares the final calculated difficulty scores from six separate runs of the script (`gpx_difficulty_v2.py`) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|Final Score (Run 6)|
|---|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|206.67|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|12.27|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|21.05|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|41.81|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|23.62|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|113.99|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`

Parameters Used for this Run:
-----------------------------
  Metric Extraction:
    SMOOTHING_WINDOW_SIZE = 7
    MCG_SEGMENT_TARGET_DISTANCE_M = 100.0
    MIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0
    SIG_CLIMB_FACTOR_THRESHOLD = 3500.0
    SIG_CLIMB_MIN_DISTANCE_M = 250.0
    SIG_CLIMB_MIN_GRADIENT_PERCENT = 3.0
    POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD = 1.0
    SIG_DESCENT_MIN_DISTANCE_M = 500.0
    SIG_DESCENT_MIN_GRADIENT_PERCENT = -3.0
    POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD = -1.0
  Difficulty Calculation:
    DISTANCE_BASE_ADDITION = 10.0
    DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.003
    LINEAR_UF_SLOPE = 0.8
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped

## Test 7
### Parameters Used:

 Difficulty Calculation:
    DISTANCE_BASE_ADDITION = 10.0
    DISTANCE_DIFFICULTY_COEFFICIENT_A = ==***0.003 > 0.0035****==
    LINEAR_UF_SLOPE = ==***0.8 > 0.9***==
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from seven separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

| GPX Filename               | Final Score (Run 1) | Final Score (Run 2) | Final Score (Run 3) | Final Score (Run 4) | Final Score (Run 5) | Final Score (Run 6) | Final Score (Run 7) |
| -------------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| Dales_Climbers_Classic.gpx | 292.64              | 255.17              | 230.02              | 238.34              | 246.65              | 206.67              | 250.22              |
| Easy Coastal.gpx           | 8.34                | 7.74                | 7.43                | 12.59               | 17.76               | 12.27               | 12.64               |
| Medium Hills.gpx           | 18.86               | 17.04               | 15.94               | 22.41               | 28.88               | 21.05               | 23.04               |
| Hard Surrey.gpx            | 50.53               | 43.82               | 39.81               | 46.53               | 53.26               | 41.81               | 48.03               |
| Easy Long.gpx              | 26.83               | 22.70               | 20.57               | 25.81               | 31.05               | 23.62               | 25.96               |
| The Rider.gpx              | 153.27              | 134.55              | 121.82              | 130.19              | 138.57              | 113.99              | 136.75              |

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`

## Test 8
### Parameters Used:

 Difficulty Calculation:
    DISTANCE_BASE_ADDITION = ==***10.0 > 9.0***==
    DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.0035
    LINEAR_UF_SLOPE = ==***0.9 > 0.95***==
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from eight separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|Final Score (Run 6)|Final Score (Run 7)|Final Score (Run 8)|
|---|---|---|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|206.67|250.22|254.37|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|12.27|12.64|11.63|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|21.05|23.04|22.01|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|41.81|48.03|47.36|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|23.62|25.96|24.98|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|113.99|136.75|138.23|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
## Test 9
### Parameters Used:

 Difficulty Calculation:
    DISTANCE_BASE_ADDITION = ==***9.0 > 9.5***==
    DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.0035
    LINEAR_UF_SLOPE = ==***0.95 > 0.9***==
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from nine separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

| GPX Filename               | Final Score (Run 1) | Final Score (Run 2) | Final Score (Run 3) | Final Score (Run 4) | ==Final Score (Run 5)== | Final Score (Run 6) | Final Score (Run 7) | Final Score (Run 8) | Final Score (Run 9) |
| -------------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- |
| Dales_Climbers_Classic.gpx | 292.64              | 255.17              | 230.02              | 238.34              | ==246.65==              | 206.67              | 250.22              | 254.37              | 249.34              |
| Easy Coastal.gpx           | 8.34                | 7.74                | 7.43                | 12.59               | ==17.76==               | 12.27               | 12.64               | 11.63               | 12.12               |
| Medium Hills.gpx           | 18.86               | 17.04               | 15.94               | 22.41               | ==28.88==               | 21.05               | 23.04               | 22.01               | 22.38               |
| Hard Surrey.gpx            | 50.53               | 43.82               | 39.81               | 46.53               | ==53.26==               | 41.81               | 48.03               | 47.36               | 47.33               |
| Easy Long.gpx              | 26.83               | 22.70               | 20.57               | 25.81               | ==31.05==               | 23.62               | 25.96               | 24.98               | 25.44               |
| The Rider.gpx              | 153.27              | 134.55              | 121.82              | 130.19              | ==138.57==              | 113.99              | 136.75              | 138.23              | 135.87              |

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
    
- **Run 9 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=9.5`

## Test 10
### Parameters Used:

 Difficulty Calculation:
    DISTANCE_BASE_ADDITION = ==***9.5 > 9.0***==
    DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.0035
    LINEAR_UF_SLOPE = ==***0.9 > 0.975***==
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from ten separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|Final Score (Run 6)|Final Score (Run 7)|Final Score (Run 8)|Final Score (Run 9)|Final Score (Run 10)|
|---|---|---|---|---|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|206.67|250.22|254.37|249.34|257.32|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|12.27|12.64|11.63|12.12|11.64|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|21.05|23.04|22.01|22.38|22.16|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|41.81|48.03|47.36|47.33|47.73|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|23.62|25.96|24.98|25.44|25.01|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|113.99|136.75|138.23|135.87|139.85|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
    
- **Run 9 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=9.5`
    
- **Run 10 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=9`
## Test 11
### Parameters Used:

 Difficulty Calculation:
    DISTANCE_BASE_ADDITION = ==***9.0 > 8.0***==
    DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.0035
    LINEAR_UF_SLOPE = 0.975
    MAX_EXPECTED_TEGA = 3500.0
    MAX_EXPECTED_ACG = 12.0
    MAX_EXPECTED_MCG = 20.0
    WEIGHT_TEGA = 0.5, WEIGHT_ACG = 0.4, WEIGHT_MCG = 0.1
    PDD_THRESHOLD = 0.65
    MAX_ASCENT_FOR_DOWNHILL_REDUCTION = 1000.0
    MIN_AVG_DESCENT_GRADIENT_THRESHOLD = 3.0
    TARGET_ADG_FOR_MAX_REDUCTION = 7.0
    WEIGHT_PDD_SCORE = 0.7, WEIGHT_ADG_SCORE = 0.3
    MAX_DOWNHILL_REDUCTION_FACTOR = 0.8
    MIN_DIFFICULTY_SCORE = 0.0
    Score Capping = Uncapped
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from eleven separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

| GPX Filename               | Final Score (Run 1) | Final Score (Run 2) | Final Score (Run 3) | Final Score (Run 4) | Final Score (Run 5) | Final Score (Run 6) | Final Score (Run 7) | Final Score (Run 8) | Final Score (Run 9) | Final Score (Run 10) | Final Score (Run 11) |
| -------------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | ------------------- | -------------------- | -------------------- |
| Dales_Climbers_Classic.gpx | 292.64              | 255.17              | 230.02              | 238.34              | 246.65              | 206.67              | 250.22              | 254.37              | 249.34              | 257.32               | 255.51               |
| Easy Coastal.gpx           | 8.34                | 7.74                | 7.43                | 12.59               | 17.76               | 12.27               | 12.64               | 11.63               | 12.12               | 11.64                | 10.60                |
| Medium Hills.gpx           | 18.86               | 17.04               | 15.94               | 22.41               | 28.88               | 21.05               | 23.04               | 22.01               | 22.38               | 22.16                | 20.80                |
| Hard Surrey.gpx            | 50.53               | 43.82               | 39.81               | 46.53               | 53.26               | 41.81               | 48.03               | 47.36               | 47.33               | 47.73                | 46.30                |
| Easy Long.gpx              | 26.83               | 22.70               | 20.57               | 25.81               | 31.05               | 23.62               | 25.96               | 24.98               | 25.44               | 25.01                | 23.96                |
| The Rider.gpx              | 153.27              | 134.55              | 121.82              | 130.19              | 138.57              | 113.99              | 136.75              | 138.23              | 135.87              | 139.85               | 138.03               |

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs, only the final difficulty calculation differed due to parameter changes._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
    
- **Run 9 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=9.5`
    
- **Run 10 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=9`
    
- **Run 11 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=8`

## Test 12
### Changes:
- None - as per test 11. Added 2 new ref routes (LBL and Giro S4)
### GPX Test Results Comparison

This table compares the final calculated difficulty scores from twelve separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|Final Score (Run 6)|Final Score (Run 7)|Final Score (Run 8)|Final Score (Run 9)|Final Score (Run 10)|Final Score (Run 11)|Final Score (Run 12)|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|206.67|250.22|254.37|249.34|257.32|255.51|255.51|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|12.27|12.64|11.63|12.12|11.64|10.60|10.60|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|21.05|23.04|22.01|22.38|22.16|20.80|20.80|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|41.81|48.03|47.36|47.33|47.73|46.30|46.30|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|23.62|25.96|24.98|25.44|25.01|23.96|23.96|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|113.99|136.75|138.23|135.87|139.85|138.03|138.03|
|LBL 2025.gpx|-|-|-|-|-|-|-|-|-|-|-|415.47|
|Giro25 S4.gpx|-|-|-|-|-|-|-|-|-|-|-|181.90|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs for the original 6 files; only the final difficulty calculation differed due to parameter changes. New files were added in Run 12._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
    
- **Run 9 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=9.5`
    
- **Run 10 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=9`
    
- **Run 11 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=8`
    
- **Run 12 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=8` (These are the same as Run 11, so the scores for the original 6 files are identical to Run 11. The new files were processed with these parameters.)
## Test 13
## Changes:
# --- Configuration: Metric Extraction ---
SMOOTHING_WINDOW_SIZE = 7
MCG_SEGMENT_TARGET_DISTANCE_M = 100.0 # User defined
MIN_DIST_FOR_MCG_GRADIENT_CALC_M = 50.0 # User defined
SIG_CLIMB_FACTOR_THRESHOLD = 3500.0
SIG_CLIMB_MIN_DISTANCE_M = 250.0
SIG_CLIMB_MIN_GRADIENT_PERCENT = 3.0
POTENTIAL_CLIMB_START_GRADIENT_THRESHOLD = 1.0
SIG_DESCENT_MIN_DISTANCE_M = 500.0
SIG_DESCENT_MIN_GRADIENT_PERCENT = -3.0
POTENTIAL_DESCENT_START_GRADIENT_THRESHOLD = -1.0

# --- Configuration: Difficulty Calculation ---
# Distance Difficulty
==DISTANCE_BASE_ADDITION = 5.0 # PARAMETER TO TUNE==
==DISTANCE_DIFFICULTY_COEFFICIENT_A = 0.003 # PARAMETER TO TUNE==
# Uphill Impact Component (Linear UF Model)
MAX_EXPECTED_TEGA = 3500.0
MAX_EXPECTED_ACG = 12.0
==MAX_EXPECTED_MCG = 45.0==
WEIGHT_TEGA = 0.50
WEIGHT_ACG = 0.40
WEIGHT_MCG = 0.10
==LINEAR_UF_SLOPE = 1.2 # PARAMETER TO TUNE==

### GPX Test Results Comparison

This table compares the final calculated difficulty scores from thirteen separate runs of the script (`gpx_difficulty_v2.py` or similar) on the same set of GPX files, reflecting different parameter settings.

|GPX Filename|Final Score (Run 1)|Final Score (Run 2)|Final Score (Run 3)|Final Score (Run 4)|Final Score (Run 5)|Final Score (Run 6)|Final Score (Run 7)|Final Score (Run 8)|Final Score (Run 9)|Final Score (Run 10)|Final Score (Run 11)|Final Score (Run 12)|Final Score (Run 13)|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|Dales_Climbers_Classic.gpx|292.64|255.17|230.02|238.34|246.65|206.67|250.22|254.37|249.34|257.32|255.51|255.51|232.10|
|Easy Coastal.gpx|8.34|7.74|7.43|12.59|17.76|12.27|12.64|11.63|12.12|11.64|10.60|10.60|7.10|
|Medium Hills.gpx|18.86|17.04|15.94|22.41|28.88|21.05|23.04|22.01|22.38|22.16|20.80|20.80|15.50|
|Hard Surrey.gpx|50.53|43.82|39.81|46.53|53.26|41.81|48.03|47.36|47.33|47.73|46.30|46.30|38.03|
|Easy Long.gpx|26.83|22.70|20.57|25.81|31.05|23.62|25.96|24.98|25.44|25.01|23.96|23.96|18.47|
|The Rider.gpx|153.27|134.55|121.82|130.19|138.57|113.99|136.75|138.23|135.87|139.85|138.03|138.03|125.98|
|LBL 2025.gpx|-|-|-|-|-|-|-|-|-|-|-|415.47|377.32|
|Giro25 S4.gpx|-|-|-|-|-|-|-|-|-|-|-|181.90|155.46|

_Note: The underlying extracted metrics (Distance, TEGa, PDD, MCg, ACg, ADg) were the same in all runs for the original 6 files; only the final difficulty calculation differed due to parameter changes. New files were added in Run 12._

- **Run 1 Parameters:** `DIST_COEFF=0.005`, `UF_SLOPE=0.6`, `BASE_ADD=5`
    
- **Run 2 Parameters:** (Unknown, user adjusted)
    
- **Run 3 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=5`
    
- **Run 4 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 5 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.8`, `BASE_ADD=15`
    
- **Run 6 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=0.8`, `BASE_ADD=10`
    
- **Run 7 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=10`
    
- **Run 8 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.95`, `BASE_ADD=9`
    
- **Run 9 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.9`, `BASE_ADD=9.5`
    
- **Run 10 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=9`
    
- **Run 11 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=8`
    
- **Run 12 Parameters:** `DIST_COEFF=0.0035`, `UF_SLOPE=0.975`, `BASE_ADD=8`
    
- **Run 13 Parameters:** `DIST_COEFF=0.003`, `UF_SLOPE=1.2`, `BASE_ADD=5`, `MAX_EXPECTED_MCG=45.0`
