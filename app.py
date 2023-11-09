# streamlit_app.py
"""
A streamlit app
"""
import os
import requests
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import japanize_matplotlib
import altair as alt
import plotly.express as px
from st_aggrid import AgGrid, DataReturnMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


st.set_page_config(page_title="Simple Streamlit App", layout="wide", initial_sidebar_state="expanded")


# UI text strings

# セッションステートを使用して選択された都道府県を格納する
if 'selected_prefecture' not in st.session_state:
    st.session_state['selected_prefecture'] = "北海道"  # 初期値

# Sidebar
def render_search():
    """
    Render the search form in the sidebar.
    """
    st.sidebar.header("Search")
     # 都道府県のセレクトボックスを表示し、選択された都道府県をセッションステートに保存
    selected_prefecture = st.sidebar.selectbox(
        "Prefecture",
        ("北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", "新潟県", "富山県", 
        "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", "和歌山県", "鳥取県", 
        "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", 
        "沖縄県"),
        index=("北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県", "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県", 
        "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県", "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県", "奈良県", 
        "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県", "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県", "熊本県", "大分県", 
        "宮崎県", "鹿児島県", "沖縄県").index(st.session_state['selected_prefecture']),
        key='selected_prefecture' # セッションステートのキーを直接使用
    )  

    if st.sidebar.button("Search"):
        handler_search(selected_prefecture)
    
def handler_search(prefecture):
    """
    Handle the search form submission.
    """

    api_endpoint = "https://www.mlit-data.jp/api/v1/" # app_1 API Endpoint
    api_key = st.secrets["https://www.mlit-data.jp/api/v1/"]["api_key"] # app_1 API Key
    # GraphQL query
    query = f"""
    query {{
        search(
            term: ""
            first: 0
            size: 10000
            attributeFilter: {{
                AND: [
                    {{ attributeName: "DPF:dataset_id", is: "cals_construction" }},
                    {{ attributeName: "DPF:prefecture_name", is: "{prefecture}" }},
                ]
            }}
        ) {{
            totalNumber
            searchResults {{
                id
                title
                metadata
            }}
        }}
    }}"""

    # Make the HTTP request
    headers = {
            "Content-Type": "application/json",
            "apikey": api_key,
    }

    response = requests.post(api_endpoint, json={"query": query}, headers=headers)
    response.raise_for_status()

    # Parse the response
    response_body = response.json()
    total_number = response_body["data"]["search"]["totalNumber"]
    search_results = response_body["data"]["search"]["searchResults"]


    # Extract the relevant metadata from the search results
    metadata = []
    for result in search_results:
        metadata.append({
            "id": result["id"],
            "title": result["title"],
            "year": result["metadata"]["DPF:year"], #年度
            "title": result["metadata"]["DPF:title"], #工事名
            "lat": result["metadata"].get("DPF:latitude", ""), #緯度
            "lon": result["metadata"].get("DPF:longitude", ""), #経度
            "client_code": result["metadata"]["CALS:client_info"]["code"], #発注者コード
            "client_cat_main": result["metadata"]["CALS:client_info"].get("main_category", ""), #発注者カテゴリ
            "client_cat_middle": result["metadata"]["CALS:client_info"].get("middle_category", ""), #発注者カテゴリ
            "client_cat_sub": result["metadata"]["CALS:client_info"].get("sub_category", ""), #発注者カテゴリ
            "contractor_name": result["metadata"]["CALS:contractor_info"].get("name", ""), #施工者名
            "construction_type": result["metadata"]["CALS:construction_name_etc"].get("construction_type", ""), #工事種別
            "construction_name": result["metadata"]["CALS:construction_name_etc"].get("construction_name", ""), #工事名称
            "construction_field": result["metadata"]["CALS:construction_name_etc"].get("construction_field", ""), #工事分野
            "construction_number": result["metadata"]["CALS:construction_name_etc"].get("construction_number", ""), #工事番号
            "construction_content" : result["metadata"]["CALS:construction_name_etc"].get("construction_content", ""), #工事内容
            "construction_start_date" : result["metadata"]["CALS:construction_name_etc"].get("construction_start_date", ""), #工期開始日
            "construction_end_date" : result["metadata"]["CALS:construction_name_etc"].get("construction_end_date", ""), #工期終了日
            "CORINS_number" : result["metadata"]["CALS:construction_name_etc"].get("CORINS_number", ""), #コリンズ番号

        })
    
    return render_search_results(total_number, metadata, search_results)


