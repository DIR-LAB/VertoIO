import config
import numpy as np
import pandas as pd
import tuning_config
import xgboost as xgb
from typing import List, Literal

# the helper function to clip a specific column in-place
def clip_cols(df: pd.DataFrame, clip_bounds: dict[str, tuple[int|float, int|float]]) -> None:
    """
    Clip columns in-place in a data frame.
    param:
        df: pd.DataFrame, the dataframe to be clipped
        clip_bounds: dict, the clip bounds for each column
    return:
        None
    """
    for col, bounds in clip_bounds.items():
        if col in df.columns:
            # Apply clipping directly to the column and reassign
            df[col] = df[col].clip(*bounds)

# <<<<<<<<< NEEDS ADAPTATION FOR TUNING >>>>>>>>>>>
def process_theta(df: pd.DataFrame, theta_cols: List[str], log  = False) -> pd.DataFrame:
  """
  Process the theta columns in-place in a data frame.
  param:
      df: pd.DataFrame, the dataframe to be processed
      theta_cols: List[str], the columns to be processed
      log: bool, whether to log the processing
  return:
      DataFrame containing the processed columns
  """
  # **Note**: the theta at time {t+1} and the s feats at time {t} is the input to predict performance y_{t+1}
  res_df = pd.DataFrame()
  for col in theta_cols:
    if log:
      res_df[col] = np.log2(df[col]).shift(-1).fillna(df[col])
    else:
      res_df[col] = df[col].shift(-1).fillna(df[col])
  return res_df

def feature_engineering(df: pd.DataFrame, clip_bounds: dict = {},
                        mode: Literal['both', 'read-only', 'write-only'] = 'both') -> pd.DataFrame:
    """
    build the features and target from the raw data based on the formula provided in ../README.md
    param:
        df: pd.DataFrame, the raw data
        clip_bounds: dict, the clip bounds for feature columns, empty if clipping is not needed
    return:
        pandas.DataFrame: secondary features
    """

    # Creating secondary features per the formulas here https://github.com/DIR-LAB/Adaptive-Tuning/tree/dl_scratch
    s_feat_df = pd.DataFrame()

    # There are 10 secondary features. We will first build Features 1, 3, 5, 7, and 9.
    # Then clip the values of some of them, before building Features 2, 4, 6, 8, and 10.

    # Feature 1:
    # the ratio of used cache to maximum cache
    s_feat_df["ratio_of_used_cache_to_maximum_cache"] = df["cur_dirty_bytes"] / \
        (df["osc_rpc_configuration_current.mdm_value"] * 1024 * 1024)

    # Feature 3:
    # the amount of IO transfer
    # which is the sum of read and write
    if mode == 'both':
      s_feat_df["amount_of_rpc_transfer"] = (
          df["ost_read_rpc_bytes_data.samples_sum"] +
          df["ost_write_rpc_bytes_data.samples_sum"]
      )
    elif mode == 'read-only':
      s_feat_df["amount_of_rpc_transfer"] = df["ost_read_rpc_bytes_data.samples_sum"]
    elif mode == 'write-only':
      s_feat_df["amount_of_rpc_transfer"] = df["ost_write_rpc_bytes_data.samples_sum"]

    # Feature 5:
    # average RPC latency
    avg_read_rpc_latency = (df["ost_read_rpc_usec_data.samples_sum"] /
                            df["ost_read_rpc_usec_data.no_of_samples"]).fillna(0)
    avg_write_rpc_latency = (df["ost_write_rpc_usec_data.samples_sum"] /
                             df["ost_write_rpc_usec_data.no_of_samples"]).fillna(0)

    if mode == 'both':
      avg_pages_per_rpc = ((df["ost_read_rpc_bytes_data.samples_sum"] + df["ost_write_rpc_bytes_data.samples_sum"])
                         / (df["ost_read_rpc_bytes_data.no_of_samples"] + df["ost_write_rpc_bytes_data.no_of_samples"]) / 4096)
      s_feat_df["avg_rpc_latency"] = (avg_read_rpc_latency + avg_write_rpc_latency) / (
          avg_pages_per_rpc * (df["avg_rpcs_in_flight"] + 1) * 2
      )
    elif mode == 'read-only':
      avg_pages_per_rpc = df["ost_read_rpc_bytes_data.samples_sum"] / \
            df['ost_read_rpc_bytes_data.no_of_samples'] / 4096
      s_feat_df["avg_rpc_latency"] = avg_read_rpc_latency / (avg_pages_per_rpc * (df["avg_rpcs_in_flight"] + 1))
    elif mode == 'write-only':
      avg_pages_per_rpc = df["ost_write_rpc_bytes_data.samples_sum"] / \
            df['ost_write_rpc_bytes_data.no_of_samples'] / 4096
      s_feat_df["avg_rpc_latency"] = avg_write_rpc_latency / (avg_pages_per_rpc * (df["avg_rpcs_in_flight"] + 1))

    # Feature 7:
    # the ratio of average to maximum pages per RPC
    s_feat_df["ratio_of_average_to_maximum_pages_per_rpc"] = avg_pages_per_rpc / \
        df["osc_rpc_configuration_current.mppr_value"]

    # Feature 9:
    # the ratio of average to maximum RPC in flight
    s_feat_df["ratio_of_average_to_maximum_rpc_in_flight"] = df["avg_rpcs_in_flight"] / \
        df["osc_rpc_configuration_current.mrif_value"]

    # clip all features above
    clip_cols(s_feat_df, clip_bounds)

    # Feature 2:
    s_feat_df["diff_in_ratio_of_used_cache_to_maximum_cache"] = s_feat_df["ratio_of_used_cache_to_maximum_cache"] - \
        s_feat_df["ratio_of_used_cache_to_maximum_cache"].shift(1)

    # Feature 4:
    # diff in amount of IO transfer
    s_feat_df["diff_in_amount_of_rpc_transfer"] = s_feat_df["amount_of_rpc_transfer"] - \
        s_feat_df["amount_of_rpc_transfer"].shift(1)

    # Feature 6:
    # diff in average RPC latency
    s_feat_df["diff_in_avg_rpc_latency"] = s_feat_df["avg_rpc_latency"] - \
        s_feat_df["avg_rpc_latency"].shift(1)

    # Feature 8:
    # diff in the ratio of average to maximum pages per RPC
    s_feat_df["diff_in_ratio_of_average_to_maximum_pages_per_rpc"] = s_feat_df["ratio_of_average_to_maximum_pages_per_rpc"] - \
        s_feat_df["ratio_of_average_to_maximum_pages_per_rpc"].shift(1)

    # Feature 10:
    # diff in the ratio of average to maximum RPC in flight
    s_feat_df["diff_in_ratio_of_average_to_maximum_rpc_in_flight"] = s_feat_df["ratio_of_average_to_maximum_rpc_in_flight"] - \
        s_feat_df["ratio_of_average_to_maximum_rpc_in_flight"].shift(1)

    return s_feat_df  # only return secondary features

