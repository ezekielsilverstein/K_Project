import pandas as pd
from argparse import ArgumentParser
import numpy as np
import matplotlib.pyplot as plt
import pylab


def read_standard_csv(filename='stats_csvs/2012_Standard_Batting.csv'):
    """
    Read in Standard Batting csv
    :param filename: 
    :return: pandas df
    """

    # Import the CSV, skipping the league average row at the bottom
    standard_raw = pd.read_csv(filename, skipfooter=1, engine='python')

    # Add column to dataframe with unique name identifier
    unique_name_id = lambda x: x.split('\\')[1]
    standard_raw['ID'] = standard_raw.loc[:, 'Name'].apply(unique_name_id)

    # Fix Pos Summary Column
    # Rename the column
    standard_raw = standard_raw.rename(
        index=str, columns={'Pos Summary': 'Position',
                            'Pos\xc2\xa0Summary': 'Position'})
    # Get the first designated position (one played most often)
    clean_position = lambda x: x.replace('*', '').replace('/', '')[0]
    standard_raw['Position'] = standard_raw['Position'].astype(str).apply(clean_position)

    # clean names
    clean_name = lambda x: x.replace('\xc2\xa0', ' ').split('\\')[0].replace('*', '').replace('#', '')
    names = list(standard_raw.loc[:, 'Name'].apply(clean_name))
    standard_raw['Name'] = standard_raw['Name'].apply(clean_name)

    # Create ID:Name dict
    id_name_df = pd.DataFrame.from_dict(dict(zip(standard_raw.ID, standard_raw.Name)), 'index')
    id_name_df = id_name_df.rename(index=str, columns={0: 'Name'})

    # Create ID:Position dict
    shaved_df = standard_raw[['ID', 'Position', 'Tm', 'Lg', 'G', 'PA', 'AB', 'BB', 'HBP', 'SH', 'SF', 'IBB']]
    # Get singular rows (no cumulative rows where a player played for multiple teams)
    no_tot = shaved_df[shaved_df.Tm != 'TOT']
    # Remove rows where there is no positional information
    non_null_pos = no_tot[no_tot['Position'] != 'n']
    # Create the dictionary
    id_position_dict = {}
    for uniq_id in non_null_pos.ID.unique():
        primary_position = (str(
            non_null_pos.loc[
                (
                    (non_null_pos.PA == non_null_pos.groupby('ID')['PA'].max().loc[uniq_id])
                    &
                    (non_null_pos.ID == uniq_id)
                )
            ].Position.iloc[0]))
        id_position_dict[uniq_id] = primary_position

    # Make a dataframe out of the dictionary and rename the column
    id_position_df = pd.DataFrame.from_dict(id_position_dict, 'index')
    id_position_df = id_position_df.rename(index=str, columns={0: 'Position'})

    # Shave the df
    shaved_df = standard_raw[['ID', 'Position', 'Tm', 'Lg', 'G', 'PA', 'AB', 'BB', 'HBP', 'SH', 'SF', 'IBB']]
    # Get singular rows (no cumulative rows where a player played for multiple teams)
    no_tot = shaved_df[shaved_df.Tm != 'TOT']
    # Group the rows by ID and sum the values for totals over a season
    summed = no_tot.groupby(['ID']).sum()

    # Combine the summed dataframe with the player's name and primary position
    dfs = [summed, id_name_df, id_position_df]
    together = pd.concat(dfs, axis=1)

    # Reorder columns
    cols = ['Name', 'Position']
    for i in summed.columns:
        cols.append(i)

    standard_final = together[cols]

    return standard_final


