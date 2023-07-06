import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
import dash  
from dash import html, dcc, html
from datetime import datetime, timedelta
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import itertools
import subprocess


# Constants
KEY_FILE_LOCATION = 'F:/zimme/Documents/Branched Roots/Dashboard/dashb/analytics/scottsdale-390303-2debe1a0bf89.json'
PROPERTY_ID = '387948176'
METRICS = [
    'totalUsers',
    'newUsers',
    'sessions',
    'engagementRate',
    'averageSessionDuration',
    'userConversionRate',
    'wauPerMau'
]
DIMENSIONS = [
    Dimension(name='country'),
    Dimension(name='region'),
    Dimension(name='city'),
    Dimension(name='continent'),
    Dimension(name='date')
]
CUSTOM_TITLES = [
    'Total Users',
    'New Users',
    'Sessions',
    'Engagement Rate',
    'Average Session Duration',
    'User Conversion Rate',
    'WAU/MAU Ratio'
]
CUSTOM_DESCRIPTIONS = [
    'Total Users: This represents the total number of unique users who have performed at least one action or event on our platform, whether its on our website or app. This count includes all activities, even if the user was not actively using the site or app when the event was logged. This metric gives us a comprehensive view of our user base and their level of activity.',
    'New Users: This refers to the number of individuals who have interacted with our website or used our app for the very first time. We identify these users when they trigger a first_open or first_visit event. This metric helps us understand how many new people are discovering and engaging with our platform.',
    'Sessions: This refers to the number of times users have started a session on our website or app. A session begins when a user initiates an interaction with our platform, which is marked by triggering a session_start event. This metric helps us understand how frequently our platform is being accessed by users.',
    'Engagement Rate: This is a measure of how engaging our platform is to our users. It is calculated by dividing the number of engaged sessions by the total number of sessions. For instance, a rate of 0.7239 means that "72.39%" of all sessions were engaged sessions. This helps us understand how effectively our platform is capturing and maintaining user interest.',
    'Average Session Duration: This refers to the average amount of time, measured in seconds, that users spend in a single session on our platform. It gives us an idea of how long users typically stay engaged during each visit.',
    'User Conversion Rate: This is the percentage of our users who have completed a desired action or conversion event on our platform. This could include actions like making a purchase signing up for a newsletter or any other goal we have set. This metric helps us understand how effectively we are persuading users to take these desired actions.',
    'WAU/MAU Ratio: This is a measure of how engaged our users are with our platform. It tells us what percentage of our users who visited at least once in the past 30 days (Monthly Active Users or MAU) also visited at least once in the past 7 days (Weekly Active Users or WAU).For instance, a ratio of 0.234 means that "23.4%" of our users who visited in the last month also visited in the last week. This helps us understand how regularly our users are interacting with our platform.'
]
def get_date_days_ago(days):
    """Returns the date a certain number of days ago."""
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

def create_header():
    """Creates a header with the company logo and name."""
    return html.Div([
        html.Img(src='/assets/Branched-Roots-Logo.png', style={'height':'10%', 'width':'10%'}),  # Adjust the path and size as needed
        html.H1('Branched Roots', style={'font-family': 'Quicksand', 'color': '#1D2327'}),
        html.H2('Client: ScottsDale Entertainers ' + PROPERTY_ID, style={'font-family': 'Quicksand', 'color': '#1D2327'})  # Replace with the actual client name
    ])

def create_graphs(data):
    """Creates a separate graph for each metric."""
    graphs = []
    for i in range(len(METRICS)):
        x_values = [datetime.strptime(row['date'], '%Y%m%d').strftime('%Y-%m-%d') for row in data['totals']]
        y_values = [float(row['values'][i]) for row in data['totals']]

        fig = go.Figure(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                name=METRICS[i],
                line={'width': 2, 'color': '#0b3c5e'},
                marker={'size': 10, 'color': '#891A3A'}
            )
        )

        # Add annotations for each point
        annotations = [
            dict(
                x=x_values[j],
                y=y_values[j],
                text=str(y_values[j]),
                showarrow=False,
                font=dict(
                    size=18,  # Increase the font size
                    color='#1D2327',
                    family="Quicksand"  # Use Quicksand font
                ),
                yshift=10  # Shift the text upwards
            ) for j in range(len(x_values))
        ]

        # Add title
        title = CUSTOM_TITLES[i]
        if METRICS[i] == 'totalUsers':
            # Calculate the percentage change in total users
            first_day_users = float(data['totals'][0]['values'][i])
            last_day_users = float(data['totals'][-2]['values'][i])
            change = ((last_day_users - first_day_users) / first_day_users) * 100
            # Add the percentage change to the title
            title += " (change: " + "{:.2f}".format(change) + "%)"

        fig.update_layout(
            title=title,
            annotations=annotations,
            plot_bgcolor='#eef2f6',
            paper_bgcolor='#ffffff',
            font=dict(size=26, family="Quicksand", color='#1D2327'),
            xaxis=dict(tickfont=dict(size=18, family="Quicksand", color='#1D2327')),
            yaxis=dict(tickfont=dict(size=18, family="Quicksand", color='#1D2327'))
        )

        # Add the graph and its description to the list of graphs
        description = CUSTOM_DESCRIPTIONS[i]
        graphs.append(html.Div([
            dcc.Graph(id=f'line-graph-{i}', figure=fig),
            html.P(description, style={'font-family': 'Quicksand', 'color': '#1D2327', 'textAlign': 'center', 'fontSize': 16})  # Add the description below the graph
        ]))

    return graphs

