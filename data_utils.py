import streamlit as st
import pandas as pd
from pathlib import Path


@st.cache_data
def load_survey_data():
    csv_path = Path(__file__).parent / "survey.csv"
    df = pd.read_csv(csv_path)
    df['pain_points_list'] = df['modeling_pain_points'].fillna('').str.split(', ')
    df['ai_helps_list'] = df['ai_helps_with'].fillna('').str.split(', ')
    df['team_focus_list'] = df['team_focus'].fillna('').str.split(', ')
    df['has_firefighting'] = df['team_focus'].str.contains('Fighting fires', na=False)
    df['has_leadership_gap'] = df['biggest_bottleneck'].str.contains('Lack of leadership', na=False)
    df['daily_ai_user'] = df['ai_usage_frequency'].isin(['Multiple times per day', 'Daily'])
    df['ai_embedded'] = df['ai_adoption'] == 'AI embedded in most workflows'
    df['role_category'] = df['role'].apply(
        lambda x: 'Leaders/Managers' if pd.notna(x) and any(kw in x.lower() for kw in ['manager', 'director', 'vp', 'lead', 'head', 'chief', 'cdo', 'cto', 'cio', 'founder']) else 'Individual Contributors'
    )
    return df


def apply_global_filters(df):
    filtered = df.copy()
    if st.session_state.filter_role:
        filtered = filtered[filtered['role'].isin(st.session_state.filter_role)]
    if st.session_state.filter_industry:
        filtered = filtered[filtered['industry'].isin(st.session_state.filter_industry)]
    if st.session_state.filter_org_size:
        filtered = filtered[filtered['org_size'].isin(st.session_state.filter_org_size)]
    if st.session_state.filter_region:
        filtered = filtered[filtered['region'].isin(st.session_state.filter_region)]
    return filtered


def reset_filters():
    keys_to_delete = [
        'filter_role', 'filter_industry', 'filter_org_size', 'filter_region',
        '_prev_filter_role', '_prev_filter_industry', '_prev_filter_org_size', '_prev_filter_region'
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]


def get_filtered_df():
    if 'df_filtered' in st.session_state and st.session_state.df_filtered is not None:
        return st.session_state.df_filtered
    return st.session_state.df


def explode_multiselect(df, column):
    exploded = df.copy()
    list_col = column + '_list' if column + '_list' in df.columns else None
    if list_col:
        exploded = exploded.explode(list_col)
        exploded = exploded[exploded[list_col].str.strip() != '']
        return exploded, list_col
    items = df[column].str.split(', ').explode()
    items = items[items.str.strip() != '']
    return items.reset_index(), column


def compute_similarity(user_profile, df, weights=None):
    if weights is None:
        weights = {
            'role': 0.8, 'industry': 0.5, 'org_size': 0.3, 'region': 0.2,
            'storage_environment': 0.7, 'orchestration': 0.6, 
            'modeling_approach': 0.5, 'ai_usage_frequency': 0.4
        }
    
    scores = pd.Series(0.0, index=df.index)
    total_weight = sum(weights.values())
    
    for col, weight in weights.items():
        if col in user_profile and col in df.columns:
            scores += (df[col] == user_profile[col]).astype(float) * weight
    
    return scores / total_weight


def get_value_counts_pct(df, column, top_n=None):
    counts = df[column].value_counts()
    pct = (counts / len(df) * 100).round(1)
    result = pd.DataFrame({'count': counts, 'percentage': pct}).reset_index()
    result.columns = [column, 'count', 'percentage']
    if top_n:
        result = result.head(top_n)
    return result


def get_crosstab_pct(df, row_col, col_col):
    ct = pd.crosstab(df[row_col], df[col_col], normalize='index') * 100
    return ct.round(1)


ORG_SIZE_ORDER = ["< 50 employees", "50–199", "200–999", "1,000–10,000", "10,000+"]

AI_USAGE_ORDER = ["Never", "Rarely", "Weekly", "Daily", "Multiple times per day"]

AI_ADOPTION_ORDER = [
    "No meaningful adoption yet",
    "Experimenting", 
    "Using AI for tactical tasks",
    "Building internal AI platforms",
    "AI embedded in most workflows"
]


def get_options_with_counts(df_subset, column, order=None):
    counts = df_subset[column].dropna().value_counts()
    if order:
        ordered_vals = [v for v in order if v in counts.index]
        counts = counts.reindex(ordered_vals).dropna()
    return {f"{val} ({int(count):,})": val for val, count in counts.items() if count > 0}


def init_multiselect_state(key, all_label):
    prev_key = f"_prev_{key}"
    if key not in st.session_state:
        st.session_state[key] = [all_label]
        st.session_state[prev_key] = [all_label]
        return
    
    current = list(st.session_state[key])
    prev = list(st.session_state.get(prev_key, [all_label]))
    
    if not current:
        st.session_state[key] = [all_label]
    elif all_label in current and all_label not in prev:
        st.session_state[key] = [all_label]
    elif all_label in current and len(current) > 1:
        st.session_state[key] = [x for x in current if x != all_label]
    
    st.session_state[prev_key] = list(st.session_state[key])


def get_multiselect_values(key, all_label, options_map):
    selection = st.session_state.get(key, [all_label])
    if not selection or all_label in selection:
        return []
    return [options_map[s] for s in selection if s in options_map]