def build_feats(input_df: pd.DataFrame,
                mode: Literal['both', 'read-only', 'write-only'] = 'both',
                target = 'avg_rpc_latency',
                keep_observation: bool = True,
                log: bool = True,
                keep_raw_s_feats: bool = False,
                clip_bounds: dict = {}) -> pd.DataFrame:
    """
    build the features and target from the raw data based on the formula provided in ../README.md
    param:
        input_df: pd.DataFrame, the raw data
        keep_observation: bool, whether to keep the observation number
        log: bool, whether to apply log transformation on theta features
        clip_bounds: dict or None, if not None, clip the features and target to the range specified in clip_bounds
    return:
        pd.DataFrame, the dataframe with features and target, keep the relative order of the input_df
    """
    # ensure the dataframe is in float type
    data_df = input_df.astype('float')

    # handle the theta features
    theta_df = process_theta(data_df, theta_cols=tuning_config.theta, log=log)

    # build the seconadary features
    s_feat_df = feature_engineering(data_df, clip_bounds, mode=mode)

    # clip the secondary features
    raw_feats = tuning_config.raw_s_feats if keep_raw_s_feats else []
    file_info = ['observation_no'] if keep_observation else []
    feats_dfs = [theta_df, s_feat_df, data_df[raw_feats], data_df[file_info]]

    # concatenate all those dataframes
    feats_df = pd.concat(feats_dfs, axis=1)
    feats_df['target'] = feats_df[target]

    # drop those rows without previous record, which leads to NaN in the difference features
    feats_df.dropna(inplace=True)

    return feats_df

def extract_client_obsrvn_dict(client_snap, record_dur, obsvn_cnt):
    client_stats_features_list = {}
    llite_params_list = client_snap.llite_snapshot.construct_params_list()

    for osc_name in client_snap.osc_names:
        osc_stats_features_list = client_snap.construct_stats_and_features_list_per_osc(llite_params_list, client_snap.osc_snapshots[osc_name], record_dur, obsvn_cnt)
        client_stats_features_list[osc_name] = osc_stats_features_list

    return client_stats_features_list

def is_osc_samples_io_inactive(cur_osc_snap, prev_osc_snap):
    if cur_osc_snap.ost_read_rpc_bytes_data.no_of_samples == 0 and cur_osc_snap.ost_write_rpc_bytes_data.no_of_samples == 0:
        return True

    if prev_osc_snap.ost_read_rpc_bytes_data.no_of_samples == 0 and prev_osc_snap.ost_write_rpc_bytes_data.no_of_samples == 0:
        return True

    return False

