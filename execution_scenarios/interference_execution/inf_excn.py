import os
import paramiko
from stat import S_ISDIR
from concurrent.futures import ThreadPoolExecutor, as_completed

# Function to recursively transfer directories and files to a node
def transfer_directories_to_node(scp, local_dir, remote_dir):
    print(f"Transferring {local_dir} to {remote_dir}")
    if os.path.isdir(local_dir):
        # Try to create remote directory
        try:
            scp.mkdir(remote_dir)
            print(f"Created remote directory: {remote_dir}")
        except IOError:
            print(f"Remote directory {remote_dir} already exists.")
        # Recursively transfer all items in the directory
        for item in os.listdir(local_dir):
            local_item_path = os.path.join(local_dir, item)
            remote_item_path = os.path.join(remote_dir, item)
            transfer_directories_to_node(scp, local_item_path, remote_item_path)
    else:
        # It's a file, transfer it
        scp.put(local_dir, remote_dir)
        print(f"Transferred file from {local_dir} to {remote_dir}")

# Check if remote_dir exists, create if not
def create_remote_dir(scp, remote_dir):
    try:
        scp.stat(remote_dir)
    except FileNotFoundError:
        # This means the remote_dir does not exist and needs to be created
        scp.mkdir(remote_dir)

# Updated function to handle SSH connection and initiate transfer
def transfer_directories_to_node_ssh(run_no, node, username, inf_types, node_index, inf_run_dir, remote_script_dir):
    print(f"Starting transfer to {node}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, username=username)

    local_node_dir = os.path.join(inf_run_dir, f"node{node_index}")
    local_inf_types_dir = os.path.join(local_node_dir, "inf_types")

    with paramiko.SFTPClient.from_transport(ssh.get_transport()) as scp:
        create_remote_dir(scp, os.path.join(remote_script_dir, "inf_runs"))
        create_remote_dir(scp, os.path.join(remote_script_dir, "inf_runs", f'inf_run_{run_no}'))

        for inf_type in inf_types:
            local_dir = os.path.join(local_inf_types_dir, inf_type)
            remote_dir = os.path.join(remote_script_dir, "inf_runs", f'inf_run_{run_no}', inf_type)
            create_remote_dir(scp, remote_dir)

            # Recursively transfer directories and files
            transfer_directories_to_node(scp, local_dir, remote_dir)
    ssh.close()
    print(f"Completed transfer to {node}")

# Function to copy inf_type contents to the root filebench directory on a node
def copy_inf_type_contents_on_node(run_no, node, username, inf_type, remote_script_dir):
    print(f"Copying inf_run_{run_no}/{inf_type} contents on {node}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, username=username)

    wld_rm_command = f"sudo rm -rf {remote_script_dir}/*.f"
    stdin, stdout, stderr = ssh.exec_command(wld_rm_command)
    # Capture and print stdout and stderr
    print(stdout.read().decode())
    print(stderr.read().decode())

    copy_command = f"sudo cp -rf {remote_script_dir}/inf_runs/inf_run_{run_no}/{inf_type}/* {remote_script_dir}"
    stdin, stdout, stderr = ssh.exec_command(copy_command)
    # Capture and print stdout and stderr
    print(stdout.read().decode())
    print(stderr.read().decode())

    ssh.close()
    print(f"Completed copying inf_run_{run_no}/{inf_type} contents on {node}")

# Function to execute script on node for a given inf_type
def execute_script_on_node(run_no, node, inf_type, username, remote_script_dir):
    print(f"Executing script for inf_run_{run_no}/{inf_type} on {node}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, username=username)

    command = f"cd {remote_script_dir} && sudo bash aut_rpc_tun.sh"
    stdin, stdout, stderr = ssh.exec_command(command)
    # Capture and print stdout and stderr
    print(stdout.read().decode())
    print(stderr.read().decode())

    ssh.close()
    print(f"Execution completed for inf_run_{run_no}/{inf_type} on {node}")

def concurrent_script_execution(run_no, nodes, inf_type, username, remote_script_dir):
    with ThreadPoolExecutor(max_workers=len(nodes)) as executor:
        futures = [executor.submit(execute_script_on_node, run_no, node, inf_type, username, remote_script_dir) for node in nodes]

        # Wait for all nodes to finish before proceeding to the next inf_type
        for future in as_completed(futures):
            future.result()

# Function to recursively download directory contents
def recursive_scp_get(scp, remote_dir, local_dir):
    print(f"Downloading contents from {remote_dir} to {local_dir}")
    os.makedirs(local_dir, exist_ok=True)
    for item in scp.listdir_attr(remote_dir):
        remote_path = os.path.join(remote_dir, item.filename)
        local_path = os.path.join(local_dir, item.filename)

        if S_ISDIR(item.st_mode):
            recursive_scp_get(scp, remote_path, local_path)
        else:
            scp.get(remote_path, local_path)
            print(f"Downloaded {remote_path} to {local_path}")

def transfer_to_local_machine(node, username, remote_results_dir, local_target_dir):
    print(f"Transferring results back from {node}")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(node, username=username)

    with paramiko.SFTPClient.from_transport(ssh.get_transport()) as scp:
        recursive_scp_get(scp, remote_results_dir, local_target_dir)

    ssh.close()

def main(run_no, nodes, username, inf_types, inf_run_dir, remote_script_dir, remote_results_dir, local_target_dir):
    # Sequentially transfer directories to each node and copy those directories to the root filebench directory
    for i, node in enumerate(nodes):
        transfer_directories_to_node_ssh(run_no, node, username, inf_types, i, inf_run_dir, remote_script_dir)
    print("All transfers have been completed on all nodes.")

    # Concurrently execute scripts for each inf_type across all nodes
    for inf_type in inf_types:
        print(f"Processing inf_run_{run_no}/inf_type: {inf_type} across all nodes")
        for i, node in enumerate(nodes):
            copy_inf_type_contents_on_node(run_no, node, username, inf_type, remote_script_dir)
        concurrent_script_execution(run_no, nodes, inf_type, username, remote_script_dir)
        print(f"Completed processing for inf_run_{run_no}/inf_type: {inf_type}")

    # Transfer results back to local machine
    for node in nodes:
        transfer_to_local_machine(node, username, remote_results_dir, local_target_dir)
    print("All inf_types have been processed on all nodes.")

# Ensure the script does not execute when imported
if __name__ == "__main__":
    # Setup initial directories based on the script location
    script_path = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_path)
    print(f"Script directory set to: {script_dir}")

    # Prompt user to input run_no
    run_no = input("Enter inference run_no: ")
    inf_run_dir = os.path.join(script_dir, "inf_runs", f"inf_run_{run_no}")
    print(f"Inference run directory set to: {inf_run_dir}")

    # Configuration for remote access
    remote_script_dir = "/root/localssd/filebench"
    remote_results_dir = "/root/localssd/filebench/rpc_tuning_tests/"
    local_target_dir = "/Users/mrashid2/dirlab/ml_tests/ml_xgb_thrsh/fifth_version/inference_tests"
    nodes = [
        "c220g5-110905.wisc.cloudlab.us",
        "c220g5-110926.wisc.cloudlab.us",
        "c220g5-111226.wisc.cloudlab.us",
        "c220g5-110421.wisc.cloudlab.us",
        "c220g5-111230.wisc.cloudlab.us"
    ]
    username = "mrashid2"
    print("SSH configuration set for nodes.")

    # Discover inf_types from local directory structure for the first node
    local_node_dir = os.path.join(inf_run_dir, "node0")
    local_inf_types_dir = os.path.join(local_node_dir, "inf_types")
    inf_types = [dir_name for dir_name in os.listdir(local_inf_types_dir) if os.path.isdir(os.path.join(local_inf_types_dir, dir_name))]
    print(f"Discovered inference types: {inf_types}")

    main(run_no, nodes, username, inf_types, inf_run_dir, remote_script_dir, remote_results_dir, local_target_dir)