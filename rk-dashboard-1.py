import pandas as pd
import numpy as np
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.layouts import column, row, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, FactorRange
from bokeh.palettes import Category10
from bokeh.models.widgets import Select, DatePicker


datafile1 = 'rk_data_cleaned.csv'
rk_data = pd.read_csv(datafile1, parse_dates=True, index_col='Date')

rk_data.loc[:, 'Duration'] = pd.to_datetime(rk_data['Duration'], format='%Y-%m-%d %H:%M:%S')
rk_data.loc[:, 'Average Pace'] = pd.to_datetime(rk_data['Average Pace'], format='%Y-%m-%d %H:%M:%S')

atypes = sorted(list(rk_data['Type'].unique()))  # List of all activity types
mapper = dict(list(zip(atypes, Category10[len(atypes)])))  # Map colors to types

rk_data['color'] = rk_data['Type'].map(mapper)  # Column with colors

my_num_axes = ['Distance (km)', 'Average Speed (km/h)', 'Climb (m)', 'Average Heart Rate (bpm)']
for_totals = ['Distance (km)', 'Climb (m)']
default_y_axis = 'Distance (km)'

src_nm = ColumnDataSource()
src_nm.data = {
    'x_ax': rk_data.index,
    'y_ax': rk_data[default_y_axis],
    'average_speed': rk_data['Average Speed (km/h)'],
    'duration': rk_data['Duration'],
    'average_pace': rk_data['Average Pace'],
    'distance': rk_data['Distance (km)'],
    'climb': rk_data['Climb (m)'],
    'ahr': rk_data['Average Heart Rate (bpm)'],
    'type': rk_data['Type'],
    'col': rk_data['color'],
}

hvr = HoverTool()
tooltip_main = [
    ('Activity', '@type'),
    ('Date', '@x_ax{%a %b %d %Y}'),
    ('Distance', '@distance{0.00} km'),
    ('Duration', '@duration{%H:%M:%S}'),
    ('Average Pace', '@average_pace{%M:%S}')
]
current_tooltip = [('Average Speed', '@average_speed{0.00} km/h')]
hvr.tooltips = tooltip_main + current_tooltip

hvr.formatters = {
    'x_ax': 'datetime',
    'duration': 'datetime',
    'average_pace': 'datetime',
}

toolbox = ['pan', 'box_zoom', 'reset', 'crosshair', hvr]

plot1 = figure(plot_width=700,
               x_axis_label='Date',
               x_axis_type='datetime',
               tools=toolbox,
               toolbar_location='above',
               background_fill_color='#bbbbbb',
               border_fill_color="whitesmoke",
               )

plot1.yaxis.axis_label = default_y_axis
title_main = 'Training activities historical data: '
plot1.title.text = title_main + default_y_axis

plot1.circle(x='x_ax', y='y_ax', source=src_nm,
             size=5,
             color='col',
             legend='type'
             )

plot1.legend.location = 'top_left'
# plot1.legend.click_policy = "mute"

"""
Plot2: bar chart for number of activities for selected period
"""
grouped = rk_data.groupby('Type')
aggregates = grouped[default_y_axis].agg([np.sum, np.max, np.mean, np.std])
counts = grouped.count()[default_y_axis]
joined = pd.concat([counts, aggregates], axis=1, join='outer')

src_cat = ColumnDataSource()

src_cat.data['Type'] = grouped.count().index
src_cat.data['count'] = counts
src_cat.data['color'] = grouped.count().index.map(mapper)
src_cat.data['total'] = joined['sum']
src_cat.data['max'] = joined['amax']
src_cat.data['mean'] = joined['mean']
src_cat.data['std'] = joined['std']

hvr2 = HoverTool()
hvr2.tooltips = [
    ('Events', '@count{0}'),
    ('Totals', '@total{0.00}'),
    ('Max', '@max{0.00}'),
    ('Mean', '@mean{0.00}'),
    ('St. dev', '@std{0.00}'),
]

