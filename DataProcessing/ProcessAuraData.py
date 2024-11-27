import pandas as pd

def process_concentration_data(aura_data_file, aura_training_file=None) -> None:
    """
    Process the aura data by normalizing it against training data averages or self averages if no training file.
    Processes both Beta and Theta waves for each electrode. The normalized data replaces the original values 
    in each column.
    The data will be used so a Large Language Model can generate an analysis of the brain wave data.

    This function only supports 40 channels AURA data for the moment, a future implementation is expected to support
    Aura data with n channels.
    :param aura_data_file: A CSV file containing the aura data.
    :param aura_training_file: Optional CSV file containing the aura training data. If None, will use averages from aura_data_file.
    """
    aura_data = pd.read_csv(aura_data_file)
    if aura_data is None or aura_data.shape[1] != 41:
        raise RuntimeError("Only 40 channels AURA data is supported.")

    # Process Beta and Theta waves for each electrode
    waves = ['Beta', 'Theta']
    electrodes = ['F3', 'F4', 'Cz', 'C3', 'C4', 'Pz', 'P3', 'P4']

    # Drop unnecessary columns
    unnecessary_waves = ['Delta', 'Gamma', 'Alpha'] 
    for wave in unnecessary_waves:
        for electrode in electrodes:
            aura_data = aura_data.drop(columns=[wave + '_' + electrode])

    # Load training data if available, otherwise use self averages
    if aura_training_file:
        try:
            training_data = pd.read_csv(aura_training_file)
        except:
            training_data = aura_data
    else:
        training_data = aura_data

    # Normalize data using training/self averages
    for wave in waves:
        for electrode in electrodes:
            col_name = f'{wave}_{electrode}'
            # Calculate average from training data for this column
            training_avg = training_data[col_name].mean()
            if training_avg != 0:  # Avoid division by zero
                # Normalize the data by dividing by training average
                aura_data[col_name] = aura_data[col_name] / training_avg
    for wave in waves:
        for electrode in electrodes:
            beta_col_name = f'Beta_{electrode}'
            theta_col_name = f'Theta_{electrode}'
            concentration_col_name = f'ConcentrationIndex_{electrode}'
            aura_data[concentration_col_name] = aura_data[beta_col_name] / aura_data[theta_col_name]
    
    for wave in waves:
        for electrode in electrodes:
            aura_data = aura_data.drop(columns=[wave + '_' + electrode])

    for electrode in ['Cz', 'C3', 'C4']:
        aura_data = aura_data.drop(columns=[f'ConcentrationIndex_{electrode}'])

    aura_data.to_csv(aura_data_file, index=False)

