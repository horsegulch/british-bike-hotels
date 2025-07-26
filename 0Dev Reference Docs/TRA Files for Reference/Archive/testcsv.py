import csv

# --- Data for GPX Test Scores ---
score_header = [
    "GPX Filename", 
    "Final Score (Run 1)", "Final Score (Run 2)", "Final Score (Run 3)", 
    "Final Score (Run 4)", "Final Score (Run 5)", "Final Score (Run 6)", 
    "Final Score (Run 7)", "Final Score (Run 8)", "Final Score (Run 9)", 
    "Final Score (Run 10)", "Final Score (Run 11)", "Final Score (Run 12)",
    "Final Score (Run 13)", "Final Score (Run 14)"
]

score_data = [
    ["Dales_Climbers_Classic.gpx", 292.64, 255.17, 230.02, 238.34, 246.65, 206.67, 250.22, 254.37, 249.34, 257.32, 255.51, 255.51, 232.10],
    ["Easy Coastal.gpx", 8.34, 7.74, 7.43, 12.59, 17.76, 12.27, 12.64, 11.63, 12.12, 11.64, 10.60, 10.60, 7.10],
    ["Medium Hills.gpx", 18.86, 17.04, 15.94, 22.41, 28.88, 21.05, 23.04, 22.01, 22.38, 22.16, 20.80, 20.80, 15.50],
    ["Hard Surrey.gpx", 50.53, 43.82, 39.81, 46.53, 53.26, 41.81, 48.03, 47.36, 47.33, 47.73, 46.30, 46.30, 38.03],
    ["Easy Long.gpx", 26.83, 22.70, 20.57, 25.81, 31.05, 23.62, 25.96, 24.98, 25.44, 25.01, 23.96, 23.96, 18.47],
    ["The Rider.gpx", 153.27, 134.55, 121.82, 130.19, 138.57, 113.99, 136.75, 138.23, 135.87, 139.85, 138.03, 138.03, 125.98],
    ["LBL 2025.gpx", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", 415.47, 377.32],
    ["Giro25 S4.gpx", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", 181.90, 155.46]
]

# --- Data for Extracted Metrics (using latest available data, e.g., from Run 14 output) ---
metrics_header = [
    "GPX Filename", "Distance (km)", "TEGa (m)", "TEGa_raw (m)", "TEGa_smoothed (m)", 
    "PDD", "MCg (%)", "ACg (%)", "ADg (%)", "Raw Points Count"
]

extracted_metrics_data = [
    {"GPX Filename": "Dales_Climbers_Classic.gpx", "Distance (km)": 195.166, "TEGa (m)": 3504.443, "TEGa_raw (m)": 4074.400, "TEGa_smoothed (m)": 3504.443, "PDD": 0.502, "MCg (%)": 26.778, "ACg (%)": 6.864, "ADg (%)": 5.868, "Raw Points Count": 5848},
    {"GPX Filename": "Easy Coastal.gpx", "Distance (km)": 25.068, "TEGa (m)": 98.700, "TEGa_raw (m)": 218.000, "TEGa_smoothed (m)": 98.700, "PDD": 0.526, "MCg (%)": 5.260, "ACg (%)": 0.000, "ADg (%)": 0.000, "Raw Points Count": 476},
    {"GPX Filename": "Medium Hills.gpx", "Distance (km)": 45.713, "TEGa (m)": 436.700, "TEGa_raw (m)": 556.500, "TEGa_smoothed (m)": 436.700, "PDD": 0.484, "MCg (%)": 20.276, "ACg (%)": 6.157, "ADg (%)": 4.530, "Raw Points Count": 952},
    {"GPX Filename": "Hard Surrey.gpx", "Distance (km)": 83.834, "TEGa (m)": 1051.314, "TEGa_raw (m)": 1321.600, "TEGa_smoothed (m)": 1051.314, "PDD": 0.518, "MCg (%)": 22.646, "ACg (%)": 5.432, "ADg (%)": 4.610, "Raw Points Count": 1857},
    {"GPX Filename": "Easy Long.gpx", "Distance (km)": 64.654, "TEGa (m)": 218.900, "TEGa_raw (m)": 378.500, "TEGa_smoothed (m)": 218.900, "PDD": 0.526, "MCg (%)": 5.761, "ACg (%)": 0.000, "ADg (%)": 4.337, "Raw Points Count": 1261},
    {"GPX Filename": "The Rider.gpx", "Distance (km)": 139.104, "TEGa (m)": 3724.743, "TEGa_raw (m)": 4799.700, "TEGa_smoothed (m)": 3724.743, "PDD": 0.497, "MCg (%)": 39.541, "ACg (%)": 7.315, "ADg (%)": 6.739, "Raw Points Count": 9068},
    {"GPX Filename": "LBL 2025.gpx", "Distance (km)": 251.602, "TEGa (m)": 4212.571, "TEGa_raw (m)": 4290.000, "TEGa_smoothed (m)": 4212.571, "PDD": 0.477, "MCg (%)": 22.175, "ACg (%)": 6.918, "ADg (%)": 5.241, "Raw Points Count": 14664},
    {"GPX Filename": "Giro25 S4.gpx", "Distance (km)": 188.950, "TEGa (m)": 669.286, "TEGa_raw (m)": 730.000, "TEGa_smoothed (m)": 669.286, "PDD": 0.543, "MCg (%)": 19.924, "ACg (%)": 5.470, "ADg (%)": 3.608, "Raw Points Count": 4019}
]

# --- Data for Run Parameters (Full List) ---
# Define all parameters that constitute the difficulty calculation model
# These are assumed to be constant unless specified otherwise for a particular run
BASE_PARAMS = {
    "MAX_EXPECTED_TEGA": 3500.0, "MAX_EXPECTED_ACG": 12.0, 
    "WEIGHT_TEGA": 0.50, "WEIGHT_ACG": 0.40, "WEIGHT_MCG": 0.10,
    "PDD_THRESHOLD": 0.65, "MAX_ASCENT_FOR_DOWNHILL_REDUCTION": 1000.0,
    "MIN_AVG_DESCENT_GRADIENT_THRESHOLD": 3.0, "TARGET_ADG_FOR_MAX_REDUCTION": 7.0,
    "WEIGHT_PDD_SCORE": 0.7, "WEIGHT_ADG_SCORE": 0.3,
    "MAX_DOWNHILL_REDUCTION_FACTOR": 0.8, "MIN_DIFFICULTY_SCORE": 0.0,
    "Score Capping": "Uncapped"
}

parameter_full_header = [
    "Run Number", "DISTANCE_BASE_ADDITION", "DISTANCE_DIFFICULTY_COEFFICIENT_A", 
    "LINEAR_UF_SLOPE", "MAX_EXPECTED_MCG (Normalization)",
    "MAX_EXPECTED_TEGA", "MAX_EXPECTED_ACG", 
    "WEIGHT_TEGA", "WEIGHT_ACG", "WEIGHT_MCG",
    "PDD_THRESHOLD", "MAX_ASCENT_FOR_DOWNHILL_REDUCTION",
    "MIN_AVG_DESCENT_GRADIENT_THRESHOLD", "TARGET_ADG_FOR_MAX_REDUCTION",
    "WEIGHT_PDD_SCORE", "WEIGHT_ADG_SCORE", "MAX_DOWNHILL_REDUCTION_FACTOR"
    # MIN_DIFFICULTY_SCORE and Score Capping are constant for these runs so not included in table rows
]

# Data for each run, including the tuned parameters and the base parameters
run_parameters_full_data = [
    # Run 1
    {**{"Run Number": "Run 1", "DISTANCE_BASE_ADDITION": 5.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.005, "LINEAR_UF_SLOPE": 0.6, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 2 (Parameters Unknown)
    {**{"Run Number": "Run 2", "DISTANCE_BASE_ADDITION": "N/A", "DISTANCE_DIFFICULTY_COEFFICIENT_A": "N/A", "LINEAR_UF_SLOPE": "N/A", "MAX_EXPECTED_MCG (Normalization)": "N/A"}, **BASE_PARAMS},
    # Run 3
    {**{"Run Number": "Run 3", "DISTANCE_BASE_ADDITION": 5.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.8, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 4
    {**{"Run Number": "Run 4", "DISTANCE_BASE_ADDITION": 10.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.8, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 5
    {**{"Run Number": "Run 5", "DISTANCE_BASE_ADDITION": 15.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.8, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 6
    {**{"Run Number": "Run 6", "DISTANCE_BASE_ADDITION": 10.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.003, "LINEAR_UF_SLOPE": 0.8, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 7
    {**{"Run Number": "Run 7", "DISTANCE_BASE_ADDITION": 10.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.9, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 8
    {**{"Run Number": "Run 8", "DISTANCE_BASE_ADDITION": 9.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.95, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 9
    {**{"Run Number": "Run 9", "DISTANCE_BASE_ADDITION": 9.5, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.9, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 10
    {**{"Run Number": "Run 10", "DISTANCE_BASE_ADDITION": 9.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.975, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 11
    {**{"Run Number": "Run 11", "DISTANCE_BASE_ADDITION": 8.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.975, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 12
    {**{"Run Number": "Run 12", "DISTANCE_BASE_ADDITION": 8.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.0035, "LINEAR_UF_SLOPE": 0.975, "MAX_EXPECTED_MCG (Normalization)": 20.0}, **BASE_PARAMS},
    # Run 13
    {**{"Run Number": "Run 13", "DISTANCE_BASE_ADDITION": 5.0, "DISTANCE_DIFFICULTY_COEFFICIENT_A": 0.003, "LINEAR_UF_SLOPE": 1.2, "MAX_EXPECTED_MCG (Normalization)": 45.0}, **BASE_PARAMS}
]


# --- CSV File Name for Combined Output ---
combined_csv_file = "gpx_all_test_data.csv"

try:
    with open(combined_csv_file, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        # --- Write Scores Table ---
        csvwriter.writerow(["GPX Test Scores"]) # Title for the first table
        csvwriter.writerow(score_header)
        csvwriter.writerows(score_data)
        csvwriter.writerow([]) # Add an empty row for separation
        csvwriter.writerow([]) # Add another empty row

        # --- Write Extracted Metrics Table ---
        csvwriter.writerow(["Extracted Metrics for Each GPX File (Based on Latest Data)"]) # Title
        # Need to convert list of dicts to list of lists for writerows
        csvwriter.writerow(metrics_header) # Write header first
        for row_dict in extracted_metrics_data:
            csvwriter.writerow([row_dict.get(col, "") for col in metrics_header]) # Write data rows
        csvwriter.writerow([]) 
        csvwriter.writerow([]) 

        # --- Write Full Parameters Table ---
        csvwriter.writerow(["Full Parameters for Each Test Run"]) # Title
        csvwriter.writerow(parameter_full_header) # Write header first
        for row_dict in run_parameters_full_data:
             csvwriter.writerow([row_dict.get(col, "") for col in parameter_full_header]) # Write data rows

    print(f"Successfully created combined CSV file: {combined_csv_file}")
    print("This file contains Test Scores, Extracted Metrics, and Run Parameters.")

except Exception as e:
    print(f"An unexpected error occurred: {e}")