plot2 = figure(x_range=FactorRange(factors=atypes),
               plot_height=250,
               plot_width=290,
               title="Activity stats for selected period",
               toolbar_location=None,
               tools=[hvr2],
               )

plot2.vbar(x='Type',
           top='count',
           width=0.9,
           fill_color='color',
           line_color='color',
           source=src_cat,
           )

plot2.xgrid.grid_line_color = None
plot2.y_range.start = 0


def update_plot1(attr, old, new):
    """
    Define the callback: update_plot
    """

    y = menu1.value
    plot1.yaxis.axis_label = y

    d_from = menu2.value
    d_to = menu3.value

    """
    Set new_data for plot1 - historical data
    """
    new_data1 = {
        'x_ax': rk_data.loc[d_to:d_from].index,
        'y_ax': rk_data.loc[d_to:d_from][y],
        'duration': rk_data.loc[d_to:d_from]['Duration'],
        'average_speed': rk_data.loc[d_to:d_from]['Average Speed (km/h)'],
        'average_pace': rk_data.loc[d_to:d_from]['Average Pace'],
        'distance': rk_data.loc[d_to:d_from]['Distance (km)'],
        'climb': rk_data.loc[d_to:d_from]['Climb (m)'],
        'ahr': rk_data.loc[d_to:d_from]['Average Heart Rate (bpm)'],
        'type': rk_data.loc[d_to:d_from]['Type'],
        'col': rk_data.loc[d_to:d_from]['color'],
    }

    src_nm.data = new_data1  # Assign new_data to ColumnDataSource object

    # Set the range of all axes
    low = min(src_nm.data['y_ax'])
    top = plot1.y_range.end = max(src_nm.data['y_ax'])*1.03
    plot1.y_range.start = min(src_nm.data['y_ax']) - (top - low)*0.02  # Decrease bottom to 2% of total range

    plot1.title.text = title_main + y  # Add title to plot

    #  Set new tooltips with selected parameter at the end, except distance, which is displayed always
    if y != "Distance (km)":
        hvr.tooltips = tooltip_main + [(y, '@y_ax{0.00}')]
    else:
        hvr.tooltips = tooltip_main

    """
    Set new data for categorical bar plot 2 - statistic of activities
    """
    new_types = sorted(list(rk_data.loc[d_to:d_from]['Type'].unique()))
    new_factors = FactorRange(factors=new_types)

    new_grouped = rk_data.loc[d_to:d_from].groupby('Type')
    new_aggregates = new_grouped[y].agg([np.sum, np.mean, np.max, np.std])
    new_counts = new_grouped[y].count()
    new_joined = pd.concat([new_counts, new_aggregates], axis=1, join='outer')

    new_data2 = {
        'Type': new_grouped.count().index,
        'count': new_counts,
        'color': new_grouped.count().index.map(mapper),
        'max': new_joined['amax'],
        'mean': new_joined['mean'],
        'std': new_joined['std'],
    }

    if y in for_totals:
        new_data2['total'] = new_joined['sum']
    else:
        new_data2['total'] = new_joined['sum']*0

    src_cat.data = new_data2

    plot2.x_range = new_factors
    plot2.y_range.start = 0
    plot2.y_range.end = max(rk_data.loc[d_to:d_from].groupby('Type').count()[default_y_axis])*1.02


menu1 = Select(options=my_num_axes, value=default_y_axis, title='Select plot to draw (numerals)')
menu2 = DatePicker(title='From:', value=src_nm.data['x_ax'].min())
menu3 = DatePicker(title='To:', value=src_nm.data['x_ax'].max())

menu1.on_change('value', update_plot1)
menu2.on_change('value', update_plot1)
menu3.on_change('value', update_plot1)

dates = column(
    widgetbox(menu2),
    widgetbox(menu3),
    plot2,
)
layout = row(column(widgetbox(menu1), dates), plot1)

# show(layout)
curdoc().add_root(layout)
