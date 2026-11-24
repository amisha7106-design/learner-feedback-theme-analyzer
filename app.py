from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st
from src.database import FeedbackDatabase
from src.utils import read_uploaded_csv, read_csv_feedback
from src.analyzer import FeedbackAnalyzer
from src.llm_report import ReportGenerator

st.set_page_config(page_title="Learner Feedback | Insight Studio", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Manrope:wght@400;600;700;800&display=swap');
:root{--ink:#eef4ff;--muted:#a9b8d4;--panel:#111d3a;--line:rgba(160,190,255,.16);--cyan:#55d8ff;--violet:#9b8cff}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(65,100,210,.25),transparent 38%),radial-gradient(ellipse at 88% 8%,rgba(117,72,220,.20),transparent 32%),linear-gradient(145deg,#071126 0%,#0b1732 55%,#101b3b 100%);color:var(--ink);font-family:'DM Sans',sans-serif}
.block-container{padding-top:1.6rem;max-width:1440px}.stApp p,.stApp label,.stApp li{color:#dce7fb}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#101d3d,#0b1530);border-right:1px solid var(--line)}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(30,51,95,.9),rgba(17,29,58,.95));border:1px solid var(--line);padding:18px;border-radius:17px}
[data-testid="stMetricLabel"]{color:#b6c7e8!important}[data-testid="stMetricValue"]{color:white!important}
.stButton>button,.stDownloadButton>button{border:1px solid rgba(100,205,255,.45);border-radius:12px;background:linear-gradient(100deg,#347be8,#775de5);color:white;font-weight:700;padding:.62rem 1rem}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:#8de7ff;color:white;filter:brightness(1.12)}
section[data-testid="stFileUploader"]{background:rgba(22,39,77,.55);border:1px dashed #6589c9;border-radius:15px;padding:12px}
input,textarea,[data-baseweb="select"]{background-color:#15264b!important;color:white!important}
hr{border-color:var(--line)!important}.hero{padding:30px 32px;border:1px solid var(--line);border-radius:24px;background:linear-gradient(115deg,rgba(38,91,172,.48),rgba(83,57,160,.38)),rgba(14,27,57,.8);box-shadow:0 18px 60px rgba(0,0,0,.18);margin-bottom:24px}
.eyebrow{color:#75dcff;font-weight:800;letter-spacing:2px;font-size:11px;text-transform:uppercase}.hero h1{font-family:Manrope,sans-serif;font-size:clamp(30px,4vw,48px);line-height:1.12;margin:10px 0;color:white}.hero p{font-size:16px;color:#d0def7;max-width:760px}.tag{display:inline-block;padding:7px 11px;border:1px solid var(--line);border-radius:30px;color:#cfe8ff;font-size:12px;margin:12px 6px 0 0}.card{background:linear-gradient(145deg,rgba(23,41,81,.9),rgba(13,27,55,.9));border:1px solid var(--line);padding:19px;border-radius:18px;min-height:130px}.card h3{margin:0 0 7px;color:white;font-size:17px}.card p{color:#b7c8e7;font-size:13px}.section-title{font-family:Manrope,sans-serif;font-size:24px;font-weight:800;color:#f4f7ff;margin:8px 0 14px}.small-muted{color:#aebfdf;font-size:13px}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_db(): return FeedbackDatabase()
db=get_db()

with st.sidebar:
    st.markdown("<div style='font-size:34px'>🎓</div><h2 style='color:white;margin:0'>Insight Studio</h2><p style='color:#9fb3d8;font-size:12px'>LEARNER FEEDBACK ANALYZER</p>",unsafe_allow_html=True)
    st.divider()
    page=st.radio("NAVIGATION",["Home","Student Feedback Form","Teacher Dashboard","How It Works","History & Reports"],label_visibility="visible")
    st.divider()
    st.markdown("<p style='color:#9fb3d8;font-size:12px'>DEMO DATA</p>",unsafe_allow_html=True)
    if st.button("↳ Load sample dataset",use_container_width=True):
        try:
            rows=read_csv_feedback(Path(__file__).parent/"data"/"sample_feedback.csv")
            n=db.add_feedback_batch(rows); st.success(f"Imported {n} sample responses.")
        except Exception as e: st.error(str(e))
    if st.button("↻ Reset demo database",use_container_width=True):
        db.delete_all_feedback(); st.success("Demo data cleared.")
    st.caption("Use anonymized or approved feedback only. Never upload sensitive learner information.")

dashboard=db.get_dashboard_data()
counts={x['sentiment']:x['count'] for x in dashboard['sentiments']}

if page=="Home":
    st.markdown("""<div class='hero'><div class='eyebrow'>AI-ASSISTED EDUCATION QUALITY INSIGHTS</div><h1>Hear what your class is<br>happy about — and what needs care.</h1><p>Turn learner comments into clear themes, sentiment signals and practical improvement actions. Make feedback easier to understand, discuss and act on.</p><span class='tag'>✦ NLP-powered</span><span class='tag'>◉ Human-reviewed insights</span><span class='tag'>⌁ Secure local database</span></div>""",unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Feedback responses",dashboard['total']); c2.metric("Positive",counts.get('Positive',0)); c3.metric("Needs attention",counts.get('Negative',0)); c4.metric("Neutral",counts.get('Neutral',0))
    st.markdown("<div class='section-title'>What Insight Studio helps you discover</div>",unsafe_allow_html=True)
    a,b,c=st.columns(3)
    for col,icon,title,desc in [(a,"✦","Finds recurring themes","Groups similar comments so repeated topics become easier to spot."),(b,"◉","Measures the mood","Summarises positive, negative and neutral sentiment signals."),(c,"↗","Suggests what to review","Creates evidence-grounded reports for human review and action.")]:
        with col: st.markdown(f"<div class='card'><div style='font-size:25px'>{icon}</div><h3>{title}</h3><p>{desc}</p></div>",unsafe_allow_html=True)
    st.markdown("<div class='section-title' style='margin-top:28px'>Get started</div>",unsafe_allow_html=True)
    x,y=st.columns(2)
    with x:
        st.markdown("<div class='card'><h3>📝 Collect feedback</h3><p>Open Student Feedback Form to enter a response or import a CSV dataset.</p></div>",unsafe_allow_html=True)
        if st.button("Open feedback form →"): st.session_state['go_form']=True; st.rerun()
    with y: st.markdown("<div class='card'><h3>📊 Explore insights</h3><p>Run NLP analysis and review sentiment and recurring themes in the teacher dashboard.</p></div>",unsafe_allow_html=True)

elif page=="Student Feedback Form":
    st.markdown("<div class='section-title'>Share your learning experience</div><p class='small-muted'>Your feedback helps the academic team improve courses and learning support.</p>",unsafe_allow_html=True)
    with st.form("student_feedback",clear_on_submit=True):
        course=st.text_input("Course / class name",placeholder="e.g. Biology Foundation")
        trainer=st.text_input("Teacher / trainer name",placeholder="Optional")
        learner=st.text_input("Learner reference (optional)",placeholder="Use an anonymous code, not a full name")
        feedback=st.text_area("Your feedback *",height=150,placeholder="What worked well? What could be improved?")
        submitted=st.form_submit_button("Submit feedback",type="primary")
        if submitted:
            if not feedback.strip(): st.error("Please enter feedback before submitting.")
            else:
                try:
                    db.add_feedback_batch([{"feedback_text":feedback.strip(),"course_name":course.strip() or "General","trainer_name":trainer.strip() or "Not specified","learner_id":learner.strip() or "anonymous"}])
                    st.success("Thank you! Your feedback has been saved.")
                except Exception as e: st.error(f"Could not save feedback: {e}")
    st.divider(); st.markdown("### Import multiple responses")
    uploaded=st.file_uploader("Upload CSV (required column: feedback_text)",type=["csv"],key="csv_upload")
    if uploaded:
        try:
            preview=pd.read_csv(uploaded); st.dataframe(preview.head(8),use_container_width=True)
            if st.button("Import CSV responses",type="primary"):
                uploaded.seek(0); rows=read_uploaded_csv(uploaded); n=db.add_feedback_batch(rows); st.success(f"Imported {n} responses.")
        except Exception as e: st.error(f"CSV validation failed: {e}")
    st.download_button("Download sample CSV template",data="feedback_text,course_name,trainer_name,learner_id\nThe lessons were clear and engaging,Biology,Ms. A,anonymous_01\nMore practice examples would help,Chemistry,Mr. B,anonymous_02\n",file_name="feedback_template.csv",mime="text/csv")

elif page=="Teacher Dashboard":
    st.markdown("<div class='section-title'>Teacher dashboard</div><p class='small-muted'>A concise view of learner experience and recurring signals.</p>",unsafe_allow_html=True)
    dashboard=db.get_dashboard_data(); counts={x['sentiment']:x['count'] for x in dashboard['sentiments']}
    cols=st.columns(4); cols[0].metric("Total responses",dashboard['total']); cols[1].metric("Positive",counts.get('Positive',0)); cols[2].metric("Negative",counts.get('Negative',0)); cols[3].metric("Neutral",counts.get('Neutral',0))
    if st.button("Run NLP analysis",type="primary"):
        try:
            with st.spinner("Cleaning text, analysing sentiment and clustering themes..."):
                result=FeedbackAnalyzer(db).run_analysis(max_clusters=5)
            st.success(f"Analysis completed for {result['processed']} responses.")
            st.session_state['analysis_result']=result
        except Exception as e: st.error(f"Analysis could not run: {e}")
    result=st.session_state.get('analysis_result')
    if result:
        st.info(f"Latest run: {result['processed']} processed · {result['positive']} positive · {result['negative']} negative · {result['neutral']} neutral")
    dashboard=db.get_dashboard_data(); counts={x['sentiment']:x['count'] for x in dashboard['sentiments']}
    left,right=st.columns(2)
    with left:
        st.markdown("### Sentiment distribution")
        if sum(counts.values()): st.bar_chart(pd.DataFrame([{"Sentiment":k,"Responses":v} for k,v in counts.items()]).set_index('Sentiment'))
        else: st.info("Run analysis after adding feedback.")
    with right:
        st.markdown("### Recurring themes")
        themes=dashboard['themes']
        if themes and any(x['theme_name']!='Unassigned' for x in themes): st.bar_chart(pd.DataFrame(themes).set_index('theme_name')['count'])
        else: st.info("Theme clusters will appear after NLP analysis.")
    st.markdown("### Latest learner responses")
    if dashboard['feedback']: st.dataframe(pd.DataFrame(dashboard['feedback']),use_container_width=True,hide_index=True)
    else: st.info("No feedback yet. Add a response or load sample data.")

elif page=="How It Works":
    st.markdown("<div class='section-title'>How the workflow works</div>",unsafe_allow_html=True)
    steps=[("01 · Collect","Learners submit feedback through the form, or an educator imports a validated CSV file."),("02 · Prepare","Python validates inputs and NLP preprocessing cleans text and detects language."),("03 · Analyse","Sentiment analysis estimates tone; TF-IDF and clustering identify recurring themes."),("04 · Store","SQLite stores responses, courses, trainers, themes, reports and audit activity."),("05 · Review","A report is generated from the available evidence. Educators review findings before taking action.")]
    for title,desc in steps: st.markdown(f"<div class='card' style='min-height:unset;margin-bottom:12px'><div class='eyebrow'>{title}</div><p style='font-size:15px;margin:7px 0 0'>{desc}</p></div>",unsafe_allow_html=True)
    st.warning("AI-generated summaries are decision-support only. They may be incomplete; a qualified human reviewer must verify findings.")

elif page=="History & Reports":
    st.markdown("<div class='section-title'>History & quality reports</div>",unsafe_allow_html=True)
    reports=db.list_reports()
    if reports:
        rdf=pd.DataFrame(reports); st.dataframe(rdf[['report_id','report_title','provider','model','status','created_at']],use_container_width=True,hide_index=True)
        choice=st.selectbox("Open saved report",rdf['report_id'].tolist())
        selected=next(r for r in reports if r['report_id']==choice); st.markdown(selected['report_text'])
    else: st.info("No reports saved yet. Generate one after adding and analysing feedback.")
    st.divider(); st.markdown("### Generate quality improvement report")
    st.caption("Uses OpenAI when OPENAI_API_KEY is configured; otherwise creates a clearly labelled offline evidence summary.")
    if st.button("Generate report",type="primary"):
        try:
            result=ReportGenerator().generate(db.get_dashboard_data())
            db.save_report("Learner Feedback Quality Report",result['text'],result['provider'],result['model'],result['status'])
            st.session_state['latest_report']=result; st.success(f"Report saved · {result['provider']} · {result['status']}")
        except Exception as e: st.error(f"Report generation failed: {e}")
    latest=st.session_state.get('latest_report')
    if latest:
        st.markdown(latest['text']); st.download_button("Download report (.md)",latest['text'],file_name="learner_feedback_report.md",mime="text/markdown")
    with st.expander("Recent audit activity"):
        with db.connect() as con:
            logs=[dict(r) for r in con.execute("SELECT audit_id,action,details,created_at FROM audit_logs ORDER BY audit_id DESC LIMIT 50").fetchall()]
        if logs: st.dataframe(pd.DataFrame(logs),use_container_width=True,hide_index=True)
        else: st.info("No audit events recorded yet.")

st.markdown("<hr><div style='text-align:center;color:#8499bd;font-size:12px;padding:8px'>LEARNER FEEDBACK THEME ANALYZER · Python · NLP · SQLite · Human-reviewed AI reports</div>",unsafe_allow_html=True)
