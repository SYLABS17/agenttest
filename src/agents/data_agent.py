import pandas as pd
from io import StringIO
from src.graph.state import GraphState

def data_agent_node(state: GraphState) -> GraphState:
    """
    Agent A: Data & Schema Agent
    - Ingests data from the given path.
    - Cleans the data (handles missing values).
    - Profiles the data to create a summary.
    - Updates the graph state.
    """
    print("--- Starting Agent A: Data & Schema ---")

    # 1. Ingest data
    raw_data_path = state['raw_data_path']
    try:
        df = pd.read_csv(raw_data_path)
    except FileNotFoundError:
        log_message = f"Error: The file '{raw_data_path}' was not found."
        print(log_message)
        state['logs'].append(log_message)
        return state

    log_message = f"Successfully loaded data from '{raw_data_path}' with shape {df.shape}."
    print(log_message)

    # 2. Clean data (basic cleaning)
    # For this dataset, let's just drop rows with any missing values for simplicity
    initial_rows = len(df)
    df.dropna(inplace=True)
    cleaned_rows = len(df)
    if initial_rows > cleaned_rows:
        log_message += f" Dropped {initial_rows - cleaned_rows} rows with missing values."
        print(f"Dropped {initial_rows - cleaned_rows} rows with missing values.")

    # 3. Profile data
    # Use StringIO to capture pandas .info() output
    info_buffer = StringIO()
    df.info(buf=info_buffer)
    info_str = info_buffer.getvalue()

    # Get .describe() output
    describe_df = df.describe()

    df_summary = {
        "schema": df.dtypes.to_dict(),
        "info": info_str,
        "describe": describe_df.to_dict(),
        "num_rows": cleaned_rows,
        "num_cols": len(df.columns)
    }

    print("Data profiling complete. Summary generated.")

    # 4. Update state
    state['df'] = df
    state['df_summary'] = df_summary
    state['logs'].append(log_message)

    print("--- Finished Agent A ---")

    return state
