import os
import glob
import shutil

def load_and_modify_file_paths(inf_run_dir):
    # Load workload file names
    inf_types = []
    file_paths = {}
    print("Loading workload file names...")

    for txt_file in glob.glob(os.path.join(inf_run_dir, "*.txt")):
        inf_type = os.path.splitext(os.path.basename(txt_file))[0]
        inf_types.append(inf_type)
        file_paths[inf_type] = []
        print(f"Found inference type: {inf_type}")

        with open(txt_file, "r") as f:
            for line in f:
                workload_file = line.strip() + ".f"
                prefix = ""
                print(f"Processing workload file: {workload_file}")

                # Modify the path based on specific conditions
                if inf_type.endswith("_dd_10g"):
                    prefix = "wlds_dd/"
                elif inf_type.endswith("_dd_1g") and ("write" in workload_file or "_w_" in workload_file):
                    prefix = "wlds_dd/write_wlds_dd_aggr_5g/"
                elif inf_type.endswith("_dd_1g"):
                    prefix = "wlds_dd/"
                elif inf_type.endswith("_psd_1g") and ("write" in workload_file or "_w_" in workload_file):
                    prefix = "write_wlds_aggr_5g/"

                # Store the modified file path
                file_paths[inf_type].append(prefix + workload_file)
                print(f"Modified path stored for {workload_file}: {prefix + workload_file}")
    return inf_types, file_paths

# Create directories and copy files based on inf_type
def setup_directories_and_copy_files(nodes, inf_run_dir, script_dir, wld_src, inf_types, file_paths):
    print("Creating directories and copying files based on inference type...")
    for i in range(len(nodes)):
        node = os.path.join(inf_run_dir, f"node{i}")
        print(f"Setting up directories for node{i}")
        os.makedirs(os.path.join(node, "read_prep"), exist_ok=True)
        os.makedirs(os.path.join(node, "write_prep"), exist_ok=True)

        shutil.copy(os.path.join(script_dir, "aut_rpc_tun_read.sh"), os.path.join(node, "read_prep", "aut_rpc_tun.sh"))
        shutil.copy(os.path.join(script_dir, "aut_rpc_tun_write.sh"), os.path.join(node, "write_prep", "aut_rpc_tun.sh"))

        for inf_type in inf_types:
            target_dir = os.path.join(node, "inf_types", inf_type)
            os.makedirs(target_dir, exist_ok=True)
            print(f"Preparing target directory for {inf_type} in node{i}")
            if i < len(file_paths[inf_type]):
                shutil.copy(os.path.join(wld_src, file_paths[inf_type][i]), target_dir)
                print(f"Copied workload file for {inf_type} to {target_dir}")

# Replicate preparation scripts based on the workload file type
def replicate_preparation_scripts(nodes, inf_run_dir, inf_types):
    print("Replicating preparation scripts based on the workload file type...")
    for i in range(len(nodes)):
        node = os.path.join(inf_run_dir, f"node{i}")
        for inf_type in inf_types:
            target_dir = os.path.join(node, "inf_types", inf_type)
            print(f"Processing inference type: {inf_type} for node{i}")
            for file_name in os.listdir(target_dir):
                print(f"Checking file {file_name} for read or write preparation replication.")
                if "read" in file_name or "_r_" in file_name:
                    print(f"Replicating read preparation scripts for {file_name}")
                    shutil.copytree(os.path.join(node, "read_prep"), target_dir, dirs_exist_ok=True)
                elif "write" in file_name or "_w_" in file_name:
                    print(f"Replicating write preparation scripts for {file_name}")
                    shutil.copytree(os.path.join(node, "write_prep"), target_dir, dirs_exist_ok=True)

def modify_wld_excn_script(run_no, nodes, inf_run_dir, inf_types):
    for i in range(len(nodes)):
        node = os.path.join(inf_run_dir, f"node{i}")
        for inf_type in inf_types:
            target_dir = os.path.join(node, "inf_types", inf_type)
            print(f"Finalizing setup for {inf_type} in node{i}")
            script_path = os.path.join(target_dir, "aut_rpc_tun.sh")

            # Assuming there's only one .f file per target_dir or you're only interested in the first one
            file_names = [fn for fn in os.listdir(target_dir) if fn.endswith('.f')]
            if file_names:
                file_name_without_extension = file_names[0][:-2]  # Remove the .f extension
                print(f"Configuring script for {file_name_without_extension} in {inf_type}")

                if os.path.exists(script_path):
                    # Read the content of the script
                    with open(script_path, 'r') as file:
                        lines = file.readlines()

                    # Replace the specific lines
                    with open(script_path, 'w') as file:
                        for line in lines:
                            if line.strip().startswith("workload="):
                                file.write(f"workload={file_name_without_extension}\n")
                            elif line.strip().startswith("k_val="):
                                file.write("k_val=1\n")
                            elif line.strip().startswith("run_no="):
                                file.write(f"run_no={run_no}\n")
                            elif line.strip() == "inf_excn_type=modify":
                                file.write(f"inf_excn_type={inf_type}\n")
                            else:
                                file.write(line)
                    print(f"Script configured successfully for {file_name_without_extension} in {inf_type}")

def main(run_no, nodes, inf_run_dir, script_dir, wld_src):
    inf_types, file_paths = load_and_modify_file_paths(inf_run_dir)
    setup_directories_and_copy_files(nodes, inf_run_dir, script_dir, wld_src, inf_types, file_paths)
    replicate_preparation_scripts(nodes, inf_run_dir, inf_types)
    modify_wld_excn_script(run_no, nodes, inf_run_dir, inf_types)

# Ensure the script does not execute when imported
if __name__ == "__main__":
    # Setup initial directories
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    parent_dir = os.path.dirname(script_dir)

    print(f"Script Directory: {script_dir}")
    print(f"Parent Directory: {parent_dir}")

    wld_src = os.path.join(script_dir, "inf_wlds")
    print(f"Source directories set for scripts, models, and workloads.")

    # Prompt user to input run_no
    run_no = input("Enter inference run_no: ")
    inf_run_dir = os.path.join(script_dir, "inf_runs", f"inf_run_{run_no}")
    print(f"Inference run directory for run_no {run_no}: {inf_run_dir}")

    # Check if the directory exists
    if not os.path.isdir(inf_run_dir):
        print(f"Directory does not exist: {inf_run_dir}")
        exit(1)

    nodes = [
        "c220g5-110905.wisc.cloudlab.us",
        "c220g5-110926.wisc.cloudlab.us",
        "c220g5-111226.wisc.cloudlab.us",
        "c220g5-110421.wisc.cloudlab.us",
        "c220g5-111230.wisc.cloudlab.us"
    ]

    main(run_no, nodes, inf_run_dir, script_dir, wld_src)