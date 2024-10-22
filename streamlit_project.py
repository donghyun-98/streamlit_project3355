# streamlit run "/Users/macbook/Desktop/vscode/내배캠/프로젝트/4. 최종프로젝트/스트림릿 구현/streamlit_project.py"
# cd '/Users/macbook/Desktop/vscode/내배캠/프로젝트/4. 최종프로젝트/스트림릿 구현/'
# streamlit run streamlit_project.py

# 기본파일 - 음식점도 검색으로 필터링 가능함


######################## 필요한 모듈들 ########################
import streamlit as st
from streamlit_extras.app_logo import add_logo
import pandas as pd
import numpy as np
from keplergl import KeplerGl
import os
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from math import pi
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 폰트 파일 경로
font_path = 'fonts/SCDream6.otf'
font_prop = fm.FontProperties(fname=font_path)
# 폰트 설정
plt.rcParams['font.family'] = font_prop.get_name()


# 배경화면과 탭 스타일을 함께 설정하는 함수
def add_bg_and_tab_style():
    st.markdown(
        """
        <style>
        # /* 배경화면 설정 */
        # .stApp {
        #     background-image: url("https://i.imgur.com/s8eZjZw.jpeg?2");
        #     background-attachment: fixed;
        #     background-size: cover;
        # }

        # /* 타이틀과 서브헤더 색상 설정 */
        # h1, h2, h3, h4, h5, h6 {
        #     color: black;  /* 타이틀과 서브헤더를 흰색으로 설정 */
        # }

        # /* 탭 스타일 설정 */
        # div[class*="stTabs"] button {
        #     color: white !important;  /* 모든 탭 글자색을 흰색으로 설정 */
        # }
        # div[class*="stTabs"] button[data-selected="true"] {
        #     background-color: #4CAF50 !important;  /* 선택된 탭 배경을 초록색으로 설정 */
        #     color: white !important;  /* 선택된 탭 글자색을 흰색으로 설정 */
        # }
        
        # /* 사이드바 텍스트 색상 설정 */
        # section.stSidebar.st-emotion-cache-vmpjyt.eczjsme18 .st-emotion-cache-6qob1r.eczjsme11 {
        #     color: black !important;  /* 사이드바 텍스트를 검정색으로 설정 */
        # }

        </style>
        """,
        unsafe_allow_html=True
    )




# 음식점 데이터 로드 함수
def load_restaurant_data(filepath):
    restaurant_df = pd.read_csv(filepath, encoding='utf-8')
    restaurant_df[['lat', 'lon']] = restaurant_df[['위도', '경도']]  # 위도, 경도 컬럼 매핑
    return restaurant_df

# 명당 데이터 로드 함수
def load_place_data(filepath):
    place_df = pd.read_csv(filepath, encoding='utf-8')
    place_df[['lat', 'lon']] = place_df[['Latitude', 'Longitude']]
    return place_df


