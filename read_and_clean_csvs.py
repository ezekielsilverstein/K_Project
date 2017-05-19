import pandas as pd


def read_standard_csv(filename='2016_Standard_Batting.csv'):
    """
    Read in Standard Batting csv
    :param filename: 
    :return: pandas df
    """
    standard_raw = pd.read_csv(filename, skipfooter=1, engine='python')

    # Add column to dataframe with unique name identifier
    unique_name_id = lambda x: x.split('\\')[1]
    standard_raw['ID'] = standard_raw.loc[:, 'Name'].apply(unique_name_id)

    # Fix Pos Summary Column
    standard_raw = standard_raw.rename(index=str, columns={'Pos\xc2\xa0Summary': 'Pos_Summary'})
    clean_position = lambda x: x.replace('*', '').replace('/', '')[0]
    standard_raw['Pos_Summary'] = standard_raw['Pos_Summary'].astype(str).apply(clean_position)

    # clean names
    clean_name = lambda x: x.replace('\xc2\xa0', ' ').split('\\')[0].replace('*', '').replace('#', '')
    names = list(standard_raw.loc[:, 'Name'].apply(clean_name))
    standard_raw['Name'] = standard_raw['Name'].apply(clean_name)

    # Create ID:Name dict
    id_name_df = pd.DataFrame.from_dict(dict(zip(standard_raw.ID, standard_raw.Name)), 'index')
    id_name_df = id_name_df.rename(index=str, columns={0: 'Name'})

    # Create ID:Position dict
    id_position_df = pd.DataFrame.from_dict(dict(zip(standard_raw.ID, standard_raw.Pos_Summary)), 'index')
    id_position_df = id_position_df.rename(index=str, columns={0: 'Position'})

    # shave the df
    shaved_df = standard_raw[['ID', 'Tm', 'Lg', 'G', 'PA', 'AB', 'BB', 'HBP', 'SH', 'SF', 'IBB']]
    no_tot_shaved_df = shaved_df[shaved_df.Tm != 'TOT']
    summed = no_tot_shaved_df.groupby(['ID']).sum()

    dfs = [summed, id_name_df, id_position_df]

    together = pd.concat(dfs, axis=1)

    cols = ['Name', 'Position']
    for i in summed.columns:
        cols.append(i)

    standard_final = together[cols]

    return standard_final


def read_pitches_csv(filename='2016_Pitches_Batting.csv'):
    """
    Read in Pitches Batting CSV
    :param filename: 
    :return: pandas df
    """
    pitches_raw = pd.read_csv(filename, skipfooter=1, engine='python')

    # Add column to dataframe with unique name identifier
    unique_name_id = lambda x: x.split('\\')[1]
    pitches_raw['ID'] = pitches_raw['Name'].apply(unique_name_id)

    # clean names
    clean_name = lambda x: x.replace('\xc2\xa0', ' ').split('\\')[0].replace('*', '').replace('#', '')
    names = list(pitches_raw.loc[:, 'Name'].apply(clean_name))
    pitches_raw['Name'] = pitches_raw['Name'].apply(clean_name)

    # Create ID:Name dict
    id_name_df = pd.DataFrame.from_dict(dict(zip(pitches_raw.ID, pitches_raw.Name)), 'index')
    id_name_df = id_name_df.rename(index=str, columns={0: 'Name'})

    # shave the df
    shaved_df = pitches_raw[['ID', 'Tm', 'L/SO', 'S/SO']]
    no_tot_shaved_df = shaved_df[shaved_df.Tm != 'TOT']
    summed = no_tot_shaved_df.groupby(['ID']).sum()

    return summed


def concat(standard, pitches):
    """
    Combine the 2 dataframes on ID as index using inner join
    :param standard: dataframe of standard_batting
    :param pitches: dataframe of pitches_batting
    :return: concatenated dataframe
    """

    joined = pd.concat([standard, pitches], axis=1, join='inner')

    return joined
