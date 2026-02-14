import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from data_utils import get_filtered_df, get_options_with_counts, init_multiselect_state, get_multiselect_values
from chart_utils import create_sankey, get_compare_colors, get_plotly_scale

st.markdown("# :primary[:material/account_tree:] Technology Stack Explorer")
st.markdown("Discover popular technology stack combinations and tool pairings")

df = get_filtered_df()

dim_mapping = {
    "Storage Environment": "storage_environment",
    "Orchestration": "orchestration", 
    "Modeling Approach": "modeling_approach",
    "Industry": "industry",
    "Organization Size": "org_size"
}

with st.container(border=True):
    st.markdown("#### :primary[:material/settings:] Flow Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        source_dim_label = st.selectbox(
            "Source (Left):",
            options=list(dim_mapping.keys()),
            index=0,
            key="sankey_source"
        )
    
    with col2:
        target_options = [k for k in dim_mapping.keys() if k != source_dim_label]
        target_dim_label = st.selectbox(
            "Target (Right):",
            options=target_options,
            index=0,
            key="sankey_target"
        )
    
    with col3:
        min_flow = st.slider(
            "Minimum Flow Size:",
            min_value=1,
            max_value=30,
            value=5,
            help="Hide flows with fewer than this many respondents",
            key="sankey_min"
        )

source_col = dim_mapping[source_dim_label]
target_col = dim_mapping[target_dim_label]

flow_counts = df.groupby([source_col, target_col]).size().reset_index(name='count')
flow_counts = flow_counts[flow_counts['count'] >= min_flow]

if len(flow_counts) > 0:
    with st.container(border=True):
        st.markdown("#### :primary[:material/swap_horiz:] Stack Flow Diagram")
        
        source_labels = list(flow_counts[source_col].unique())
        target_labels = list(flow_counts[target_col].unique())
        all_labels = source_labels + target_labels
        
        sources = [source_labels.index(s) for s in flow_counts[source_col]]
        targets = [len(source_labels) + target_labels.index(t) for t in flow_counts[target_col]]
        values = flow_counts['count'].tolist()
        
        sankey_colors = get_compare_colors()
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_labels,
                color=[sankey_colors[0]] * len(source_labels) + [sankey_colors[1]] * len(target_labels)
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color='rgba(150, 150, 150, 0.4)'
            )
        )])
        fig.update_layout(height=500, font_size=11)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption(f"Showing {len(flow_counts):,} connections representing {flow_counts['count'].sum():,} respondents")

    with st.container(border=True):
        st.markdown("#### :primary[:material/category:] Top Stack Combinations")
        
        top_n = st.slider("Show top N combinations:", 5, 20, 10, key="stack_top")
        
        top_flows = flow_counts.nlargest(top_n, 'count')
        top_flows['combination'] = top_flows[source_col] + " → " + top_flows[target_col]
        top_flows['percentage'] = (top_flows['count'] / len(df) * 100).round(1)
        
        display_df = top_flows[['combination', 'count', 'percentage']].copy()
        display_df.columns = ['Stack Combination', 'Count', '% of Total']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

else:
    st.warning("No flows match the current filter. Try lowering the minimum flow size.")

source_opts = get_options_with_counts(df, source_col)

init_multiselect_state("stack_deep_source", f"All {source_dim_label.lower()}")

with st.container(border=True):
    st.markdown("#### :primary[:material/explore:] Stack Deep Dive")
    st.caption("Select 'All' to include everything; selecting specific options removes 'All'")
    
    if source_opts:
        all_label = f"All {source_dim_label.lower()}"
        st.multiselect(
            f"Select {source_dim_label}:",
            options=[all_label] + list(source_opts.keys()),
            key="stack_deep_source"
        )
        selected_sources = get_multiselect_values("stack_deep_source", all_label, source_opts)
        
        if selected_sources:
            filtered_df = df[df[source_col].isin(selected_sources)]
        else:
            filtered_df = df
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"##### {target_dim_label} Distribution")
            target_counts = filtered_df[target_col].value_counts().head(8)
            st.bar_chart(target_counts)
        
        with col2:
            st.markdown("##### Profile Metrics")
            st.metric("Respondents", f"{len(filtered_df):,}")
            ai_pct = filtered_df['daily_ai_user'].sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
            st.metric("Daily AI Users", f"{ai_pct:.1f}%")
            ff_pct = filtered_df['has_firefighting'].sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
            st.metric("Firefighting Rate", f"{ff_pct:.1f}%")
    else:
        st.warning("No data available")

with st.container(border=True):
    st.markdown("#### :primary[:material/pie_chart:] Tool Distribution")
    
    dist_col = st.selectbox(
        "View distribution for:",
        options=["Orchestration", "Storage Environment", "Modeling Approach"],
        key="tool_dist_col"
    )
    dist_col_map = {"Orchestration": "orchestration", "Storage Environment": "storage_environment", "Modeling Approach": "modeling_approach"}
    dist_field = dist_col_map[dist_col]
    
    tool_counts = df[dist_field].value_counts().reset_index()
    tool_counts.columns = [dist_field, 'count']
    tool_counts['percentage'] = (tool_counts['count'] / tool_counts['count'].sum() * 100).round(1)
    
    top_tool = tool_counts.iloc[0][dist_field] if len(tool_counts) > 0 else "N/A"
    top_tool_pct = tool_counts.iloc[0]['percentage'] if len(tool_counts) > 0 else 0
    
    fig = px.treemap(
        tool_counts,
        path=[dist_field],
        values='count',
        color='count',
        color_continuous_scale=get_plotly_scale()
    )
    fig.update_layout(height=500, margin=dict(t=30, l=10, r=10, b=10))
    fig.update_traces(textinfo='label+value', textfont_size=14)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("##### :primary[:material/lightbulb:] Key Insights")
        st.metric("Unique Options", f"{df[dist_field].nunique()}")
        top3_pct = tool_counts.head(3)['percentage'].sum()
        st.metric("Top 3 Concentration", f"{top3_pct:.1f}%")
        st.caption(f"**:primary[#1:]** {top_tool} ({top_tool_pct:.0f}%)")
        if len(tool_counts) >= 2:
            st.caption(f"**:primary[#2:]** {tool_counts.iloc[1][dist_field]} ({tool_counts.iloc[1]['percentage']:.0f}%)")