# 사이드바 필터와 검색창 생성 및 음식점 필터링 및 지표 필터링 함수
def sidebar_filters(restaurant_df, place_df):    
    with st.sidebar:
        # 사이드바에 로고 이미지 표시
        st.image("images/로고.png", use_column_width=True)
        
        # 명당 데이터 검색 (주소나 명당 건물명 검색)
        search_query = st.text_input(
            "🔍 주소나 명당 건물명을 입력하세요",
            placeholder="ex) RM숲2호 or 여의동로 330"  # 여기서 placeholder를 설정하여 기본 텍스트 제공
            )
        
        # 기본 필터링 상태를 유지할 초기화 변수
        filtered_place_df = place_df
        filtered_restaurant_df = restaurant_df
        
        
        if search_query:
            # 입력된 검색어와 place_df 데이터에서 띄어쓰기를 제거한 후 검색
            search_query_cleaned = search_query.replace(" ", "")
            
            # place_df 필터링
            filtered_place_df = place_df[
                place_df['건물명'].str.replace(" ", "").str.contains(search_query_cleaned, case=False, na=False) |
                place_df['전체주소'].str.replace(" ", "").str.contains(search_query_cleaned, case=False, na=False) |
                place_df['추천장소이름'].str.replace(" ", "").str.contains(search_query_cleaned, case=False, na=False)
            ]
            
            # restaurant_df 필터링
            filtered_restaurant_df = restaurant_df[
                restaurant_df['업체명'].str.replace(" ", "").str.contains(search_query_cleaned, case=False, na=False) |
                restaurant_df['주소'].str.replace(" ", "").str.contains(search_query_cleaned, case=False, na=False)
            ]
            
            st.session_state.map_flag = True  # 검색어가 입력되면 col2가 나타나도록 함
        else:
            st.session_state.map_flag = False  # 검색어가 없으면 지도를 표시하지 않음


        # 장소 분류 필터 선택
        selected_place_types = st.multiselect(
            '📍 장소 유형 선택',
            ['개방형 공간', '유료 공간', '제한형 공간', '그 외 공간']
        )
        # 장소 분류에 따른 매핑 사전
        place_type_mapping = {
            # 개방형 공간
            '공공': '개방형 공간',  # 기존 코드의 '공공'도 추가
            '비건물': '개방형 공간',
            
            # 유료 공간
            '숙박시설': '유료 공간',
            '제2종근린생활시설': '유료 공간',
            '제1종근린생활시설': '유료 공간',
            '운동시설': '유료 공간',
            '판매시설': '유료 공간',
            '판매및영업시설': '유료 공간',
            '근린생활시설': '유료 공간',
            '문화및집회시설': '유료 공간',
            '관광휴게시설': '유료 공간',
            '카페': '유료 공간',
            '식당': '유료 공간',
            '호텔': '유료 공간',
            '관광': '유료 공간',
            '빌딩': '유료 공간',

            # 제한형 공간
            '공동주택': '제한형 공간',
            '업무시설': '제한형 공간',
            '단독주택': '제한형 공간',
            '종교시설': '제한형 공간',
            '의료시설': '제한형 공간',
            '교육연구시설': '제한형 공간',
            '노유자시설': '제한형 공간',
            '공장': '제한형 공간',
            '운수시설': '제한형 공간',
            '교정및군사시설': '제한형 공간',
            '자동차관련시설': '제한형 공간',
            '방송통신시설': '제한형 공간',
            '창고시설': '제한형 공간',
            '위험물저장및처리시설': '제한형 공간',

            # 그 외 공간
            None: '그 외 공간'  # NaN 값은 '그 외 공간'으로 처리
        }
        # 장소종류에 따라 장소 유형을 매핑하고, NaN 값을 '그 외 공간'으로 처리
        filtered_place_df['place_type'] = filtered_place_df['장소종류'].map(place_type_mapping).fillna('그 외 공간')

        # 선택된 장소 유형에 맞는 데이터 필터링
        if selected_place_types:
            filtered_place_df = filtered_place_df[filtered_place_df['place_type'].isin(selected_place_types)]
        
        
        # 지표 필터 선택
        select_indicator = st.multiselect(
            '📊 지표 필터',
            ('가시성', '거리', '상권발달', '쾌적도', '접근성')
        )
        # 선택한 지표에 따른 필터링
        if select_indicator:
            filtered_df = pd.DataFrame()
            for indicator in select_indicator:
                indicator_column = indicator + "등급"
                indicator_filtered_df = filtered_place_df[filtered_place_df[indicator_column] == 1]
                filtered_df = pd.concat([filtered_df, indicator_filtered_df]).drop_duplicates().reset_index(drop=True)
        else:
            filtered_df = filtered_place_df  # 선택된 지표가 없으면 장소 필터링된 데이터를 사용


        st.markdown("<br>", unsafe_allow_html=True)
        # 음식점 포인트 표시 여부를 토글로 제어
        show_restaurants = st.toggle(
            "Show restaurant 🍴",
            value=False,
            help="이 토글을 활성화하면 음식점 포인트가 지도에 나타납니다.")
        
        # 음식점 필터 선택
        selected_filters = st.multiselect(
            '🍴 음식점 필터링',
            ('가족모임', '넓은', '데이트', '혼밥', '회식')
        )
        # 음식점 데이터 필터링
        if selected_filters:
            filter_condition = filtered_restaurant_df['필터'].apply(lambda x: all(f in x for f in selected_filters))
            filtered_restaurant_df = filtered_restaurant_df[filter_condition].reset_index(drop=True)

        
        
        # 필터링 후 결과 확인
        if filtered_restaurant_df.empty or filtered_df.empty:
            st.warning("해당 필터에 해당하는 결과가 없습니다. 필터를 조정해 주세요.")

    return filtered_restaurant_df, filtered_df, select_indicator, show_restaurants




