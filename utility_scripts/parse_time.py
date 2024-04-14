import re

def parse_time_log(file_path):
    # Regular expressions to match lines
    prediction_re = r"Prediction Time:  (\d+)  miliseconds for OSC: (.+)"
    tuning_re = r"Tuning Time:  (\d+)  miliseconds for OSC: (.+)"
    tuning_cleanup_re = r"Tuning \+ Cleanup Time:  (\d+)  miliseconds"
    snapshot_generation_re = r"Snapshot Generation Time:  (\d+)  miliseconds for OSC: (.+)"

    # Dictionaries to hold times
    prediction_times = {}
    tuning_times = {}
    tuning_cleanup_times = []
    snapshot_generation_times = {}

    with open(file_path, 'r') as file:
        for line in file:
            # Check for prediction time
            prediction_match = re.search(prediction_re, line)
            if prediction_match:
                time, osc = int(prediction_match.group(1)), prediction_match.group(2)
                prediction_times.setdefault(osc, []).append(time)

            # Check for tuning time
            tuning_match = re.search(tuning_re, line)
            if tuning_match:
                time, osc = int(tuning_match.group(1)), tuning_match.group(2)
                tuning_times.setdefault(osc, []).append(time)

            # Check for tuning + cleanup time
            tuning_cleanup_match = re.search(tuning_cleanup_re, line)
            if tuning_cleanup_match:
                time = int(tuning_cleanup_match.group(1))
                tuning_cleanup_times.append(time)

            # Check for snapshot generation time
            snapshot_generation_match = re.search(snapshot_generation_re, line)
            if snapshot_generation_match:
                time, osc = int(snapshot_generation_match.group(1)), snapshot_generation_match.group(2)
                snapshot_generation_times.setdefault(osc, []).append(time)

    # Calculating averages
    prediction_avg = {osc: sum(times)/len(times) for osc, times in prediction_times.items()}
    tuning_avg = {osc: sum(times)/len(times) for osc, times in tuning_times.items()}
    snapshot_generation_avg = {osc: sum(times)/len(times) for osc, times in snapshot_generation_times.items()}

    tuning_cleanup_avg = sum(tuning_cleanup_times) / len(tuning_cleanup_times) if tuning_cleanup_times else 0

    return prediction_avg, tuning_avg, tuning_cleanup_avg, snapshot_generation_avg

# Example of how to call the function
file_path = "/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/profiling_time/model_k_1/dir_rnd_r_1_io_16m_itern_1/rnd_r_1_io_16m_itern_1_rpc_tuning_module_output.txt"
prediction_avg, tuning_avg, tuning_cleanup_avg, snapshot_generation_avg = parse_time_log(file_path)
print("[READ] Snapshot Generation Averages:")
for osc, avg_time in snapshot_generation_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[READ] Prediction Averages:")
for osc, avg_time in prediction_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[READ] Tuning Averages:")
for osc, avg_time in tuning_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[READ] Average Tuning + Cleanup Time:", tuning_cleanup_avg, "milliseconds")

file_path = "/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/profiling_time/model_k_1/dir_rnd_w_1_io_16m_itern_1/rnd_w_1_io_16m_itern_1_rpc_tuning_module_output.txt"
prediction_avg, tuning_avg, tuning_cleanup_avg, snapshot_generation_avg = parse_time_log(file_path)
print("[WRITE] Snapshot Generation Averages:")
for osc, avg_time in snapshot_generation_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[WRITE] Prediction Averages:")
for osc, avg_time in prediction_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[WRITE] Tuning Averages:")
for osc, avg_time in tuning_avg.items():
    print(f"{osc}: {avg_time} milliseconds")

print("\n[WRITE] Average Tuning + Cleanup Time:", tuning_cleanup_avg, "milliseconds")
