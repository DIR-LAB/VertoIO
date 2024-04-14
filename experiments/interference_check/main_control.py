import os
import shutil
import dir_prep
import inf_excn

def get_no_of_runs():
    # Prompt user to input run_no
    start_run_no = int(input("Start no of inference run: "))
    end_run_no = int(input("End no of inference run: "))

    return start_run_no, end_run_no

def retrieve_directories():
    # Setup initial directories (combined logic from both scripts)
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    parent_dir = os.path.dirname(script_dir)
    print(f"Script Directory: {script_dir}")
    print(f"Parent Directory: {parent_dir}")

    return script_dir, parent_dir

def get_inf_types(inf_run_dir):
    # Discover inf_types from local directory structure for the first node
    local_node_dir = os.path.join(inf_run_dir, "node0")
    local_inf_types_dir = os.path.join(local_node_dir, "inf_types")
    inf_types = [dir_name for dir_name in os.listdir(local_inf_types_dir) if os.path.isdir(os.path.join(local_inf_types_dir, dir_name))]
    print(f"Discovered inference types: {inf_types}")

    return inf_types

def main():
    nodes = [
        "c220g5-110905.wisc.cloudlab.us",
        "c220g5-110926.wisc.cloudlab.us",
        "c220g5-111226.wisc.cloudlab.us",
        "c220g5-110421.wisc.cloudlab.us",
        "c220g5-111230.wisc.cloudlab.us"
    ]
    username = "mrashid2"

    # Common directories setup
    script_dir, parent_dir = retrieve_directories()
    wld_src = os.path.join(parent_dir, "filebench_workloads")
    print(f"Source directories set for scripts, models, and workloads.")

    start_run_no, end_run_no = get_no_of_runs()

    for run_no in range(start_run_no, end_run_no+1):
        inf_run_dir = os.path.join(script_dir, "inf_runs", f"inf_run_{run_no}")
        print(f"Inference run directory for run_no {run_no}: {inf_run_dir}")

        # Execute functionality from dir_prep.py
        dir_prep.main(run_no, nodes, inf_run_dir, script_dir, wld_src)

        inf_types = get_inf_types(inf_run_dir)

        # Configuration for remote access
        remote_script_dir = "/root/localssd/filebench"
        remote_results_dir = "/root/localssd/filebench/rpc_tuning_tests/"
        local_target_dir = "/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/inference_tests"

        # Store the data prepared for the tests
        shutil.copytree(inf_run_dir, os.path.join(local_target_dir, f'inf_run_{run_no}'), dirs_exist_ok=True)

        # Execute functionality from inf_excn.py
        inf_excn.main(run_no, nodes, username, inf_types, inf_run_dir, remote_script_dir, remote_results_dir, local_target_dir)

        for i in range(len(nodes)):
            node = os.path.join(inf_run_dir, f"node{i}")
            shutil.rmtree(node)

if __name__ == "__main__":
    main()