# Kepler.gl을 사용하여 지도 표시
def display_map(restaurant_df, place_df, show_restaurants):
    # Kepler.gl 초기 설정
    map_1 = KeplerGl()


    # 음식점 포인트가 보이도록 토글에 따라 데이터 추가
    if show_restaurants:
        map_1.add_data(data=restaurant_df, name="음식점")
    # 명당 데이터는 항상 추가
    map_1.add_data(data=place_df, name="명당")


    # 기본 config 설정 (세션 상태 제거)
    config = {
        "version": "v1",
        "config": {
            "visState": {
                "filters": [],
                "layers": [
                    {
                        "id": "음식점",
                        "type": "point",
                        "config": {
                            "dataId": "음식점",
                            "label": "음식점",
                            "color": [245, 28, 106],  # 음식점은 빨간색
                            "columns": {
                                "lat": "lat",
                                "lng": "lon"
                            },
                            "isVisible": show_restaurants  # 음식점 포인트 가시성 설정
                        }
                    },
                    {
                        "id": "명당",
                        "type": "point",
                        "config": {
                            "dataId": "명당",
                            "label": "명당",
                            "color": [86, 193, 225],  # 명당은 파란색
                            "columns": {
                                "lat": "lat",
                                "lng": "lon"
                            },
                            "isVisible": True
                        }
                    }
                ],
                "interactionConfig": {
                    "tooltip": {
                        "fieldsToShow": {
                            "음식점": [
                                {"name": "업체명", "format": None},
                                {"name": "업종", "format": None},
                                {"name": "평점", "format": None},
                                {"name": "방문자리뷰", "format": None},
                                {"name": "블로그리뷰", "format": None},
                                {"name": "주소", "format": None},
                                {"name": "영업시간", "format": None},
                                {"name": "전화번호", "format": None},
                                {"name": "필터", "format": None},
                                {"name": "URL", "format": None}
                            ],
                            "명당": [
                                {"name": "건물명", "format": None},
                                {"name": "전체주소", "format": None},
                                {"name": "가시성등급", "format": None},
                                {"name": "거리등급", "format": None},
                                {"name": "상권발달등급", "format": None},
                                {"name": "쾌적도등급", "format": None},
                                {"name": "접근성등급", "format": None}
                            ]
                        },
                        "enabled": True
                    }
                }
            },
            "mapState": {
                "latitude": place_df['lat'].mean(),
                "longitude": place_df['lon'].mean(),
                "zoom": 13
            }
        }
    }

    # 초기 설정 및 지도 출력
    map_1.config = config
    map_1.save_to_html(file_name="map.html")
    st.components.v1.html(open("map.html", 'r').read(), height=720)
    
    