def read_pitches_csv(filename='stats_csvs/2012_Pitches_Batting.csv'):
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
    Change the Position to 'PH' (pinch-hitter) if the player has <100 PAs on the season
    :param standard: dataframe of standard_batting
    :param pitches: dataframe of pitches_batting
    :return: concatenated dataframe
    """

    joined = pd.concat([standard, pitches], axis=1, join='inner')

    joined.loc[((joined['PA'] < 100) & (joined['Position'] != '1')), 'Position'] = 'PH'

    return joined

def groupby(joined):
    """
    Group the player dataframe by positions and calculate
    :param joined: 
    :return: position dataframe
    """
    by_position = joined.groupby('Position').sum()
    by_position['TPAa'] = by_position[['AB', 'BB', 'SH', 'SF']].sum(axis=1)
    by_position['L/SO%%'] = by_position['L/SO'] / by_position['TPAa']
    by_position.sort_values('L/SO%%', inplace=True)

    return by_position

def yearly_stats(year, pos_exclusions):
    """
    Take a year and return the rankings by position
    :param year: 
    :return: 
    """

    print "Reading stats from {}".format(year)

    standard_fname = 'stats_csvs/{}_Standard_Batting.csv'.format(year)
    pitching_fname = 'stats_csvs/{}_Pitches_Batting.csv'.format(year)
    standard = read_standard_csv(standard_fname)
    pitches = read_pitches_csv(pitching_fname)
    joined = concat(standard, pitches)
    by_position = groupby(joined)

    by_position = by_position.loc[~by_position.index.isin(pos_exclusions)]

    return by_position

def years_in_question(start, end):
    """
    Make list of years for which to look at data
    :param start: int start year
    :param end: int end year
    :return: list
    """
    years = [yr for yr in range(start, end+1)]
    return years

def create_concatenation(years, excluded_positions):
    """
    
    :param years: list of years 
    :param excluded_positions: list of excluded positions
    :return: concatenated dataframe of individual dataframes for each year,
    a dictionary of K-looking rates by year with positions as keys,
    a Series of average K-looking rates over the years by position,
    a dictionary of Standard Deviations based around the positional average
    """

    dfs = dfs = {yr: yearly_stats(yr, excluded_positions) for yr in years}
    concatenated = pd.concat(dfs, keys=range(min(dfs.keys()), max(dfs.keys()) + 1), names=['Year', 'Position'])

    positional_year_by_year = {
        pos: concatenated.xs(pos, level='Position')['L/SO%%']
        for pos in concatenated.loc[args.start_year].index
    }

    year_totals = concatenated.groupby(['Position']).sum()
    year_totals['L/SO%%'] = year_totals['L/SO'] / year_totals['TPAa']
    year_totals.sort_values('L/SO%%', inplace=True)
    total_rates = year_totals['L/SO%%']

    stdev = {
        pos: (sum((concatenated.xs(pos, level='Position')['L/SO%%'] - total_rates[pos])**2)/len(years))**0.5
        for pos in concatenated.loc[args.start_year].index
    }

    return concatenated, positional_year_by_year, total_rates, stdev

def plot(positional_year_by_year, stdev, ebars):
    """
    
    :param positional_year_by_year: 
    :param stdev: 
    :return: 
    """
    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    for pos, rate in positional_year_by_year.iteritems():
        if len(years) == 1:
            ax1.scatter(rate.index, rate, label="{} -- {}%".format(pos, 100.0 * round(rate.mean(), 4)))
        elif len(years) > 1:
            if ebars:
                ax1.errorbar(rate.index, rate, yerr=stdev[pos], capsize=10,
                             label="{} -- {}%".format(pos, 100.0 * round(rate.mean(), 4)))
                ax1.fill_between(rate.index, rate - stdev[pos], rate + stdev[pos], alpha=0.1, linestyle='--')
            else:
                ax1.errorbar(rate.index, rate,
                             label="{} -- {}%".format(pos, 100.0 * round(rate.mean(), 4)))

    ax1.set_title('Positional K Looking Rate\n(Total average in legend)')
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Strikeout Looking PCT')
    ax1.set_xlim(min(years), max(years))
    ax1.legend(loc='lower center', ncol=len(positional_year_by_year) / 2, fontsize='small')

    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())

    plt.show()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-s", "--start_year",
                        type=int, default=2007,
                        help="First year to begin looking at data")
    parser.add_argument("-e", "--end_year",
                        type=int, default=2016,
                        help="Last year to look at data")
    parser.add_argument("--excluded_positions", default = [], nargs='+',
                        help=("Positions to be excluded from analysis."
                              "Options must be 1-9, PH or DH"))
    parser.add_argument("--errorbars",
                        action='store_true', default=False,
                        help="Include errorbars (default=False)")

    args = parser.parse_args()

    years = years_in_question(args.start_year, args.end_year)

    concatenated, positional_year_by_year, total_rates, stdev = create_concatenation(years, args.excluded_positions)

    plot(positional_year_by_year, stdev, args.errorbars)
