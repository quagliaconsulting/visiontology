import streamlit as st
import plotly.graph_objects as go
import yaml

# Function to load configuration from YAML file
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config

# Load configuration
config = load_config('config.yaml')

# Function to calculate required camera precision and recall
def calculate_camera_metrics(max_fp_rate, max_fn_rate, num_cameras, overlap_factor):
    camera_fp_rate = max_fp_rate / 100  # False positives are not affected by overlap
    adjusted_cameras = num_cameras / overlap_factor
    camera_fn_rate = 1 - (1 - max_fn_rate / 100) ** (1 / adjusted_cameras)
    required_camera_precision = 100 - camera_fp_rate * 100
    required_camera_recall = 100 - camera_fn_rate * 100
    return required_camera_precision, required_camera_recall

# Function to calculate effective recall with overlap
def calculate_effective_recall(current_recall, overlap_factor):
    fn_rate = 1 - current_recall / 100
    effective_fn_rate = fn_rate ** overlap_factor
    effective_recall = (1 - effective_fn_rate) * 100
    return effective_recall

# Function to simulate the financial impact
def calculate_financial_impact(defect_rate, production_rate, max_fp_rate, max_fn_rate, cost_impact_fp, cost_impact_fn, hours_per_day):
    daily_production = production_rate * hours_per_day  # Convert hourly rate to daily rate
    expected_defects = (defect_rate / 100) * daily_production
    
    false_positives = (max_fp_rate / 100) * daily_production
    false_negatives = (max_fn_rate / 100) * expected_defects
    
    cost_fp = false_positives * cost_impact_fp
    cost_fn = false_negatives * cost_impact_fn
    total_cost = cost_fn - cost_fp
    
    return total_cost, cost_fp, cost_fn, false_positives, false_negatives

# Function to calculate the financial impact without the system
def calculate_impact_without_system(defect_rate, production_rate, cost_impact_fn, current_inspection_rate, hours_per_day):
    daily_production = production_rate * hours_per_day  # Convert hourly rate to daily rate
    expected_defects = (defect_rate / 100) * daily_production
    caught_defects = expected_defects * (current_inspection_rate / 100)
    uncaught_defects = expected_defects - caught_defects
    cost_without_system = uncaught_defects * cost_impact_fn
    
    return cost_without_system, caught_defects, uncaught_defects

# Function to calculate time to ROI
def calculate_time_to_roi(system_cost, recurring_cost, daily_savings, time_horizon_months):
    monthly_recurring_cost = recurring_cost / 12
    monthly_savings = daily_savings * 30  # Assume 30 days in a month for simplicity
    cumulative_costs = [system_cost + monthly_recurring_cost * month for month in range(time_horizon_months + 1)]
    cumulative_savings = [monthly_savings * month for month in range(time_horizon_months + 1)]
    roi = [cumulative_savings[month] - cumulative_costs[month] for month in range(time_horizon_months + 1)]
    return cumulative_costs, cumulative_savings, roi

# Home Page
st.title("Machine Vision Application Simulator")
st.write("Welcome to the Machine Vision Application Simulator. Please follow the steps to input your application's details.")

# Sidebar for inputs
st.sidebar.header("Input Form")