# 데이터 테이블 표시 함수
def display_data_table(restaurant_df, place_df, selected_indicators=None, selected_place_types=None):
    # 필요한 컬럼만 선택
    selected_columns = ['건물명', '전체주소', '장소종류', '가시성등급', '거리', '거리등급', '점포수', 
                        '상권발달등급', '혼잡도비율', '쾌적도등급', '접근성소요시간', 
                        '접근성등급', '추천장소이름', '추천장소여부']
    
    if selected_indicators:
        # 선택한 지표에 따라 명당 데이터를 정렬하고 색상을 입힘
        st.markdown("<h5>명당 후보 데이터 (지표 필터링 적용)</h5>", unsafe_allow_html=True)

        # 선택한 지표에 따른 데이터 정렬 기준
        sort_columns = []
        ascending = []
        
        # 선택한 지표 순서대로 정렬 기준 적용
        for indicator in selected_indicators:
            if indicator == '가시성':
                sort_columns.append('가시성등급')
                ascending.append(True)  # 가시성등급 오름차순
            elif indicator == '거리':
                sort_columns.append('거리')
                ascending.append(True)  # 거리 오름차순
            elif indicator == '쾌적도':
                sort_columns.append('혼잡도비율')
                ascending.append(True)  # 혼잡도비율 오름차순
            elif indicator == '상권발달':
                sort_columns.append('점포수')
                ascending.append(False)  # 점포수 내림차순
            elif indicator == '접근성':
                sort_columns.append('접근성소요시간')
                ascending.append(True)  # 접근성소요시간 오름차순

        # 선택한 지표 순서대로 데이터 정렬
        if sort_columns:
            df_sorted = place_df.sort_values(by=sort_columns, ascending=ascending)
        else:
            df_sorted = place_df  # 선택된 지표가 없으면 원본 데이터 사용

        # 결측치 처리 및 변환
        df_sorted['거리등급'] = df_sorted['거리등급'].fillna(0).astype(int)
        df_sorted['접근성소요시간'] = df_sorted['접근성소요시간'].fillna(0).astype(int)

        # 필요한 컬럼만 선택하여 데이터프레임 필터링
        df_filtered = df_sorted[selected_columns].reset_index(drop=True)
        df_filtered.index += 1  # 인덱스를 1부터 시작하도록 설정

        # 스타일 적용 함수
        def highlight_target_column(row):
            # 기본 색상 설정
            styles = ['color: black'] * len(row)
            # 선택한 지표의 등급이 1인 경우 해당 컬럼을 빨간색으로 표시
            for indicator in selected_indicators:
                column_name = indicator + '등급'
                if column_name in row and row[column_name] == 1:
                    col_idx = row.index.get_loc(column_name)
                    styles[col_idx] = 'color: red'
            return styles

        styled_df = df_filtered.style.apply(highlight_target_column, axis=1)

        # 데이터프레임 표시
        st.dataframe(styled_df, hide_index=True)

    else:
        # 선택한 지표가 없으면 기본 명당 데이터만 표시
        # 명당 데이터에서 필요한 컬럼만 선택하여 필터링
        df_filtered = place_df[selected_columns].reset_index(drop=True)
        df_filtered.index += 1  # 인덱스를 1부터 시작하도록 설정
        
        # 명당 데이터 표시 (h5 크기로)
        st.markdown("<h5>명당 데이터</h5>", unsafe_allow_html=True)
        st.dataframe(df_filtered, hide_index=True)
    
    
    # 음식점 데이터 표시
    st.markdown("<h5>음식점 데이터</h5>", unsafe_allow_html=True)
    # 보고 싶은 음식점 컬럼 설정
    restaurant_columns = ['업체명', '업종', '평점', '방문자리뷰', '블로그리뷰', '주소', '영업시간', '전화번호', '필터', 'URL']
    # 사용자에게 보여줄 컬럼만 선택하여 표시
    st.dataframe(restaurant_df[restaurant_columns], hide_index=True)