def extract_client_feats_df_dict(cur_snap, prev_snap, record_dur, seq_length, obsvn_cnt):
    header_list = config.stat_name_list + config.feature_name_list
    cur_obsrvn_dict = extract_client_obsrvn_dict(cur_snap, record_dur, obsvn_cnt)

    # Although we did a wrong assignment of record_dur here, it's not important
    prev_obsrvn_dict = extract_client_obsrvn_dict(prev_snap, record_dur, obsvn_cnt)

    client_feats_df_dict_read = {}
    client_feats_df_dict_write = {}

    for osc_name in cur_snap.osc_names:
        for idx, header in enumerate(header_list):
            if len(cur_snap.osc_snapshots[osc_name].seq_data[header]) == 0 or seq_length == 0:
                cur_snap.osc_snapshots[osc_name].seq_data[header] = [prev_obsrvn_dict[osc_name][idx], cur_obsrvn_dict[osc_name][idx]]
            elif len(cur_snap.osc_snapshots[osc_name].seq_data[header]) < (seq_length + 1):
                cur_snap.osc_snapshots[osc_name].seq_data[header].append(cur_obsrvn_dict[osc_name][idx])
            else:
                cur_snap.osc_snapshots[osc_name].seq_data[header].pop(0)
                cur_snap.osc_snapshots[osc_name].seq_data[header].append(cur_obsrvn_dict[osc_name][idx])

        input_df = pd.DataFrame(cur_snap.osc_snapshots[osc_name].seq_data)
        num_rows = len(input_df.iloc[0:])

        if num_rows < (seq_length + 1):
            client_feats_df_dict_read[osc_name] = {}
            client_feats_df_dict_write[osc_name] = {}
        elif seq_length == 0:
            client_feats_df_dict_read[osc_name] = build_feats(input_df, mode='read-only', target='amount_of_rpc_transfer', keep_observation=False, log=True, keep_raw_s_feats=True, clip_bounds=tuning_config.clip_bounds)
            client_feats_df_dict_write[osc_name] = build_feats(input_df, mode='write-only', target='amount_of_rpc_transfer', keep_observation=False, log=True, keep_raw_s_feats=True, clip_bounds=tuning_config.clip_bounds)
        else:
            client_feats_df_dict_read[osc_name] = build_feats(input_df, mode='read-only', target='amount_of_rpc_transfer', keep_observation=False, log=True, keep_raw_s_feats=False, clip_bounds=tuning_config.clip_bounds)
            client_feats_df_dict_write[osc_name] = build_feats(input_df, mode='write-only', target='amount_of_rpc_transfer', keep_observation=False, log=True, keep_raw_s_feats=False, clip_bounds=tuning_config.clip_bounds)

    return client_feats_df_dict_read, client_feats_df_dict_write

def feat_columns(df: pd.DataFrame):
    """
    determine the feat columns in the dataframe (before lag), [s_feats + theta] or [s_raw_feats + s_feats + theta]
    in ascending order of the column names (lexicographical order), to keep consistent when normalizing
    param:
        df: pd.DataFrame, the dataframe to be checked
    return:
        List[str], the feat column names
    """
    return sorted(list(set(df.columns) & (set(tuning_config.s_feats + tuning_config.theta + tuning_config.raw_s_feats))))

def build_sequential_data(df: pd.DataFrame, k: int = 1):
    """
    build the sequential data from the raw data by rolling window for each file
    param:
        df: pd.DataFrame, the raw dataframe
        k: window size
    return:
        pd.DataFrame, the sequential data
        List[str], the feat column names
    """
    if k == 0:
        return df.copy(), tuning_config.raw_s_feats + tuning_config.theta
    if k == 1:
        return df.copy(), tuning_config.s_feats + tuning_config.theta
    feats = feat_columns(df)

    for i in range(1, k):
        df = df.join(df[feats].shift(i).add_suffix(f'_lag{i}'))
    df.dropna()

    return df, feats + [f'{f}_lag{i}' for f in feats for i in range(1, k)]

def build_seq_df_dict(cur_snap, prev_snap, seq_length, client_feats_df_dict):
    for osc_name in cur_snap.osc_names:
        if is_osc_samples_io_inactive(cur_snap.osc_snapshots[osc_name], prev_snap.osc_snapshots[osc_name]) or len(client_feats_df_dict[osc_name]) == 0:
            continue

        client_feats_df_dict[osc_name], _ = build_sequential_data(client_feats_df_dict[osc_name], seq_length)

    return client_feats_df_dict

def load_model(path):
    """Load the model from the path"""
    model = xgb.XGBClassifier()
    model.load_model(path)
    return model

def predict(model, X, feats):
    """Return the probabilities based on the model and the input"""
    return model.predict_proba(X[feats].values)[:,1]

def normalize(value, min_value, max_value):
    """Normalize value to a range of 0 to 1."""
    if max_value == min_value:
        return 1
    return (value - min_value) / (max_value - min_value)