# Customer's Process Overview
st.sidebar.subheader("Customer's Process Overview")
application_type = st.sidebar.text_input("Type of Application", value=config['application']['type'])
process_description = st.sidebar.text_area("Process Description", value=config['application']['process_description'])
current_defect_rate = st.sidebar.number_input("Current Defect Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['application']['current_defect_rate'])
production_rate = st.sidebar.number_input("Production Rate (parts per hour)", min_value=1, step=1, value=config['application']['production_rate'])
current_inspection_rate = st.sidebar.number_input("Current Inspection Defect Detection Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['application'].get('current_inspection_rate', 0))
hours_per_day = st.sidebar.number_input("Working Hours per Day", min_value=1, step=1, value=18)

# Customer's Expectations
st.sidebar.subheader("Customer's Expectations")
max_fp_rate = st.sidebar.number_input("Max False Positive Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['expectations']['max_fp_rate'])
max_fn_rate = st.sidebar.number_input("Max False Negative Rate (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['expectations']['max_fn_rate'])
cost_impact_fp = st.sidebar.number_input("Cost Impact of False Positives ($)", min_value=0.0, step=0.1, value=config['expectations']['cost_impact_fp'])
cost_impact_fn = st.sidebar.number_input("Cost Impact of False Negatives ($)", min_value=0.0, step=0.1, value=config['expectations']['cost_impact_fn'])

# Implementation Details
st.sidebar.subheader("Implementation Details")
system_cost = st.sidebar.number_input("System Cost ($)", min_value=0.0, step=0.1, value=config['implementation']['system_cost'])
num_cameras = st.sidebar.number_input("Number of Cameras", min_value=1, step=1, value=config['implementation']['num_cameras'])
overlap_factor = st.sidebar.number_input("Overlap Factor (number of cameras covering the same area)", min_value=1, step=1, value=config['implementation'].get('overlap_factor', 1))
recurring_cost = st.sidebar.number_input("Recurring Cost ($/year)", min_value=0.0, step=0.1, value=config['implementation']['recurring_cost'])
time_horizon_months = st.sidebar.number_input("Time Horizon (months)", min_value=1, step=1, value=config['implementation']['time_horizon']*12)
production_days_per_year = st.sidebar.number_input("Production Days per Year", min_value=1, step=1, value=config['application']['production_days_per_year'])

# Current Model Performance
st.sidebar.subheader("Current Model Performance")
current_precision = st.sidebar.number_input("Current Precision (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['current_performance']['current_precision'])
current_recall = st.sidebar.number_input("Current Recall (%)", min_value=0.0, max_value=100.0, step=0.1, value=config['current_performance']['current_recall'])
num_images = st.sidebar.number_input("Number of Images Used", min_value=1, step=1, value=config['current_performance']['num_images'])

# Calculate Required Camera Precision and Recall
required_camera_precision, required_camera_recall = calculate_camera_metrics(max_fp_rate, max_fn_rate, num_cameras, overlap_factor)

# Calculate Effective Recall with Overlap
effective_recall = calculate_effective_recall(current_recall, overlap_factor)

st.markdown("### Calculations")

# 1. Adjusted Number of Cameras
st.latex(r'''
\text{Adjusted Number of Cameras} = \frac{\text{Total Number of Cameras}}{\text{Overlap Factor}}
''')

# 2. Camera False Positive Rate
st.latex(r'''
\text{Camera False Positive Rate} = \frac{\text{Max False Positive Rate}}{100}
''')

# 3. Camera False Negative Rate
st.latex(r'''
\text{Camera False Negative Rate} = 1 - \left(1 - \frac{\text{Max False Negative Rate}}{100}\right)^{\frac{1}{\text{Adjusted Number of Cameras}}}
''')

# 4. Required Camera Precision
st.latex(r'''
\text{Required Camera Precision (\%)} = 100 - \text{Camera False Positive Rate} \times 100
''')

# 5. Required Camera Recall
st.latex(r'''
\text{Required Camera Recall (\%)} = 100 - \text{Camera False Negative Rate} \times 100
''')

# 6. Effective Recall with Overlap
st.latex(r'''
\text{Effective Recall with Overlap} = 1 - \left(1 - \frac{\text{Current Recall}}{100}\right)^{\text{Overlap Factor}}
''')

# 7. Expected Defects
st.latex(r'''
\text{Expected Defects} = \frac{\text{Current Defect Rate} \times \text{Production Rate}}{100}
''')

# 8. False Positives
st.latex(r'''
\text{False Positives} = \frac{\text{Max False Positive Rate} \times \text{Production Rate}}{100}
''')

# 9. False Negatives
st.latex(r'''
\text{False Negatives} = \frac{\text{Max False Negative Rate} \times \text{Expected Defects}}{100}
''')

# 10. Cost of False Positives
st.latex(r'''
\text{Cost of False Positives} = \text{False Positives} \times \text{Cost Impact of False Positives}
''')

# 11. Cost of False Negatives
st.latex(r'''
\text{Cost of False Negatives} = \text{False Negatives} \times \text{Cost Impact of False Negatives}
''')

# 12. Total Cost
st.latex(r'''
\text{Total Cost} = \text{Cost of False Negatives} - \text{Cost of False Positives}
''')

# 13. Cost Without System
st.latex(r'''
\text{Cost Without System} = \left(\frac{\text{Current Defect Rate}}{100} \times \text{Production Rate} \times (1 - \frac{\text{Current Inspection Rate}}{100})\right) \times \text{Cost Impact of False Negatives}
''')

# 14. Daily Savings
st.latex(r'''
\text{Daily Savings} = \text{Cost Without System} - \text{Total Financial Impact}
''')

# 15. Cumulative Costs (Month m)
st.latex(r'''
\text{Cumulative Costs (Month m)} = \text{System Cost} + \left(\frac{\text{Recurring Cost}}{12} \times m\right)
''')

# 16. Cumulative Savings (Month m)
st.latex(r'''
\text{Cumulative Savings (Month m)} = \text{Daily Savings} \times 30 \times m
''')

# 17. ROI (Month m)
st.latex(r'''
\text{ROI (Month m)} = \text{Cumulative Savings (Month m)} - \text{Cumulative Costs (Month m)}
''')

# Run Simulation Button
if st.sidebar.button("Run Simulation"):

    # Display Required Camera Precision and Recall
    st.subheader("Required Camera Precision and Recall")
    st.write(f"Required Camera Precision: {required_camera_precision:.2f}%")
    st.write(f"Required Camera Recall: {required_camera_recall:.2f}%")
    st.write(f"Effective Recall with Overlap: {effective_recall:.2f}%")

    total_cost, cost_fp, cost_fn, false_positives, false_negatives = calculate_financial_impact(
        current_defect_rate, production_rate, max_fp_rate, max_fn_rate, cost_impact_fp, cost_impact_fn, hours_per_day)
    
    cost_without_system, caught_defects, uncaught_defects = calculate_impact_without_system(
        current_defect_rate, production_rate, cost_impact_fn, current_inspection_rate, hours_per_day)
    
    daily_savings = cost_without_system - total_cost
    annual_savings = daily_savings * production_days_per_year
    
    cumulative_costs, cumulative_savings, roi = calculate_time_to_roi(system_cost, recurring_cost, daily_savings, time_horizon_months)

    st.header("Results")
    
    st.subheader("Financial Impact")
    col1, col2 = st.columns(2)
    
    expected_defects = (current_defect_rate / 100) * production_rate * hours_per_day  # Ensure this is calculated here for display
    
    with col1:
        st.write("### Without System")
        st.write(f"Expected Defects: {expected_defects:.2f}")
        st.write(f"Caught Defects: {caught_defects:.2f}")
        st.write(f"Uncaught Defects: {uncaught_defects:.2f}")
        st.write(f"Cost Without System: ${cost_without_system:.2f} per day")
        
    with col2:
        st.write("### With System")
        st.write(f"False Positives: {false_positives:.2f}")
        st.write(f"False Negatives: {false_negatives:.2f}")
        st.write(f"Cost Due to False Positives: ${cost_fp:.2f} per day")
        st.write(f"Cost Due to False Negatives: ${cost_fn:.2f} per day")
        st.write(f"Total Financial Impact: ${total_cost:.2f} per day")
        
    st.write("### Delta")
    st.write(f"Cost Saving: ${daily_savings:.2f} per day")

    # Visualizations with Plotly
    st.subheader("Graphs and Visualizations")
    fig_cost_comparison = go.Figure()
    
    months = list(range(time_horizon_months + 1))
    
    fig_cost_comparison.add_trace(go.Scatter(x=months, y=[cost_without_system * 30 * month for month in months], 
                                             mode='lines', name='Cost Without System'))
    fig_cost_comparison.add_trace(go.Scatter(x=months, y=[cumulative_costs[month] + total_cost * 30 for month in months], 
                                             mode='lines', name='Cost With System'))

    fig_cost_comparison.update_layout(title="Cost Comparison Over Time (Monthly)",
                                      xaxis_title="Month",
                                      yaxis_title="Cost ($)")
    
    st.plotly_chart(fig_cost_comparison)

    # Bold statement for happy customer check
    if any(month < 18 and roi[month] > 0 for month in months):
        st.markdown("**Congratulations! Your customer will be happy since the ROI is less than 18 months.**")
    else:
        st.markdown("**The ROI exceeds 18 months. The customer may not be fully satisfied.**")

    # Performance gap analysis
    precision_gap = required_camera_precision - current_precision
    recall_gap = required_camera_recall - effective_recall
    
    st.subheader("Performance Gap Analysis")
    st.write(f"Precision Gap: {precision_gap:.2f}%")
    st.write(f"Recall Gap: {recall_gap:.2f}%")
    
    # Suggestions for improvement
    if precision_gap > 0:
        st.write("### Suggestions to Improve Precision")
        st.write("1. Increase the quality of training data by removing mislabeled images.")
        st.write("2. Use data augmentation techniques to enhance the dataset.")
        st.write("3. Implement advanced algorithms and second stage result filtering techniques.")
        st.write("4. Reduce the class imbalance by adding more samples of the minority class.")

    if recall_gap > 0:
        st.write("### Suggestions to Improve Recall")
        st.write("1. Increase the variety of training data to cover more scenarios.")
        st.write("2. Improve the labeling accuracy of the training data.")
        st.write("3. Consider adding overlapping cameras to improved effective recall")
        st.write("3. Research using ensemble methods to improve recall.")
        st.write("4. Adjust the decision threshold to favor recall over precision, if appropriate.")
