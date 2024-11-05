import pandas as pd

def process_concentration_data(aura_data) -> None:
    """
    Process the aura data to calculate a concentration value. Also removes unnecessary data that is present in the
    CSV file. The data is encoded to represent a value from 0 to 1, where 0 is the lowest concentration and 1 is the
    highest concentration. The new data overwrites the old data in the CSV file.
    The data will be used so a Large Language Model can generate an analysis of the concentration data.

    This function only supports 40 channels AURA data for the moment, a future implementation is expected to support
    Aura data with n channels.
    :param aura_data: A pandas dataframe containing the aura data.
    """
    print(df.shape)
    if aura_data is None or df.shape[1] != 41:
        raise RuntimeError("Only 40 channels AURA data is supported.")

    # The data is processed to calculate the concentration value.
    unnecessary_waves = ['Delta', 'Theta', 'Alpha', 'Gamma']
    electrodes = ['F3', 'F4', 'Cz', 'C3', 'C4', 'Pz', 'P3', 'P4']
    for wave in unnecessary_waves:
        for electrode in electrodes:
            aura_data = aura_data.drop(columns=[wave + '_' + electrode])

    for electrode in electrodes:
        ch_name = 'Beta_' + electrode
        aura_data['Encoded_Beta_' + electrode] = aura_data[ch_name] / aura_data[ch_name].max()
    print(aura_data)
    aura_data.to_csv('processed_aura_data.csv', index=False)


df = pd.read_csv('test.csv')
process_concentration_data(df)
