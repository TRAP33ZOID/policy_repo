import mysql.connector
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def create_sunburst():
    # Database connection configuration
    db_config = {
        'user': 'waleed@policy',
        'password': 'Trap3zoid',
        'host': 'policy.mysql.database.azure.com',
        'database': 'policy_azure'
    }

    # Establish a connection to the MySQL database
    conn = mysql.connector.connect(**db_config)

    # Function to fetch data from a table
    def fetch_data(table_name, column_name):
        cursor = conn.cursor()
        query = f"SELECT {column_name} FROM {table_name};"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return [item[0] for item in results]

    # Fetch data from each table
    events_data = fetch_data('events_data', 'event_name')
    property_excluded_data = fetch_data('property_excluded_data', 'property_name')
    personal_not_covered_data = fetch_data('personal_not_covered_data', 'item_name')
    events_not_covered_data = fetch_data('events_not_covered_data', 'event_name')

    #coverage & annual
    def fetch_coverage_annual(table_name, column_name):
        cursor = conn.cursor()
        query = f"SELECT {column_name} FROM {table_name};"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        # Join all the results into a single string separated by a space (or any other separator you prefer)
        return ' '.join([str(item[0]) for item in results])

    coverage = fetch_coverage_annual('coverage', 'total_coverage')
    annual = fetch_coverage_annual('annual', 'total_annual')

    # Fetch data for personal belongings as before
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name FROM personal_belongings;")
    personal_belongings_results = cursor.fetchall()
    cursor.close()
    personal_belongings_subcategories = [
        {"name": item_name, "parent": "Personal Belongings", "value": 3}
        for id, item_name in personal_belongings_results
    ]

    # Fetch hover data for personal belongings
    cursor = conn.cursor()
    cursor.execute("SELECT id, hover_data FROM hover;")
    hover_data_results = cursor.fetchall()
    cursor.close()

    # Create a dictionary for quick hover data retrieval
    hover_data_dict = {id: hover_data for id, hover_data in hover_data_results}

    # Update personal belongings subcategories to include hover data
    personal_belongings_subcategories = [
        {"name": item_name, "parent": "Personal Belongings", "value": 3, "hovertext": hover_data_dict.get(id)}
        for id, item_name in personal_belongings_results
    ]

    # Fetch dwelling address
    cursor = conn.cursor()
    cursor.execute("SELECT dwelling_address FROM dwelling WHERE id = 1;")
    dwelling_address_result = cursor.fetchone()
    cursor.close()

    dwelling_address = dwelling_address_result[0] if dwelling_address_result else "Address not found"



    # Close the main connection
    conn.close()

    centre = "total coverage: " + coverage + "<br>annual premium: " + annual
    # Data for the sunburst chart
    data = [
        {"name": centre, "parent": "", "value": 100},
        {"name": "home", "parent": centre, "value": 91},
        {"name": "life", "parent": centre, "value": 3},
        {"name": "car", "parent": centre, "value": 3},
        {"name": "business", "parent": centre, "value": 3},
        {"name": "Dwelling", "parent": "home", "value": 5},
        {"name": "Other Structures", "parent": "home", "value": 5},
        {"name": "Personal Belongings", "parent": "home", "value": 81},
        {"name": "Primary Dwelling", "parent": "Dwelling", "value": 2.5},
        {"name": "Construction Materials", "parent": "Dwelling", "value": 2.5},
        {"name": "Physically Separated Structures", "parent": "Other Structures", "value": 2.5},
        {"name": "Materials for Separated Structures", "parent": "Other Structures", "value": 2.5},
        # Personal Belongings subcategories
        
        # More subcategories can be added as needed
    ]

    # Update the 'Primary Dwelling' entry in the data list
    for item in data:
        if item['name'] == 'Primary Dwelling':
            item['hovertext'] = dwelling_address
            break

    # Integrate the fetched data into your existing sunburst data structure
    data.extend(personal_belongings_subcategories)

    # Create subplots with 4 rows and 2 columns
    fig = make_subplots(
        rows=4, cols=2,
        column_widths=[0.67, 0.33],
        
        specs=[
            [{"type": "sunburst", "rowspan": 4}, {"type": "table"}],
            [None, {"type": "table"}],
            [None, {"type": "table"}],
            [None, {"type": "table"}],
            
        ],
        vertical_spacing=0.02
    )

    # Update sunburst trace to include hover information
    sunburst = go.Sunburst(
        ids=[item["name"] for item in data],
        labels=[item["name"] for item in data],
        parents=[item["parent"] for item in data],
        values=[item["value"] for item in data],
        branchvalues="total",
        hoverinfo="label+text",
        hovertext=[item.get("hovertext", "") for item in data]
    )

    # Add the sunburst chart to the subplot
    fig.add_trace(sunburst, row=1, col=1)

    # Create and add the tables to the subplot
    events_table = go.Table(
        header=dict(values=["Events Covered"]),
        cells=dict(values=[events_data])
    )
    fig.add_trace(events_table, row=1, col=2)

    property_excluded_table = go.Table(
        header=dict(values=["Property not Covered"]),
        cells=dict(values=[property_excluded_data])
    )
    fig.add_trace(property_excluded_table, row=2, col=2)

    personal_not_covered_table = go.Table(
        header=dict(values=["Personal Belongings Not Covered"]),
        cells=dict(values=[personal_not_covered_data])
    )
    fig.add_trace(personal_not_covered_table, row=3, col=2)

    events_not_covered_table = go.Table(
        header=dict(values=["Events Not Covered"]),
        cells=dict(values=[events_not_covered_data])
    )
    fig.add_trace(events_not_covered_table, row=4, col=2)

    # Update layout
    fig.update_layout(
        title_text="Policy Dash",
        title_x=0.5,
        title_y=0.95,
        title_xanchor='center',
        # Other layout parameters
    )

    # Show plot
    #plot(fig)
    return fig
