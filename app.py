import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# Collegiate Athlete Injury Analysis Dashboard
# ---------------------------------------------------------

st.set_page_config(
    page_title="Athlete Performance & Injury Analysis",
    page_icon="🏅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown(
    """
    <style>
        .main {background-color: #f7f9fc;}
        [data-testid="stMetric"] {
            background-color: white;
            border: 1px solid #e6eaf0;
            padding: 15px;
            border-radius: 12px;
            color: #222222 !important;
        }

        [data-testid="stMetric"] label,
        [data-testid="stMetric"] [data-testid="stMetricLabel"],
        [data-testid="stMetric"] [data-testid="stMetricValue"],
        [data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #222222 !important;
        }
        div[data-testid="stTabs"] button {
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🏅 Collegiate Athlete Performance & Injury Analysis")
st.caption(
    "An interactive sports analytics dashboard to explore athlete characteristics, "
    "training patterns, performance and injury indicators."
)

# Load the dataset. Keep the CSV in the same folder as app.py.
@st.cache_data
def load_data():
    data = pd.read_csv("collegiate_athlete_injury_dataset.csv")
    numeric_columns = data.select_dtypes(include="number").columns
    data[numeric_columns] = data[numeric_columns].apply(
        pd.to_numeric, errors="coerce"
    )
    return data


try:
    df_original = load_data()
except FileNotFoundError:
    st.error("Dataset not found.")
    st.stop()
except Exception as error:
    st.error(f"Unable to read the dataset: {error}")
    st.stop()

if df_original.empty:
    st.error("The uploaded dataset is empty.")
    st.stop()

required_columns = {
    "Athlete_ID", "Age", "Gender", "Position", "Training_Intensity",
    "Training_Hours_Per_Week", "Recovery_Days_Per_Week",
    "Fatigue_Score", "Performance_Score", "ACL_Risk_Score",
    "Injury_Indicator"
}
missing_columns = required_columns.difference(df_original.columns)
if missing_columns:
    st.error(
        "The dataset is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

# ---------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------
st.sidebar.header("🔎 Filters")

filtered = df_original.copy()

def add_multiselect_filter(frame, column, label):
    values = sorted(frame[column].dropna().unique().tolist())
    selected = st.sidebar.multiselect(
        label, options=values, default=values, key=f"filter_{column}"
    )
    return frame[frame[column].isin(selected)]

for column, label in [
    ("Gender", "Gender"),
    ("Position", "Playing position")
]:
    filtered = add_multiselect_filter(filtered, column, label)

if "Age" in filtered.columns and filtered["Age"].notna().any():
    age_min = int(filtered["Age"].min())
    age_max = int(filtered["Age"].max())
    age_range = st.sidebar.slider(
        "Age range",
        min_value=age_min,
        max_value=age_max,
        value=(age_min, age_max)
    )
    filtered = filtered[filtered["Age"].between(*age_range)]

if "Training_Intensity" in filtered.columns and filtered["Training_Intensity"].notna().any():
    intensity_min = int(filtered["Training_Intensity"].min())
    intensity_max = int(filtered["Training_Intensity"].max())
    intensity_range = st.sidebar.slider(
        "Training intensity",
        min_value=intensity_min,
        max_value=intensity_max,
        value=(intensity_min, intensity_max)
    )
    filtered = filtered[
        filtered["Training_Intensity"].between(*intensity_range)
    ]

if "Injury_Indicator" in filtered.columns:
    injury_choice = st.sidebar.selectbox(
        "Injury status",
        ["All", "Injury indicated", "No injury indicated"]
    )
    if injury_choice == "Injury indicated":
        filtered = filtered[filtered["Injury_Indicator"] == 1]
    elif injury_choice == "No injury indicated":
        filtered = filtered[filtered["Injury_Indicator"] == 0]

st.sidebar.divider()
st.sidebar.caption(f"Showing {len(filtered):,} of {len(df_original):,} records.")

if filtered.empty:
    st.warning("No records match the selected filters. Change the filters in the sidebar.")
    st.stop()

# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------
def injury_label(value):
    return "Injury indicated" if value == 1 else "No injury indicated"


def safe_mean(data, column):
    return float(data[column].mean()) if column in data and data[column].notna().any() else 0.0


def safe_sum(data, column):
    return float(data[column].sum()) if column in data and data[column].notna().any() else 0.0


# ---------------------------------------------------------
# KPI row
# ---------------------------------------------------------
st.subheader("📊 Dashboard Overview")

total_records = len(filtered)
avg_performance = safe_mean(filtered, "Performance_Score")
avg_fatigue = safe_mean(filtered, "Fatigue_Score")
total_training_hours = safe_sum(filtered, "Training_Hours_Per_Week")
injury_count = int((filtered["Injury_Indicator"] == 1).sum())
injury_rate = (injury_count / total_records * 100) if total_records else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total athletes", f"{total_records:,}")
k2.metric("Average performance", f"{avg_performance:.1f}")
k3.metric("Average fatigue", f"{avg_fatigue:.1f}")
k4.metric("Total weekly training hours", f"{total_training_hours:,.0f}")
k5.metric("Injury-indicator rate", f"{injury_rate:.1f}%")

st.caption(
    "All KPIs and charts update automatically when sidebar filters are changed. "
    "The injury indicator is a dataset label, not a medical diagnosis."
)

# ---------------------------------------------------------
# Tabs
# ---------------------------------------------------------
overview_tab, analysis_tab, visual_tab, insights_tab = st.tabs(
    ["📋 Dataset Overview", "🔬 Data Analysis", "📈 Visualizations", "💡 Insights"]
)

with overview_tab:
    st.subheader("Dataset Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Columns / attributes", df_original.shape[1])
    c2.metric("Original dataset records", len(df_original))
    c3.metric("Missing values", int(df_original.isna().sum().sum()))

    st.markdown("**Filtered dataset preview**")
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    with st.expander("View descriptive statistics"):
        st.dataframe(
            filtered.describe(include="all").transpose(),
            use_container_width=True
        )

    with st.expander("View missing-value summary"):
        missing_summary = (
            df_original.isna().sum()
            .rename("Missing values")
            .to_frame()
        )
        st.dataframe(missing_summary, use_container_width=True)

with analysis_tab:
    st.subheader("Category-wise Analysis")

    category_column = st.selectbox(
        "Select a category for group-by analysis",
        options=[
            col for col in ["Position", "Gender", "Injury_Indicator", "Age"]
            if col in filtered.columns
        ]
    )

    category_summary = (
        filtered.groupby(category_column, dropna=False)
        .size()
        .reset_index(name="Athlete Count")
        .sort_values("Athlete Count", ascending=False)
    )

    if category_column == "Injury_Indicator":
        category_summary["Injury Status"] = category_summary[
            "Injury_Indicator"
        ].map({0: "No injury indicated", 1: "Injury indicated"})
        display_category = "Injury Status"
    else:
        display_category = category_column

    left, right = st.columns(2)
    with left:
        st.markdown("**Number of athletes by category**")
        st.dataframe(
            category_summary[[display_category, "Athlete Count"]],
            use_container_width=True,
            hide_index=True
        )
    with right:
        fig_category = px.bar(
            category_summary,
            x=display_category,
            y="Athlete Count",
            color=display_category,
            title=f"Athlete Count by {category_column.replace('_', ' ')}",
            labels={
                display_category: category_column.replace("_", " "),
                "Athlete Count": "Number of athletes"
            },
            text="Athlete Count"
        )
        fig_category.update_layout(showlegend=False)
        st.plotly_chart(fig_category, use_container_width=True)

    st.divider()
    st.subheader("Numerical Attribute Summary")
    numerical_columns = filtered.select_dtypes(include="number").columns.tolist()
    default_metric = "Performance_Score" if "Performance_Score" in numerical_columns else numerical_columns[0]
    selected_metric = st.selectbox(
        "Choose a numerical attribute",
        numerical_columns,
        index=numerical_columns.index(default_metric)
    )

    m1, m2, m3 = st.columns(3)
    m1.metric(f"Sum of {selected_metric.replace('_', ' ')}", f"{filtered[selected_metric].sum():,.2f}")
    m2.metric(f"Average {selected_metric.replace('_', ' ')}", f"{filtered[selected_metric].mean():,.2f}")
    m3.metric(f"Maximum {selected_metric.replace('_', ' ')}", f"{filtered[selected_metric].max():,.2f}")

    st.markdown("**Average selected metric by position**")
    if "Position" in filtered.columns:
        position_metric = (
            filtered.groupby("Position")[selected_metric]
            .mean()
            .reset_index()
            .sort_values(selected_metric, ascending=False)
        )
        st.dataframe(position_metric, use_container_width=True, hide_index=True)

with visual_tab:
    st.subheader("Data Visualization")

    # Bar chart
    st.markdown("#### 1. Bar Chart – Athlete Distribution by Position")
    if "Position" in filtered.columns:
        position_counts = (
            filtered["Position"].value_counts()
            .rename_axis("Position")
            .reset_index(name="Athlete Count")
        )
        bar_fig = px.bar(
            position_counts,
            x="Position",
            y="Athlete Count",
            color="Position",
            text="Athlete Count",
            title="Number of Athletes in Each Playing Position",
            labels={"Athlete Count": "Number of athletes"}
        )
        bar_fig.update_layout(showlegend=False)
        st.plotly_chart(bar_fig, use_container_width=True)
        st.caption(
            "Interpretation: This chart compares the number of athletes in each "
            "playing position and shows how the dataset is distributed."
        )

    st.divider()

    # Line chart: no date field exists, so training intensity is used as an ordered scale.
    st.markdown("#### 2. Line Chart – Average Performance Across Training Intensity")
    line_metric = st.selectbox(
        "Select metric for line chart",
        ["Performance_Score", "Fatigue_Score", "ACL_Risk_Score"],
        key="line_metric"
    )
    line_data = (
        filtered.groupby("Training_Intensity")[line_metric]
        .mean()
        .reset_index()
        .sort_values("Training_Intensity")
    )
    line_fig = px.line(
        line_data,
        x="Training_Intensity",
        y=line_metric,
        markers=True,
        title=f"Average {line_metric.replace('_', ' ')} by Training Intensity",
        labels={
            "Training_Intensity": "Training intensity",
            line_metric: f"Average {line_metric.replace('_', ' ')}"
        }
    )
    st.plotly_chart(line_fig, use_container_width=True)
    st.caption(
        "Interpretation: Training intensity is displayed in ascending order. "
        "The line shows how the selected average metric varies across intensity levels. "
        "This is a comparison across intensity levels, not a time-series trend."
    )

    st.divider()

    # Scatter plot
    st.markdown("#### 3. Scatter Plot – Training Hours and Fatigue")
    scatter_x = st.selectbox(
        "X-axis variable",
        ["Training_Hours_Per_Week", "Training_Intensity", "Age", "Weight_kg"],
        key="scatter_x"
    )
    scatter_y = st.selectbox(
        "Y-axis variable",
        ["Fatigue_Score", "Performance_Score", "ACL_Risk_Score", "Load_Balance_Score"],
        key="scatter_y"
    )
    scatter_fig = px.scatter(
        filtered,
        x=scatter_x,
        y=scatter_y,
        color=filtered["Injury_Indicator"].map(
            {0: "No injury indicated", 1: "Injury indicated"}
        ),
        hover_data=["Athlete_ID", "Position"],
        title=f"{scatter_y.replace('_', ' ')} vs {scatter_x.replace('_', ' ')}",
        labels={
            scatter_x: scatter_x.replace("_", " "),
            scatter_y: scatter_y.replace("_", " "),
            "color": "Injury status"
        }
    )
    st.plotly_chart(scatter_fig, use_container_width=True)
    st.caption(
        "Interpretation: Each point represents one athlete. The scatter plot helps "
        "explore relationships, clusters and unusual observations between two "
        "numerical attributes. Association does not prove causation."
    )

with insights_tab:
    st.subheader("Key Observations and Insights")

    position_counts = filtered["Position"].value_counts()
    most_common_position = position_counts.index[0] if not position_counts.empty else "N/A"
    highest_training_intensity = (
        filtered.groupby("Training_Intensity")["Performance_Score"].mean().idxmax()
        if filtered["Training_Intensity"].nunique() > 0 else "N/A"
    )
    injury_group = filtered.groupby("Injury_Indicator")["ACL_Risk_Score"].mean()
    avg_acl_injury = injury_group.get(1, float("nan"))
    avg_acl_no_injury = injury_group.get(0, float("nan"))

    st.markdown(
        f"""
        - **Most represented position:** {most_common_position}.
        - **Athletes in the current filtered view:** {total_records}.
        - **Average performance score:** {avg_performance:.2f}.
        - **Average fatigue score:** {avg_fatigue:.2f}.
        - **Athletes with an injury indicator:** {injury_count} ({injury_rate:.1f}%).
        """
    )

    if pd.notna(avg_acl_injury) and pd.notna(avg_acl_no_injury):
        st.markdown(
            f"- **Average ACL risk score:** {avg_acl_injury:.2f} for athletes "
            f"with an injury indicator and {avg_acl_no_injury:.2f} for athletes "
            "without an injury indicator."
        )

    st.info(
        "Use these results as descriptive insights from this dataset only. "
        "They should not be interpreted as medical advice or proof that a training "
        "factor causes an injury."
    )

    with st.expander("Explore injury-indicator summary"):
        injury_summary = (
            filtered["Injury_Indicator"]
            .value_counts()
            .rename(index={0: "No injury indicated", 1: "Injury indicated"})
            .rename_axis("Injury status")
            .reset_index(name="Athlete count")
        )
        st.dataframe(injury_summary, use_container_width=True, hide_index=True)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.divider()
st.caption(
    "Collegiate Athlete Injury Analysis | Developed using Python, Streamlit, "
    "Pandas and Plotly"
)