# 그래프 생성 함수
def congestion_figure(stay_final_dong, dong):
    colors = ['#a3d8f1',] * 16
    colors[11] = '#255daa'
    colors[12] = '#255daa'

    # 축제 기간과 비축제 기간 데이터 분리
    stay_festival = stay_final_dong[stay_final_dong['date'] == '2023-10-07']
    stay_not_festival = stay_final_dong[~(stay_final_dong['date'] == '2023-10-07')]

    # 축제 기간 유동인구를 시간별로 그룹화하여 총합 계산
    festival_grouped = stay_festival[stay_festival['법정동'] == dong].groupby('time')['stay_cnts'].sum().reset_index()

    # 비축제 기간 시간별 평균 유동인구 계산
    grouped_data = stay_not_festival[stay_not_festival['법정동'] == dong].groupby(['time', 'date'])['stay_cnts'].sum().reset_index()
    grouped_data_mean = grouped_data.groupby('time')['stay_cnts'].mean().round().reset_index()

    # 첫 번째 그래프: 축제 기간과 비축제 기간 비교
    fig = go.Figure(data=[go.Bar(
        x=festival_grouped['time'],
        y=festival_grouped['stay_cnts'],
        marker_color=colors,
        name='축제 기간 유동인구',
        hovertemplate='%{y:,}<extra></extra>'
        )],
            layout=dict( barcornerradius=8,)
        )

    fig.add_trace(go.Scatter(
        x=grouped_data_mean["time"], 
        y=grouped_data_mean["stay_cnts"],
        mode='lines',
        line=dict(color='#f51c6a', width=2),
        name="비축제 기간 평균 유동인구",
        hovertemplate='%{y:,}<extra></extra>'
    ))

    # y축 범위 설정
    max_non_festival = grouped_data_mean['stay_cnts'].max()
    max_festival = festival_grouped['stay_cnts'].max()
    y_range = max_non_festival * 5 if max_festival > (max_non_festival * 4) else max_non_festival * 3

    fig.update_layout(
        plot_bgcolor='#FFFFFF',
        width=800,
        height=500,
        title="<b>2023년 시간별 주변 혼잡도</b><br><sup>2023.10.07</sup>",
        title_x=0.01,
        title_font_size=25,
        font_size=11,
        hovermode="x unified",
        hoverlabel_bgcolor="WhiteSmoke",
        hoverlabel_font=dict(size=15,weight='bold'),
        legend=dict(orientation='h',yanchor='bottom', xanchor='center', y=-0.23, x=0.5,
                    font=dict(size=14)
    ),
        margin=dict(t=130))
    fig.update_xaxes(tickvals=['09:00', '12:00', '15:00', '18:00', '21:00'], showline=True, linecolor='#D8D8D8', tickfont=dict(size=14))
    fig.update_yaxes(range=(0, y_range), gridcolor='#D8D8D8', showline=True, linecolor='#D8D8D8', tickformat=',', tickfont=dict(size=14))

    # Streamlit으로 그래프 출력
    st.plotly_chart(fig, config={'displayModeBar': False})


    # 두 번째 그래프: 날짜별 유동인구
    grouped_data_all = stay_final_dong[stay_final_dong['법정동'] == dong].groupby(['time', 'date'])['stay_cnts'].sum().reset_index()
    custom_colors = ['#6E7072', '#67B0F5', '#60D98D', '#E5E4FA', '#ED3224', '#8C84EB'] 
    fig2 = px.line(grouped_data_all, x="time", y="stay_cnts", color='date', color_discrete_sequence=custom_colors)
    
    fig2.update_traces(hovertemplate='시간: %{x} <br>유동인구 : %{y}',hoverlabel=dict(font=dict(size=16)))
    fig2.update_layout(
        plot_bgcolor='#FFFFFF',
        width=800,
        height=500,
        title="<b>2023년 토요일 날짜별 유동인구</b><br><sup>2023.09.02 ~ 2023.10.14</sup><br>",
        title_x=0.01,
        title_font_size=25,
        font_size=15,
        legend=dict(orientation='h', entrywidth=100, yanchor='bottom', xanchor='center', y=-0.3, x=0.5,font=dict(size=15)),
        legend_title_text=None,
        margin=dict(t=120)
    )
    
    # hovertemplate 수정하여 외부 텍스트 제거
    fig2.update_traces(hovertemplate='<b>날짜</b>: %{customdata[0]} <br>' + 
                                    '<b>시간:</b> %{x}<br>' +
                                    '<b>유동인구:</b> %{y:,} <extra></extra>')

    # 날짜 정보를 hovertemplate에 포함시키기 위해 customdata 사용
    fig2.update_traces(customdata=grouped_data_all[['date']].values)
    
    # 각 라인에 대해 hoverlabel 색상 설정
    for i, color in enumerate(custom_colors):
        fig2.data[i].hoverlabel.bgcolor = color
        if i == 3:
            fig2.data[i].hoverlabel.font.color = 'Black'  # i가 3일 때 글씨 색상을 빨간색으로 설정
        else:
            fig2.data[i].hoverlabel.font.color = 'white'  # 나머지 라인의 글씨 색상은 흰색으로 설정
    
    fig2.update_xaxes(tickvals=['09:00', '12:00', '15:00', '18:00', '21:00'], showline=True, linecolor='#D8D8D8',title=None, tickfont=dict(size=14))
    fig2.update_yaxes(gridcolor='#D8D8D8', showline=True, linecolor='#D8D8D8', tickformat=',',title = None, tickfont=dict(size=14))
    st.plotly_chart(fig2, config={'displayModeBar': False})
    
    
   # 세 번째 그래프: 성별 및 연령대별 유동인구 분포
    stay_festival_age_gender = stay_festival[stay_festival['법정동'] == dong].groupby(['gender', 'age'])['stay_cnts'].sum().reset_index()
    categories = ['10대이하', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대']
    left_data = stay_festival_age_gender[stay_festival_age_gender['gender'] == 0]['stay_cnts'].values
    right_data = stay_festival_age_gender[stay_festival_age_gender['gender'] == 1]['stay_cnts'].values

    total_male = left_data.sum()
    total_female = right_data.sum()
    total_population = total_male + total_female
    left_percentage = (left_data / total_population) * 100
    right_percentage = (right_data / total_population) * 100


    fig3 = go.Figure(data=[
        go.Bar(
            y=categories,
            x=-left_percentage,
            name='남성',
            orientation='h',
            marker_color='#56C1E1',
            customdata=np.abs(left_percentage), 
            hovertemplate='<b>%{y}</b><br>남성: %{customdata:.2f}%<extra></extra>',
            hoverlabel=dict(bgcolor='WhiteSmoke', font=dict(color='#56C1E1', size=17))
        ),
        go.Bar(
            y=categories,
            x=right_percentage,
            name='여성',
            orientation='h',
            marker_color='#F51C6A',
            hovertemplate='<b>%{y}</b><br>여성: %{x:.2f}%<extra></extra>',
            hoverlabel=dict(bgcolor='WhiteSmoke', font=dict(color='#F51C6A', size=17))
        )
    ],
            layout=dict( barcornerradius=8,)
    )

    fig3.update_layout(
        width=800,
        height=500,
        title='<b>축제 인구 분포</b>',
        barmode='overlay',
        title_x=0.01,
        title_font_size=25,
        font_size=12,
        legend=dict(orientation='h', yanchor='bottom', xanchor='center', y=-0.2, x=0.5,font=dict(size=15)),
        margin=dict(t=120)
    )
    fig3.update_xaxes(range=[-20, 20],  # x축 범위 설정
                 tickvals=[-20,-15, -10, -5, 0, 5, 10, 15, 20],  # x축 값
                 ticktext=['20%','15%', '10%', '5%', '0%', '5%', '10%', '15%','20%'],
                 showline=True, 
                 linecolor='#D8D8D8',
                 title=None,  tickfont=dict(size=14))
    fig3.update_yaxes(
                 showline=True, 
                 linecolor='#D8D8D8',
                 title = None,  tickfont=dict(size=14))
    st.plotly_chart(fig3, config={'displayModeBar': False})

# 데이터 로드 및 전처리 함수
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-8')
    recommend = df[['건물명', '전체주소', '추천장소이름', '가시성등급', '거리', '점포수', '혼잡도비율', '접근성소요시간']].reset_index(drop=True)
    recommend.rename(columns={'점포수': '상권발달 점수'}, inplace=True)

    # 정규화 및 점수 계산
    recommend['가시성 점수'] = normalize(6 - recommend['가시성등급'])
    recommend['거리 점수'] = 1 - normalize(recommend['거리'])
    recommend['상권발달 점수'] = normalize(recommend['상권발달 점수'])
    recommend['쾌적도 점수'] = 1 - normalize(recommend['혼잡도비율'])
    recommend['접근성 점수'] = 1 - normalize(recommend['접근성소요시간'])

    return recommend[['추천장소이름', '가시성 점수', '거리 점수', '상권발달 점수', '쾌적도 점수', '접근성 점수', '전체주소', '건물명']]


# 정규화 함수
def normalize(column):
    return (column - column.min()) / (column.max() - column.min())


# 레이더 차트 생성 함수
def create_radar_chart(data, title):
    # '추천장소이름', '건물명', '전체주소' 중 하나를 선택
    selected_name = data['추천장소이름'].values[0] if not data['추천장소이름'].isnull().all() else \
                    data['건물명'].values[0] if not data['건물명'].isnull().all() else \
                    data['전체주소'].values[0]

    # 레이더 차트에 포함할 데이터 선택
    categories = ['가시성 점수', '거리 점수', '상권발달 점수', '쾌적도 점수', '접근성 점수']
    values = data[categories].iloc[0].values.flatten().tolist()
    values += values[:1]  # 첫 번째 값을 다시 추가하여 닫힌 차트 만들기

    N = len(categories)
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(pi / 2)
    ax.set_theta_direction(-1)

    plt.xticks(angles[:-1], [''] * len(categories), color='black', size=9, ha='center')  # 빈 문자열로 레이블 설정

    # 레이블이 표시될 y 좌표를 설정하기 위한 오프셋
    y_offset = 1.12  # 그래프의 반지름보다 약간 큰 값을 설정

    # 각 레이블의 y 위치를 수동으로 조정
    for i, category in enumerate(categories):
        plt.text(angles[i], y_offset, category, ha='center', va='bottom', color='black', fontsize=8, fontweight='bold')

    plt.yticks([0.2, 0.4, 0.6, 0.8], ["2", "4", "6", "8"], color="grey", size=7)
    plt.ylim(0, 1)

    ax.plot(angles, values, linewidth=2, linestyle='solid', label=selected_name)
    ax.fill(angles, values, alpha=0.4)

    plt.title(title, size=13, y=1.1, fontweight='bold')

    return fig


# 이미지 업로드 함수
def upload_image():
    st.subheader("명당 리뷰를 작성해주세요")
    place_name = st.text_input("명당명을 입력하세요:")
    uploaded_file = st.file_uploader("불꽃축제 사진을 업로드해 주세요", type=["jpg", "jpeg", "png"])
    
    if st.button("업로드"):
        if place_name and uploaded_file is not None:
            image = Image.open(uploaded_file)
            folder_path = os.path.join("업로드_사진", place_name)
            os.makedirs(folder_path, exist_ok=True)
            image_path = os.path.join(folder_path, f"{place_name}.jpg")
            image.save(image_path)
            st.image(image, caption='업로드된 이미지', use_column_width=True)
            st.success(f"{place_name}에 이미지가 성공적으로 업로드되었습니다!")
        else:
            st.warning("음식점 또는 명당명과 이미지를 모두 입력해야 합니다.")


# 메인 함수
def main():
    # 페이지 설정 (Wide 모드로 설정)
    st.set_page_config(layout="wide")
    add_bg_and_tab_style()

    
    # 세션 상태 초기화
    if "map_flag" not in st.session_state:
        st.session_state.map_flag = False  # 기본적으로 False로 설정하여 col2를 숨김
        
    
    # 음식점 데이터 불러오기
    restaurant_filepath = 'datafile/naver_category_crawling_result_merged_data_1017_02.csv'
    restaurant_df = load_restaurant_data(restaurant_filepath)

    # 명당 데이터 불러오기
    place_filepath = 'datafile/rank_merged_total_1018.csv'
    place_df = load_place_data(place_filepath)
    recommend_data = load_and_preprocess_data(place_filepath)
    
    # 타이틀과 서브타이틀 설정
    # st.title("서울세계불꽃축제 ~~")
    # st.subheader("🔎 음식점을 필터링하고 명당을 검색해보세요!")
    st.image('images/제목2.svg')
    
    
    # 사이드바 필터 및 토글 적용
    filtered_restaurant_df, filtered_place_df, selected_indicators, show_restaurants = sidebar_filters(restaurant_df, place_df)
    
    
    # 필터링 후 결과 확인
    if filtered_restaurant_df.empty and filtered_place_df.empty:
        st.warning("해당 필터에 해당하는 결과가 없습니다. 필터를 조정해 주세요.")
    else:
        # 탭 설정
        tabs = st.tabs(["🌏 지도 보기", "💽 음식점 및 명당 리스트", "📸 명당 리뷰"])
        
        
    # 첫 번째 탭: 음식점 및 명당 지도 보기
    with tabs[0]:
        # col2는 map_flag에 따라 표시
        if st.session_state.map_flag:
            col1, col2 = st.columns([2, 1], vertical_alignment='top')  # 왼쪽 컬럼의 크기를 더 크게 설정
        else:
            col1 = st.container()

        # 왼쪽 컬럼에서 Kepler.gl 지도와 추천장소 선택을 추가
        with col1:
            display_map(filtered_restaurant_df, filtered_place_df, show_restaurants)

        if st.session_state.map_flag:
            # 오른쪽 컬럼에서 전체 장소의 selectbox와 세부 정보를 표시
            with col2:
                # filtered_place_df를 명확하게 복사한 후 새로운 열 추가
                filtered_place_df = filtered_place_df.copy()

                # 새로운 열을 추가하여 정렬 기준 설정
                filtered_place_df['sort_key'] = filtered_place_df.apply(
                    lambda row: (
                        0 if row['추천장소여부'] == "yes" else 1,  # 추천장소여부가 "yes"인 경우 가장 우선순위
                        0 if pd.notnull(row['추천장소이름']) or pd.notnull(row['건물명']) else 1  # 추천장소이름 또는 건물명이 있는 경우 우선
                    ), 
                    axis=1
                )

                # 정렬된 데이터프레임 생성 (추천장소여부, 추천장소이름/건물명 순서대로 정렬)
                sorted_places_df = filtered_place_df.sort_values(by=['sort_key'])

                # 장소명 선택 (추천장소이름이 있으면 그 값, 없으면 건물명 또는 전체주소)
                sorted_places_list = sorted_places_df.apply(
                    lambda row: row['추천장소이름'] if pd.notnull(row['추천장소이름']) 
                                else (row['건물명'] if pd.notnull(row['건물명']) else row['전체주소']), axis=1
                )

                # 정렬된 리스트를 selectbox에 표시
                selected_place = st.selectbox(
                    "장소 선택", 
                    sorted_places_list.unique()  # 중복 제거 후 표시
                )

                # 선택된 장소의 정보를 container 안에 표시
                if selected_place:
                    selected_place_info = filtered_place_df[
                        (filtered_place_df['추천장소이름'] == selected_place) |
                        (filtered_place_df['건물명'] == selected_place) |
                        (filtered_place_df['전체주소'] == selected_place)
                    ]
                    with st.container(border=True, height=637):
                        st.markdown("<h4 style='text-align: left;'><strong>추천장소 정보</strong></h4>", unsafe_allow_html=True)

                        # CSS를 사용하여 값들을 오른쪽 정렬
                        st.markdown(f"""
                            <p style='display: flex; justify-content: space-between;'>
                                <strong>건물명</strong><span style='text-align: right;'>{selected_place_info['건물명'].values[0]}</span>
                            </p>
                            <p style='display: flex; justify-content: space-between;'>
                                <strong>전체주소</strong><span style='text-align: right;'>{selected_place_info['전체주소'].values[0]}</span>
                            </p>
                            <p style='display: flex; justify-content: space-between;'>
                                <strong>장소종류</strong><span style='text-align: right;'>{selected_place_info['장소종류'].values[0]}</span>
                            </p>
                            <p style='display: flex; justify-content: space-between;'>
                                <strong>추천장소여부</strong><span style='text-align: right;'>{selected_place_info['추천장소여부'].values[0]}</span>
                            </p>
                        """, unsafe_allow_html=True)

                        
                        st.markdown("<h4 style='text-align: left;'><strong>한눈에 지표 보기</strong></h4>", unsafe_allow_html=True)
                        # 레이더 차트 생성
                        place_data = recommend_data[
                            (recommend_data['추천장소이름'] == selected_place) |
                            (recommend_data['건물명'] == selected_place) |
                            (recommend_data['전체주소'] == selected_place)
                        ]

                        if not place_data.empty:
                            title = place_data['추천장소이름'].values[0] if not place_data['추천장소이름'].isnull().all() else \
                                    place_data['건물명'].values[0] if not place_data['건물명'].isnull().all() else \
                                    place_data['전체주소'].values[0]
                            
                            fig = create_radar_chart(place_data, title)
                            st.pyplot(fig)
                        else:
                            st.warning("선택된 장소에 대한 그래프를 생성할 수 없습니다.")
                        
                        # 선택된 장소의 지역3 정보를 확인
                        selected_region3 = selected_place_info['지역3']
                        
                        if not selected_region3.empty:
                            dong = selected_region3.values[0]
                            stay_final_dong = pd.read_csv("datafile/stay_final_dong.csv")                      
                            festival_grouped = stay_final_dong[stay_final_dong['법정동'] == dong]
                            
                            if not festival_grouped.empty:
                                congestion_figure(stay_final_dong, dong)
                            else:
                                st.warning("선택한 장소와 일치하는 데이터가 없습니다.")
                        else:
                            st.warning("선택된 장소의 지역3 정보가 없습니다.")
                                 

    # 두 번째 탭: 음식점 및 명당 데이터 보기
    with tabs[1]:
        display_data_table(filtered_restaurant_df, filtered_place_df, selected_indicators)

        
    # 세 번째 탭: 음식점 및 명당 사진 업로드
    with tabs[2]:
        upload_image()


# Streamlit 실행
if __name__ == "__main__":
    main()
    