def render_search_results(total_number, metadata, search_results):

    # Create a DataFrame from the metadata
    df = pd.DataFrame(metadata)

    # Display prefecuture name
    st.markdown("### 都道府県：" + st.session_state['selected_prefecture'])
 

    row1_1, row1_2 = st.columns([1, 2])        
    with row1_1:
        # Display metrics
        st.metric(label="工事件数", value=total_number)

    with row1_2:
        # plotting the map
        ## Convert latitude and longitude to numeric
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        ## Drop rows with NaN values in latitude and longitude
        df_map = df.dropna(subset=['lat', 'lon'])
        ## Plot the map
        st.map(df_map)


    st.markdown("### 年度毎の工事件数")
    row2_1, row2_2 = st.columns([1, 2])        
    with row2_1:
        # Table: Number of construction by year
        df_year = df.groupby("year").size().reset_index(name="count")
        st.write(df_year)
        fig = plt.figure()
    
    with row2_2:
        # Plotting the holizontal bar chart: Number of construction by year and construction field
        df_year_field = df.groupby(["year", "construction_field"]).size().reset_index(name="count")
        fig = plt.figure()
        fig = px.bar(df_year_field, x="year", y="count", color="construction_field", barmode="stack")
        st.plotly_chart(fig)


    st.markdown("### 発注者分類")
    row3_1, row3_2 = st.columns([1, 1])
    with row3_1:
        ## count the number of construction by client category
        counts = df.groupby(['client_cat_main', 'client_cat_middle', 'client_cat_sub']).size().reset_index(name='count')
        ## plotly Icicle chart
        fig = px.icicle(counts, path=['client_cat_main', 'client_cat_middle', 'client_cat_sub'], values='count')
        st.plotly_chart(fig)
    with row3_2:
        ## Table: Number of construction by client category
            st.write(counts)

    
    row4_1, row4_2 = st.columns([1, 1])
    with row4_1:
        st.markdown("### 工事分野") # Construction field
        ## Plotly horizontal bar chart: Number of construction by construction field
        df_construction_field = df.groupby("construction_field").size().reset_index(name="count")
        fig = px.bar(df_construction_field, x="count", y="construction_field", orientation="h")
        st.plotly_chart(fig)



    with row4_2:
        st.markdown("### 工事種別") # Construction type
        ## Plotly horizontal bar chart
        df_construction_field = df.groupby("construction_type").size().reset_index(name="count")
        fig = px.bar(df_construction_field, x="count", y="construction_type", orientation="h")
        st.plotly_chart(fig)


    st.markdown("### 工事一覧") 
    df_copy = df.copy()

    # グリッドの設定を更新
    gb = GridOptionsBuilder.from_dataframe(df_copy)
    gb.configure_pagination(enabled=True) #add pagination
    gridOptions = gb.build()


    # グリッドを表示
    grid_response = AgGrid(
        df_copy,
        gridOptions=gridOptions,
        height=1000,
        width='100%',
        fit_columns_on_grid_load=False,
        editable=False,
        custom_css={
            "#gridToolBar": { "padding-bottom": "0px !important"}
        },
    )


# Main page
def main():
    """
    Render the main page.
    """
    st.title("直轄工事ダッシュボード")
    
    render_search()


if __name__ == "__main__":
    main()