def create_run_report_request(start_date, end_date, dimensions=DIMENSIONS, metrics=METRICS):
    """Creates a RunReportRequest for the given date range."""
    return RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        dimensions=dimensions,
        metrics=[Metric(name=metric) for metric in metrics]
    )

def get_report(start_date, end_date):
    """Queries the Google Analytics Data API and returns the response."""
    client = BetaAnalyticsDataClient.from_service_account_file(KEY_FILE_LOCATION)

    request = create_run_report_request(start_date, end_date, dimensions=[Dimension(name='date')])

    response = client.run_report(request)

    # Convert the response to a format that matches your existing code
    result = {
        'totals': [
            {
                'date': row.dimension_values[0].value,
                'values': [value.value for value in row.metric_values]
            } for row in response.rows
        ]
    }

    return result


def calculate_increase(current_data, previous_data, metric_index):
    """Calculates the month-to-month increase for a specific metric."""
    if not current_data['totals'] or not previous_data['totals']:
        return 0

    current_value = int(current_data['totals'][0]['values'][metric_index])
    previous_value = int(previous_data['totals'][0]['values'][metric_index])

    if previous_value == 0:
        return 0

    increase = (current_value - previous_value) / previous_value * 100
    return increase


def run_lighthouse_audit(url):
    """Runs a Lighthouse audit on the given URL and returns the results."""
    result = subprocess.run(['C:\\Users\\zimme\\AppData\\Roaming\\npm\\lighthouse.cmd', url, '--output=json'], capture_output=True)
    
    # Check if the Lighthouse audit was successful
    if result.returncode != 0:
        raise Exception(f"Lighthouse audit failed with error code {result.returncode}: {result.stderr.decode('utf-8')}")
    
    results = json.loads(result.stdout)
    return results

def save_lighthouse_results(url, filename):
    """Runs a Lighthouse audit and saves the results to a file."""
    results = run_lighthouse_audit(url)
    with open(filename, 'w') as f:
        json.dump(results, f)

def load_lighthouse_results(filename):
    """Loads the Lighthouse results from a file."""
    try:
        with open(filename) as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load Lighthouse results: {e}")
        exit(1)
    
def create_lighthouse_gauges(results, data):
    """Creates a Dash gauge chart for each Lighthouse category."""
    if 'categories' not in results:
        raise KeyError('categories key not found in results dictionary')

    categories = results['categories']

    gauges = []
    for category in categories:
        score = categories[category]['score'] * 100  # Convert score to a percentage

        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={'text': category},
            gauge={'axis': {'range': [0, 100]}}
        ))

        gauges.append(dcc.Graph(figure=gauge))

    # Create the header and graphs
    header = create_header()
    graphs = create_graphs(data)

    # Create the layout
    app.layout = html.Div([header] + gauges + graphs, style={'backgroundColor': '#ffffff', 'font-family': 'Quicksand', 'color': '#1D2327'})

    return app

def create_lighthouse_table(results):
    """Creates a Dash table that displays the Lighthouse scores."""
    if 'categories' not in results:
        raise KeyError('categories key not found in results dictionary')

    categories = results['categories']

    table_header = [
        html.Thead(html.Tr([html.Th('Category'), html.Th('Score')]))
    ]
    table_body = [
        html.Tbody([html.Tr([html.Td(category), html.Td(categories[category]['score'])]) for category in categories])
    ]

    # Add individual audits
    for category in categories:
        for audit in categories[category]['auditRefs']:
            audit_id = audit['id']
            audit_score = results['audits'][audit_id]['score']
            table_body.append(html.Tr([html.Td(audit_id), html.Td(audit_score)]))

    return html.Table(table_header + table_body)

homepage_audit_results = load_lighthouse_results('lighthouse_results.json')




def setup_dash_app(data, lighthouse_results):
    """Sets up the Dash app and returns the layout as an HTML string."""
    app = dash.Dash(__name__)  
    
    if 'totals' not in data:
        raise KeyError("'totals' key not found in data dictionary")

    # Create the Lighthouse gauges
    lighthouse_gauges = create_lighthouse_gauges(homepage_audit_results, current_month_data)

    # Create the Lighthouse table
    lighthouse_table = create_lighthouse_table(lighthouse_results)

    # Sort the data by date
    data['totals'].sort(key=lambda row: row['date'])

    # Create a separate graph for each metric
    graphs = create_graphs(data)

    # Add a header with the company logo and name
    header = create_header()

    app.layout = html.Div([header, lighthouse_table] + lighthouse_gauges + graphs, style={'backgroundColor': '#ffffff', 'font-family': 'Quicksand', 'color': '#1D2327'})

    return app


# Main script
# Get the current date and the date one month ago
current_date = datetime.now().strftime('%Y-%m-%d')
one_month_ago = get_date_days_ago(30)
two_months_ago = get_date_days_ago(60)

# Get the Google Analytics data for the current and previous month
current_month_data = get_report(one_month_ago, current_date)
previous_month_data = get_report(two_months_ago, one_month_ago)

# Calculate the month-to-month increase for each metric
increases = [calculate_increase(current_month_data, previous_month_data, i) for i in range(len(METRICS))]

# Run the Lighthouse audit and save the results
try:
    save_lighthouse_results('https://www.scottsdaleentertainers.com', 'lighthouse_results.json')
except Exception as e:
    print(f"Failed to run Lighthouse audit: {e}")
    exit(1)

# Set up the Dash app
app = setup_dash_app(current_month_data, homepage_audit_results)

# Run the Dash server
app.run_server(debug=True)