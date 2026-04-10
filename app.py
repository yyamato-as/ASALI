import streamlit as st
from streamlit_searchbox import st_searchbox
from astroquery.linelists.cdms import CDMS
from astropy.coordinates import SkyCoord
from astropy import units as u
import astropy.constants as ac
import pandas as pd
import pyvo
from astroquery.alma import Alma
import numpy as np
from specdata import SpectroscopicData, PartitionFunction
import re
import urllib.parse
from astropy.table import Table
from astropy.table import vstack
from astropy.io import ascii

ASA_query = Alma()
ASA_query.archive_url = "https://almascience.nao.ac.jp"

st.set_page_config(layout="wide")

# --- カスタムCSSでチェックボックスの余白を削る ---
st.markdown(
    """
    <style>
    /* サイドバー内のチェックボックス（stCheckbox）の上下余白を最小化 */
    [data-testid="stSidebar"] [data-testid="stCheckbox"] {
        margin-bottom: -10px;  /* 下方向の余白を削る */
        padding-top: 0px;      /* 上方向の余白を削る */
    }
    /* テキストのフォントサイズを少し小さくしてさらに密度を上げる場合 */
    [data-testid="stSidebar"] label {
        font-size: 0.9rem !  important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    /* 全てのヘッダーの上部余白を調整 */
    div[data-testid="stHeaderElement"] {
        padding-top: 0rem !important;
        margin-top: -100px !important;
    }
    /* メインコンテンツエリア自体の最上部のパディングも削る */
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# st.markdown(
#     """
#     <style>
#     /* 1. 全ての入力欄（searchbox内部を含む）の縦幅を強制的に上書き */
#     div[data-baseweb="input"] {
#         height: 30px !important; /* お好みの高さに固定 */
#     }

#     /* 2. 入力欄内部のパディング（余白）を最小化 */
#     div[data-baseweb="input"] input {
#         padding-top: 0px !important;
#         padding-bottom: 0px !important;
#         line-height: 30px !important;
#     }

#     /* 3. 外側のコンテナ自体の高さも制限（これをしないと枠だけ小さくなって余白が残る） */
#     .st-key-mol_search_main_0, /* keyを指定している場合、その要素を狙い撃ち */
#     div:has(> .st-key-mol_search_main_0) {
#         height: 30px !important;
#         margin-bottom: 20px !important;
#     }

#     /* 4. 見出し(H5)との隙間も詰める */
#     h5 {
#         margin-bottom: 5px !important;
#         padding-bottom: 0px !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

st.markdown(
    """
    <style>
    /* 特定のボタン（Clear All）だけを小さくする */
    div.stButton > button[kind="secondary"] {
        height: 24px !important;
        line-height: 24px !important;
        padding: 0px 10px !important;
        font-size: 0.8rem !important;
        margin-top: 5px !important; /* ヘッダーの高さに合わせる微調整 */
    }
    
    /* ゴミ箱ボタンなど、他のボタンとの干渉を避けるなら
       keyを使ってセレクタを特定することも可能です */
    .st-key-clear_all_btn button {
        border-radius: 4px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# st.markdown(
#     """
#     <style>
#     /* 1. カラム内の要素を垂直方向中央に強制的に揃える */
#     [data-testid="column"] {
#         display: flex;
#         flex-direction: column;
#         justify-content: center;
#     }

#     /* 2. number_input の上下の無駄な余白を削除 */
#     [data-testid="stNumberInput"] {
#         padding-top: 0px !important;
#         padding-bottom: 0px !important;
#         margin-top: -5px !important;
#     }

#     /* 3. ボタン（ゴミ箱・Clear All）のサイズと余白の統一 */
#     .stButton button {
#         width: 100% !important;
#         padding: 0px !important;
#         height: 35px !important;
#     }
    
#     /* 4. 水平方向のズレを防ぐため、コンテナのパディングをリセット */
#     [data-testid="stHorizontalBlock"] {
#         align-items: center !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

st.markdown(
    """
    <style>
    /* 1. ヘッダーのスタイル */
    .table-header {
        font-size: 0.85rem;
        font-weight: bold;
        margin: 0 !important;
        padding: 0 !important;
        height: 30px;
        display: flex;
        align-items: center;
    }

    /* 2. 区切り線の余白を最小化 */
    .table-hr {
        margin-top: 2px !important;
        margin-bottom: 10px !important;
    }

    /* 3. 分子名のセルの高さを入力欄(38px)と完全に一致させる */
    .table-cell {
        height: 38px;
        line-height: 38px;
        font-size: 0.9rem;
        vertical-align: middle;
    }

    /* 4. 全てのウィジェットの上下マージンをゼロに強制固定 */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 5. number_input の高さを強制 */
    [data-testid="stNumberInput"] {
        margin-bottom: 0px !important;
    }
    
    [data-testid="stNumberInput"] div[data-baseweb="input"] {
        height: 38px !important;
    }

    /* 6. ボタン（ゴミ箱）の高さを入力欄と一致させ、余計な余白を排除 */
    [data-testid="column"] .stButton button {
        height: 38px !important;
        width: 100% !important;
        margin: 0 !important;
    }

    /* 7. 行間の隙間を一定にする */
    [data-testid="stHorizontalBlock"] {
        margin-bottom: 4px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# st.markdown(
#     """
#     <style>
#     /* 1. ヘッダー行の縦幅を最小化 */
#     .table-header {
#         font-size: 0.8rem !important; /* 文字を小さく */
#         font-weight: bold;
#         color: #555;
#         margin: 0 !important;
#         padding: 0 !important;
#         height: 20px !important; /* 高さを20pxに固定 */
#         line-height: 20px !important;
#     }

#     /* 2. 区切り線の隙間をさらに詰める */
#     hr {
#         margin-top: 2px !important;
#         margin-bottom: 8px !important;
#     }

#     /* 3. ボタン（Clear All & 🗑️）をさらに小さく */
#     [data-testid="column"] .stButton button {
#         height: 24px !important;   /* 標準の半分強 */
#         min-height: 24px !important;
#         padding: 0px 8px !important;
#         font-size: 0.75rem !important;
#         border-radius: 4px !important;
#         margin-top: 0px !important;
#     }

#     /* 4. 入力欄の高さをボタンに合わせて微調整（32px程度） */
#     [data-testid="stNumberInput"] div[data-baseweb="input"] {
#         height: 30px !important;
#     }
    
#     /* 5. 分子名の行の高さも合わせる */
#     .table-cell {
#         height: 30px;
#         line-height: 30px;
#         font-size: 0.85rem;
#     }

#     /* 6. 行間（コンテナ間の隙間）を極限まで詰める */
#     [data-testid="stHorizontalBlock"] {
#         gap: 0.2rem !important;
#         margin-bottom: -10px !important;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True
# )

# ALMA TAP Service URL
ALMA_TAP_URL = "https://almascience.org/tap"

JPL_PF_filename = "./database/catdir.cat"
CDMS_PF_filename = "./database/partition_function.dat"

ALMA_Band_frequency_range = {
    "Band 1": (35, 50),
    "Band 2": (67, 116),
    "Band 3": (84, 116),
    "Band 4": (125, 163),
    "Band 5": (163, 211),
    "Band 6": (211, 275),
    "Band 7": (275, 373),
    "Band 8": (385, 500),
    "Band 9": (602, 720),
    "Band 10": (787, 950)
}

def get_JPL_table(filename):
    with open(filename, "r") as f:
        data = f.read()

    lines = data.split("\n")
    def tryfloat(x):
            try:
                return float(x)
            except ValueError:
                return np.nan

    tbl = ascii.read(
        filename,
        format="fixed_width",
        names=['tag', 'name', '#lines', 'lg(Q(300))', 'lg(Q(225))',
                            'lg(Q(150))', 'lg(Q(75))', 'lg(Q(37.5))', 'lg(Q(18.75))', 'lg(Q(9.375))', "version"],
        col_starts=(0, 7, 19, 26, 33, 40, 47, 54, 61, 68, 75),
    )
    # tbl = Table(tbl_rows)
    return tbl

def fetch_JPL_species():
    tbl = get_JPL_table(JPL_PF_filename)
    df_mol = tbl["tag", "name"].to_pandas()
    df_mol["catalog"] = "JPL"
    return df_mol

def read_JPL_partition_function(filename, tag):
    tbl = get_JPL_table(filename)

    temps = np.array([300, 225, 150, 75, 37.5, 18.75, 9.375])
    Qvals = tbl[tbl["tag"] == tag]
    Qvals = np.array(list(Qvals[0])[3:-1])
    # print(tbl)
    return temps[~np.isnan(Qvals)], 10 ** Qvals[~np.isnan(Qvals)]

def get_CDMS_table(filename):
    with open(filename, "r") as f:
        data = f.read()

    lines = data.split("\n")
    def tryfloat(x):
            try:
                return float(x)
            except ValueError:
                return np.nan

    # the 'fixed width' table reader fails because there are rows that violate fixed width
    tbl_rows = []
    for row in lines[4:-2]:
        split = row.split()
        tag = int(split[0])
        molecule_and_lines = row[7:41]
        molecule = " ".join(molecule_and_lines.split()[:-1])
        nlines = int(molecule_and_lines.split()[-1])
        partfunc = map(tryfloat, row[41:].split())
        partfunc_dict = dict(zip(['lg(Q(1000))', 'lg(Q(500))', 'lg(Q(300))', 'lg(Q(225))',
                                    'lg(Q(150))', 'lg(Q(75))', 'lg(Q(37.5))', 'lg(Q(18.75))',
                                    'lg(Q(9.375))', 'lg(Q(5.000))', 'lg(Q(2.725))'], partfunc))
        tbl_rows.append({'tag': tag,
                            'name': molecule,
                            '#lines': nlines,
                            })
        tbl_rows[-1].update(partfunc_dict)
    tbl = Table(tbl_rows)
    return tbl


def fetch_CDMS_species():
    tbl = get_CDMS_table(CDMS_PF_filename)
    df_mol = tbl["tag", "name"].to_pandas()
    # df_mol = pd.read_csv(
    #     CDMS_PF_filename,
    #     sep='\s+', 
    #     skip_blank_lines=True,
    #     skiprows=4,
    #     usecols=[0,1],
    #     names=["tag", "name"]
    # )
    df_mol["catalog"] = "CDMS"
    return df_mol

def read_CDMS_partition_function(filename, tag):
    tbl = get_CDMS_table(filename)

    temps = np.array([100, 500, 300, 225, 150, 75, 37.5, 18.75, 9.375, 5.000, 2.725])
    Qvals = tbl[tbl["tag"] == tag]
    Qvals = np.array(list(Qvals[0])[3:])
    # print(tbl)
    return temps[~np.isnan(Qvals)], 10 ** Qvals[~np.isnan(Qvals)]

def parse_frequency_support(frequency_support_str):
    spw_list = str(frequency_support_str).split("U")
    freq_range_list = []
    for spw in spw_list:
        numin, numax = spw.strip()[1:-1].split(",")[0].split("..")
        numax = numax.replace("GHz", "")
        freq_range_list.append((float(numin), float(numax)))
    return freq_range_list

def get_spw_freq_coverage(em_min, em_max):
    numin = ac.c.to(u.m/u.s).value / em_max
    numax = ac.c.to(u.m/u.s).value / em_min
    return numin, numax

def format_ALMA_query(query_result):
    df = pd.DataFrame()
    df["Project Code"] = query_result["proposal_id"]
    df["Source Name"] = query_result["target_name"]

    # source coordinate
    coord = SkyCoord(ra=query_result["s_ra"], dec=query_result["s_dec"], unit=u.deg)
    df["R.A."] = coord.ra.to_string(sep="hms", precision=3)
    df["Dec."] = coord.dec.to_string(sep="dms", precision=2)
    df["Band"] = [int(band) for band in query_result["band_list"]]

    # frequency coverage
    freq_support = []
    for i, row in query_result.iterrows():
        freq_range_list = parse_frequency_support(row["frequency_support"])
        numin, numax = np.min(freq_range_list), np.max(freq_range_list)
        freq_support.append(f"{numin:.2f}–{numax:.2f} GHz")
    df["Freq. Support"] = freq_support

    df["Ang. Res. \n (arcsec)"] = query_result["s_resolution"]
    df["Min. Vel. Res. \n (km/s)"] = query_result["velocity_resolution"] * 1e-3
    df["Line Sens. @ 10 km/s \n (mJy/beam)"] = query_result["sensitivity_10kms"]
    df["Int. Time \n (h)"] = query_result["t_exptime"] / 3600 # in hour
    df["PWV \n (mm)"] = query_result["pwv"]
    df["PI"] = query_result["pi_name"]
    df["Status"] = query_result["data_rights"]

    # resolve duplication and averaged sensitivity
    # subset = df[df.duplicated(subset=["project_code", "source_name", "Freq. Support", "Ang. Res. (arcsec)"], keep=False)]
    # print(subset)
    df = df.loc[
        df.groupby(["Project Code", "Source Name", "Freq. Support", "Ang. Res. \n (arcsec)"])["Line Sens. @ 10 km/s \n (mJy/beam)"].idxmin()
    ]

    df = df.sort_values("Project Code")
    
    # return df.drop_duplicates()
    return df

# --- データ準備・キャッシュ ---
def fetch_all_target_names():
    query = "SELECT DISTINCT target_name FROM ivoa.ObsCore"
    # Alma ではなく、ご自身で定義されている ASA_query (Almaクラスのインスタンス) を使用してください
    result = Alma.query_tap(query)
    # リスト形式に変換して返す
    return sorted(result['target_name'].tolist())

@st.cache_data
def fetch_all_species():
    df_JPL = fetch_JPL_species()
    df_CDMS = fetch_CDMS_species()
    return pd.concat([df_CDMS, df_JPL])

def search_molecules(searchterm: str):
    if not searchterm: return []
    df = fetch_all_species()
    matches = df[df['name'].str.contains(searchterm, case=False, na=False)]
    return [(f"{row['name']} ({row['catalog']} {row['tag']})", int(row['tag'])) for _, row in matches.iterrows()]

# if "target_list" not in st.session_state:
#     st.session_state.target_list = fetch_all_target_names()

if "alma_query_results" not in st.session_state:
    st.session_state.alma_query_results = None


# --- UI: サイドバー ---
st.sidebar.title("Search Settings")

# 1. 天体設定
source_name = st.sidebar.text_input("Source Name", "")
alma_source_name = st.sidebar.text_input("ALMA source name", "")
# target_list = search_alma_sources(alma_source_name)
# st.write(target_list)
coordinate_RADec = st.sidebar.text_input("R.A. Dec.", "")
search_radius_str = st.sidebar.text_input("Search Radius (arcmin)", value=1.0)
# systemic_velocity_str = st.sidebar.text_input("Source Velocity (km/s)", placeholder="e.g., 2.8")

# def search_alma_source_names(searchterm: str):
#     return search_alma_sources(searchterm) if searchterm else []

# # サイドバーに設置
# st.sidebar.header("Search Settings")
# selected_target = st.sidebar.selectbox(
#     "Select or Type Target Name",
#     options=st.session_state.target_list,
#     index=None,
#     placeholder="Search targets..."
# )
# with st.sidebar:
#     selected_source = st_searchbox(
#         search_alma_source_names,
#         key="alma_source_search",
#         label="ALMA source name",
#         # placeholder="e.g. V883 Ori or G028",
#         placeholder=""
#     )

    # if selected_source:
    #     st.sidebar.success(f"Selected: **{selected_source}**")

colmin, colmax = st.sidebar.columns(2)
angres_min_str = colmin.text_input("Min. Ang. Res. (arcsec)", value=0.0)
angres_max_str = colmax.text_input("Max. Ang. Res. (arcsec)", value=1.0)
velres_min_str = colmin.text_input("Min. Vel. Res. (km/s)", value=0.0)
velres_max_str = colmax.text_input("Max. Vel. Res. (km/s)", value=10.0)

# 1. バンドリストの定義
bands = [f"{band} ({nurange[0]}–{nurange[1]} GHz)" for band, nurange in ALMA_Band_frequency_range.items()]

# 2. サイドバーに配置
st.sidebar.subheader("ALMA Bands")

selected_bands = []
for band in bands:
    # 各バンドのチェック状態を保持
    if st.sidebar.checkbox(band, value=True, key=f"check_{band}"):
        selected_bands.append(int(band.split()[1]))

if st.sidebar.button("Search Archive", type="primary"):
    # AstroqueryでALMA Archiveを検索
    with st.sidebar.spinner("Searching ALMA Science Archive..."):
        # ここで Alma.query_object 等を叩く
        if alma_source_name != "":
            # query_results_full = []
            # for source in targets:
            query_str = f"select * from ivoa.obscore where target_name like '%{alma_source_name}%'"
            query_str += "AND band_list in (" + ", ".join([f"'{str(band)}'" for band in selected_bands]) + ")"
            query_results_full = ASA_query.query_tap(
                query_str
            ).to_table()
            # st.write(query_results_full)
        else:
            source = SkyCoord(coordinate_RADec, frame="icrs") if coordinate_RADec != "" else source_name
            query_results_full = ASA_query.query_region(
                source,
                radius=float(search_radius_str) * u.arcmin,
                public=None,
                band_list=selected_bands
            )
        
        # limit angular/velocity resolution
        condition = (query_results_full["spatial_resolution"] >= float(angres_min_str)) & (query_results_full["spatial_resolution"] <= float(angres_max_str))
        condition = condition & (query_results_full["velocity_resolution"] * 1e-3 >= float(velres_min_str)) & (query_results_full["velocity_resolution"] * 1e-3 <= float(velres_max_str))
        query_results_full = query_results_full[condition].to_pandas()
        st.session_state.alma_query_results_full = query_results_full.copy()
        st.session_state.alma_query_results = format_ALMA_query(query_results_full)

if st.session_state.alma_query_results is not None:
    st.subheader(f"Archive Search Results")

    df = st.session_state.alma_query_results
    
    if not df.empty:
        # インタラクティブなテーブルを表示
        st.dataframe(
            df,
            use_container_width=True, # 横幅いっぱい
            hide_index=True,          # インデックス（左端の数字）を隠す
            height=300
        )
        st.caption(f"Showing {len(df)} projects matching selection criteria")
    else:
        st.warning("No projects found.")
else:
    st.info("Enter the criteria in the sidebar and click 'Search Archive'.")

st.divider()
        

# --- 0. セッション状態の初期化 ---
if "selected_molecules" not in st.session_state:
    st.session_state.selected_molecules = []
if "search_key_count" not in st.session_state:
    st.session_state.search_key_count = 0  # 検索窓をリセットするためのカウンター

# --- 1. 分子選択（下部） ---
col_search, _, col_spacer = st.columns([0.2, 0.05, 0.75])

with col_search:
    # 検索窓の key にカウンターを混ぜることで、追加後に強制リセットさせる
    st.markdown("##### Select Species")
    selected_tag = st_searchbox(
        search_molecules, 
        key=f"mol_search_{st.session_state.search_key_count}", 
        placeholder="Type & Select"
    )

    # st.write("Systemic Velocity (km/s)")
    vsys_str = st.text_input("Source Velocity (km/s)", value=0.0)

# 追加ロジック
with col_spacer:
    cols = st.columns([0.9, 0.1])
    # with cols[0]:
    #     st.markdown("##### Selected Species:")

    if selected_tag:
        # st.write(selected_tag)
        all_df = fetch_all_species()
        matching_rows = all_df[all_df['tag'] == selected_tag]
        
        if not matching_rows.empty:
            selected_name = matching_rows['name'].values[0]
            selected_catalog = matching_rows["catalog"].values[0]
            
            
            # 重複チェック
            if not any(m['tag'] == selected_tag for m in st.session_state.selected_molecules):
                st.session_state.selected_molecules.append({"name": selected_name, "tag": selected_tag, "catalog": selected_catalog})
                # st.session_state.selected_molecules.append(all_df[all_df['tag'] == selected_tag])
                # カウンターを増やして、次の検索窓を「新しいウィジェット」として認識させる
                st.session_state.search_key_count += 1
                st.rerun()

    col_ratio = [2, 1, 1, 1, 1, 0.8]
    h_cols = st.columns(col_ratio)
    header_names = ["Species", "$E_{up, min}$", "$E_{up, max}$", "$\log Int_{min}$", "$\log Int_{max}$", ""]

    for col, header in zip(h_cols, header_names):
        with col:
            # ヘッダーに Clear All を入れる場合
            if header == "" and col == h_cols[-1]:
                if st.button("Clear All", key="clear_all"):
                    st.session_state.selected_molecules = []
                    st.session_state.search_key_count += 1 # 念のため検索窓もリセット
                    st.rerun()
            else:
                col.markdown(f"<p class='table-header'>{header}</p>", unsafe_allow_html=True)

    # st.markdown("<hr style='margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
    st.markdown("<hr class='table-hr'>", unsafe_allow_html=True)
    # for col, name in zip(m_col, header_names):
    #     with col:
    #         # st.captionより少し太く、色をはっきりさせるとヘッダーらしくなります
    #         st.markdown(f"<p style='font-size: 1.0rem; font-weight: bold; color: #555;'>{name}</p>", unsafe_allow_html=True)
    # with m_col[-1]:
    #     if st.button("Clear All"):
    #         st.session_state.selected_molecules = []
    #         st.session_state.search_key_count += 1 # 念のため検索窓もリセット
    #         st.rerun()

    # st.divider()

    # m_col = st.columns(col_ratio)
    # --- 2. 選択済みリストの表示（常に表示） ---
    if st.session_state.selected_molecules:

        # with cols[1]:
        #     if st.button("Clear All"):
        #         st.session_state.selected_molecules = []
        #         st.session_state.search_key_count += 1 # 念のため検索窓もリセット
        #         st.rerun()
        
        # 削除用のインデックス保持
        to_delete = None
        mols_to_be_searched = []
        for i, mol in enumerate(st.session_state.selected_molecules):
            cols = st.columns(col_ratio)
        
            with cols[0]:
                # 分子名を中央に配置
                st.markdown(f"<div class='table-cell'>{mol['name']} ({mol['catalog']} {mol['tag']})</div>", unsafe_allow_html=True)
            
            # 数値入力：label_visibility="collapsed" は必須
            with cols[1]:
                Eu_min = st.number_input("emin", key=f"emin_{i}", label_visibility="collapsed", value=0.0, step=10.0)
            with cols[2]:
                Eu_max = st.number_input("emax", key=f"emax_{i}", label_visibility="collapsed", value=500.0, step=10.0)
            with cols[3]:
                logint_min = st.number_input("lmin", key=f"logImin_{i}", label_visibility="collapsed", value=-8.0, step=1.0)
            with cols[4]:
                logint_max = st.number_input("lmax", key=f"logImax_{i}", label_visibility="collapsed", value=None)
            
            mol["eu_range"] = (Eu_min, Eu_max)
            mol["logint_range"] = (logint_min, logint_max)
            mols_to_be_searched.append(mol)
            
            with cols[5]:
                # 削除ボタンの key も確実にユニークにする
                # st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True) # 微調整
                # st.markdown("<div style='padding-top:-5px;'>", unsafe_allow_html=True)
                # st.markdown("<div style='display:flex; justify-content:center; align-items:center; height:40px;'>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_btn_{mol['tag']}_{i}"):
                # if st.button("Clear", key=f"del_btn_{mol['tag']}_{i}"):
                    to_delete = i
        
        # 削除実行
        if to_delete is not None:
            st.session_state.selected_molecules.pop(to_delete)
            # 削除時も検索窓の状態に影響を与えないよう再描画
            st.rerun()

# --- メインロジック ---
# st.header("ALMA Science Archive Spectral Line Searching Tool")

if st.button("Search for Selected Species"):
    if not st.session_state.selected_molecules:
        st.warning("Please add at least one species.")
    else:
        with st.spinner("Fetching line frequencies and searching in the data above..."):
            try:
                df_rows = []
                for mol in mols_to_be_searched:
                    name = mol["name"]
                    catalog = mol["catalog"]
                    tag = mol["tag"]
                    
                    # get partition function
                    PF_FILENAME = JPL_PF_filename if catalog == "JPL" else CDMS_PF_filename
                    pf_func = read_CDMS_partition_function if catalog == "CDMS" else read_JPL_partition_function
                    # T, Q = getattr(SpectroscopicData, f"read_{catalog}_partition_function")(PF_FILENAME, tag)
                    T, Q = pf_func(PF_FILENAME, tag)
                    pf = PartitionFunction(species=name, T=T, Q=Q, database=catalog)

                    filename = f"./database/{catalog}/c{str(tag).zfill(6)}.cat"
                    specdata = SpectroscopicData(filename=filename, format=catalog, species=name, pf=pf)

                    # filtering with Eup and logint
                    Eumin, Eumax = (0.0, 500)
                    if Eumin is None: Eumin = 0.0
                    if Eumax is None: Eumax = np.inf

                    logintmin, logintmax = (-8, 0)
                    if logintmin is None: logintmin = -np.inf
                    if logintmax is None: logintmax = np.inf
                    specdata.table = specdata.table[(specdata.table["E_up"] >= Eumin) & (specdata.table["E_up"] <= Eumax) & (specdata.logint >= logintmin) & (specdata.logint <= logintmax)]

                    # st.write("heloo")

                    specdata._set_quantities()

                    # search
                    for i, row in st.session_state.alma_query_results_full.iterrows():
                        numin, numax = get_spw_freq_coverage(row["em_min"], row["em_max"])
                        nu_obs = (1 - float(vsys_str) / ac.c.to(u.km/u.s).value) * specdata.nu0
                        table = specdata.table[(nu_obs >= numin) & (nu_obs <= numax)]

                        if len(table) > 0:
                            for trow in table:
                                df_rows.append(
                                    {
                                        "Project Code": row["proposal_id"],
                                        "Source Name": row["target_name"],
                                        "Band": row["band_list"],
                                        "Ang. Res. (arcsec)": row["s_resolution"],
                                        "Vel. Res. (km/s)": trow["Frequency"] * 1e9 * row["em_resolution"] * 1e-3,
                                        "SPW": row["obs_id"].split(".")[-1],
                                        "Transition": name, # TODO format QNs,
                                        "Rest Freq. (GHz)": trow["Frequency"],
                                        "$E_\mathrm{u}$ (K)": trow["E_up"],
                                        "$\log_{10}A_\mathrm{ul}$": np.log10(trow["A_ul"]),
                                        "$g_\mathrm{u}$": trow["g_up"],
                                        "Link": ASA_query.archive_url + f"/aq/?{urllib.parse.urlencode({'mous': row['member_ous_uid'], 'sourceName': row['target_name']})}"
                                    }
                                )
                df = pd.DataFrame(df_rows)

                st.subheader(f"Line Search Results")
                if not df.empty:
                    # インタラクティブなテーブルを表示
                    st.dataframe(
                        df,
                        use_container_width=True, # 横幅いっぱい
                        hide_index=True,          # インデックス（左端の数字）を隠す
                        height=300,
                        column_config={
                            "Link": st.column_config.LinkColumn(
                                "Link",       # 表での表示名
                                help="Click to open the original ASA page",
                                validate="^https://.*", # セキュリティのためのバリデーション
                                display_text="Open in ASA" # セルに表示するテキストを統一（URLを隠す）
                            )
                        },
                    )
                    st.caption(f"Showing {len(df)} lines covered by the observations above")
                else:
                    st.warning("No lines found.")

            except Exception as e:
                st.error(f"Error: {e}")

