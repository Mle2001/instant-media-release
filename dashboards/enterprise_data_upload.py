"""
Enterprise Data Upload Dashboard
Streamlit-based interface for enterprises to upload campaign feedback data
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import asyncio
import time
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import plotly.graph_objects as go
import plotly.express as px
from loguru import logger
import requests
import io

# Set page configuration
st.set_page_config(
    page_title="Enterprise ML Data Upload",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #3b82f6, #1e40af);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .upload-section {
        background: #f8fafc;
        padding: 2rem;
        border-radius: 1rem;
        border-left: 4px solid #3b82f6;
        margin: 1rem 0;
    }
    
    .metrics-card {
        background: white;
        padding: 1.5rem;
        border-radius: 0.8rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #e2e8f0;
    }
    
    .success-message {
        background: #dcfce7;
        color: #166534;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #22c55e;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fef3c7;
        color: #92400e;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f59e0b;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #fee2e2;
        color: #dc2626;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ef4444;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'uploaded_campaigns' not in st.session_state:
    st.session_state.uploaded_campaigns = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'enterprise_id' not in st.session_state:
    st.session_state.enterprise_id = ""

def main():
    """Main dashboard function"""
    
    # Header
    st.markdown('<h1 class="main-header">🏢 Enterprise ML Data Upload Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Configuration
        st.subheader("API Settings")
        api_base_url = st.text_input(
            "API Base URL",
            value="http://localhost:8000",
            help="Base URL of the Instant Media Release API"
        )
        
        st.session_state.api_key = st.text_input(
            "API Key",
            type="password",
            value=st.session_state.api_key,
            help="Your enterprise API key for authentication"
        )
        
        st.session_state.enterprise_id = st.text_input(
            "Enterprise ID",
            value=st.session_state.enterprise_id,
            help="Your unique enterprise identifier"
        )
        
        # Upload Statistics from database
        st.subheader("📊 Upload Statistics")
        
        # Get real stats from database
        try:
            import sqlite3
            conn = sqlite3.connect("media_release.db")
            cursor = conn.cursor()
            
            # Get total campaigns
            cursor.execute("SELECT COUNT(*) FROM ml_feedback_data")
            total_campaigns = cursor.fetchone()[0]
            
            # Get total budget and average ROI
            cursor.execute("SELECT SUM(budget), AVG(roi_percentage) FROM ml_feedback_data")
            budget_roi = cursor.fetchone()
            total_budget = budget_roi[0] if budget_roi[0] else 0
            avg_roi = budget_roi[1] if budget_roi[1] else 0
            
            conn.close()
            
            st.metric("Campaigns Uploaded", total_campaigns)
            st.metric("Total Budget", f"{total_budget:,.0f} VND")
            st.metric("Average ROI", f"{avg_roi:.1f}%")
            
        except Exception as e:
            st.metric("Campaigns Uploaded", len(st.session_state.uploaded_campaigns))
            if st.session_state.uploaded_campaigns:
                total_budget = sum(camp.get('budget', 0) for camp in st.session_state.uploaded_campaigns)
                st.metric("Total Budget", f"{total_budget:,.0f} VND")
                avg_roi = np.mean([camp.get('roi_percentage', 0) for camp in st.session_state.uploaded_campaigns])
                st.metric("Average ROI", f"{avg_roi:.1f}%")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload Data", "📊 Data Preview", "📈 Analytics", "🔧 Batch Upload", "🗑️ Manage Data"])
    
    with tab1:
        upload_single_campaign(api_base_url)
    
    with tab2:
        preview_uploaded_data()
    
    with tab3:
        show_analytics()
    
    with tab4:
        batch_upload_interface(api_base_url)
    
    with tab5:
        manage_data_tab()

def upload_single_campaign(api_base_url: str):
    """Interface for uploading single campaign data"""
    
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📋 Campaign Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        campaign_title = st.text_input("Campaign Title", placeholder="Enter campaign name")
        campaign_type = st.selectbox(
            "Campaign Type",
            ["product_launch", "brand_awareness", "lead_generation", "event_promotion", "crisis_management"]
        )
        industry = st.selectbox(
            "Industry",
            ["technology", "fintech", "healthcare", "retail", "manufacturing", "education", "tourism", "other"]
        )
        budget = st.number_input("Budget (VND)", min_value=1000000, value=10000000, step=1000000)
    
    with col2:
        launch_date = st.date_input("Launch Date", value=date.today() - timedelta(days=60))
        completion_date = st.date_input("Completion Date", value=date.today() - timedelta(days=30))
        campaign_duration = (completion_date - launch_date).days
        st.metric("Campaign Duration", f"{campaign_duration} days")
        
        target_audience = st.multiselect(
            "Target Audience",
            ["SME", "startups", "enterprises", "consumers", "students", "professionals", "investors"],
            default=["SME"]
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Media Performance Metrics
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("📺 Media Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📰 Publication Metrics**")
        total_articles = st.number_input("Total Articles Published", min_value=0, value=10)
        total_reach = st.number_input("Total Media Reach", min_value=0, value=500000)
        tier1_coverage = st.number_input("Tier 1 Coverage", min_value=0, value=3)
    
    with col2:
        st.markdown("**📱 Engagement Metrics**")
        click_through_rate = st.slider("Click Through Rate (%)", 0.0, 10.0, 2.5, 0.1) / 100
        social_shares = st.number_input("Social Media Shares", min_value=0, value=500)
        media_quality_score = st.slider("Media Quality Score", 0.0, 10.0, 7.0, 0.1)
    
    with col3:
        st.markdown("**🎯 Coverage Distribution**")
        tier2_coverage = st.number_input("Tier 2 Coverage", min_value=0, value=5)
        tier3_coverage = st.number_input("Tier 3 Coverage", min_value=0, value=2)
        publication_success_rate = st.slider("Publication Success Rate", 0.0, 1.0, 0.8, 0.01)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Business Impact Metrics
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("💼 Business Impact Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💰 Revenue Metrics**")
        revenue_generated = st.number_input("Revenue Generated (VND)", min_value=0, value=50000000)
        roi_percentage = ((revenue_generated - budget) / budget * 100) if budget > 0 else 0
        st.metric("Calculated ROI", f"{roi_percentage:.1f}%")
        
        lead_generation = st.number_input("Leads Generated", min_value=0, value=100)
        sales_conversion = st.number_input("Sales Conversions", min_value=0, value=20)
    
    with col2:
        st.markdown("**📈 Brand Metrics**")
        brand_awareness_lift = st.slider("Brand Awareness Lift (%)", 0.0, 100.0, 15.0, 0.5)
        brand_mention_increase = st.slider("Brand Mention Increase (%)", 0.0, 200.0, 25.0, 1.0)
        market_share_gain = st.slider("Market Share Gain (%)", 0.0, 20.0, 1.5, 0.1)
        
        customer_acquisition_cost = budget / sales_conversion if sales_conversion > 0 else 0
        st.metric("Customer Acquisition Cost", f"{customer_acquisition_cost:,.0f} VND")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Audience Engagement Metrics
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("👥 Audience Engagement Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        average_engagement_rate = st.slider("Average Engagement Rate", 0.0, 0.2, 0.035, 0.001)
        audience_retention_rate = st.slider("Audience Retention Rate", 0.0, 1.0, 0.65, 0.01)
        user_generated_content = st.number_input("User Generated Content", min_value=0, value=15)
    
    with col2:
        comment_sentiment_score = st.slider("Comment Sentiment Score", -1.0, 1.0, 0.6, 0.01)
        social_virality_score = st.slider("Social Virality Score", 0.0, 1.0, 0.25, 0.01)
        influencer_engagement_rate = st.slider("Influencer Engagement Rate", 0.0, 0.3, 0.05, 0.001)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Cost Efficiency Metrics  
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    st.subheader("💸 Cost Efficiency Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cost_per_impression = st.number_input("Cost per Impression (VND)", min_value=0.0, value=0.02, format="%.4f")
        cost_per_click = st.number_input("Cost per Click (VND)", min_value=0.0, value=0.8, format="%.2f")
        budget_utilization = st.slider("Budget Utilization", 0.0, 1.2, 0.95, 0.01)
    
    with col2:
        cost_per_lead = budget / lead_generation if lead_generation > 0 else 0
        st.metric("Cost per Lead", f"{cost_per_lead:,.0f} VND")
        
        efficiency_vs_industry_avg = st.slider("Efficiency vs Industry Average", 0.0, 3.0, 1.2, 0.1)
        waste_percentage = st.slider("Waste Percentage", 0.0, 50.0, 5.0, 0.5)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Validation and Upload
    if st.button("🚀 Upload Campaign Data", type="primary", use_container_width=True):
        if not all([campaign_title, st.session_state.enterprise_id, st.session_state.api_key]):
            st.error("Please fill in all required fields and configure API settings in the sidebar.")
            return
        
        if completion_date <= launch_date:
            st.error("Completion date must be after launch date.")
            return
        
        # Prepare campaign data
        campaign_data = {
            "enterprise_id": st.session_state.enterprise_id,
            "campaign_id": f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "campaign_title": campaign_title,
            "campaign_type": campaign_type,
            "industry": industry,
            "target_audience": target_audience,
            "budget": budget,
            
            # Media Performance
            "total_articles_published": total_articles,
            "total_media_reach": total_reach,
            "click_through_rate": click_through_rate,
            "social_media_shares": social_shares,
            "media_quality_score": media_quality_score,
            "publication_success_rate": publication_success_rate,
            "tier1_coverage": tier1_coverage,
            "tier2_coverage": tier2_coverage,
            "tier3_coverage": tier3_coverage,
            "average_article_quality": media_quality_score,
            
            # Business Impact
            "brand_awareness_lift": brand_awareness_lift,
            "lead_generation": lead_generation,
            "sales_conversion": sales_conversion,
            "revenue_generated": revenue_generated,
            "roi_percentage": roi_percentage,
            "customer_acquisition_cost": customer_acquisition_cost,
            "brand_mention_increase": brand_mention_increase,
            "market_share_gain": market_share_gain,
            
            # Audience Engagement
            "average_engagement_rate": average_engagement_rate,
            "comment_sentiment_score": comment_sentiment_score,
            "audience_retention_rate": audience_retention_rate,
            "social_virality_score": social_virality_score,
            "user_generated_content": user_generated_content,
            "influencer_engagement_rate": influencer_engagement_rate,
            "audience_quality_score": (comment_sentiment_score + 1) * 5,  # Convert to 0-10 scale
            
            # Cost Efficiency
            "cost_per_acquisition": customer_acquisition_cost,
            "cost_per_impression": cost_per_impression,
            "cost_per_click": cost_per_click,
            "budget_utilization": budget_utilization,
            "cost_per_lead": cost_per_lead,
            "efficiency_vs_industry_avg": efficiency_vs_industry_avg,
            "waste_percentage": waste_percentage,
            
            # Dates
            "campaign_duration_days": campaign_duration,
            "launch_date": launch_date.isoformat(),
            "completion_date": completion_date.isoformat(),
            "feedback_timestamp": datetime.now().isoformat()
        }
        
        # Upload to API
        success = upload_campaign_data(api_base_url, campaign_data)
        
        if success:
            st.session_state.uploaded_campaigns.append(campaign_data)
            st.markdown('<div class="success-message">✅ Campaign data uploaded successfully! The ML system will use this data to improve ranking accuracy.</div>', unsafe_allow_html=True)
            
            # Refresh the page to update statistics
            time.sleep(1)  # Brief delay to ensure database write is committed
            st.rerun()
            
            # Show summary
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("ROI", f"{roi_percentage:.1f}%")
            with col2:
                st.metric("Total Reach", f"{total_reach:,}")
            with col3:
                st.metric("Conversion Rate", f"{(sales_conversion/lead_generation*100):.1f}%" if lead_generation > 0 else "0%")
            with col4:
                st.metric("Media Quality", f"{media_quality_score:.1f}/10")
        else:
            st.markdown('<div class="error-message">❌ Failed to upload campaign data. Please check your API settings and try again.</div>', unsafe_allow_html=True)

def upload_campaign_data(api_base_url: str, campaign_data: Dict) -> bool:
    """Upload campaign data directly to database"""
    try:
        # Import database modules
        import sqlite3
        import json
        from datetime import datetime
        
        # Connect to database
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        # Calculate ground truth score
        roi = campaign_data.get('roi_percentage', 0) / 100
        reach = campaign_data.get('total_media_reach', 0)
        articles = campaign_data.get('total_articles_published', 0)
        
        # Simple ground truth calculation (0-1 scale)
        ground_truth = min(1.0, max(0.0, 
            (roi * 0.4 + (articles / 10) * 0.3 + (reach / 200000) * 0.3)
        ))
        
        # Insert into ml_feedback_data table
        cursor.execute("""
            INSERT INTO ml_feedback_data (
                enterprise_id, campaign_id, campaign_title, campaign_type, industry,
                target_audience, budget, total_articles_published, total_media_reach,
                click_through_rate, social_media_shares, media_quality_score,
                brand_awareness_lift, lead_generation, sales_conversion, roi_percentage,
                average_engagement_rate, comment_sentiment_score, audience_retention_rate,
                cost_per_acquisition, cost_per_impression, budget_utilization,
                ground_truth_score, confidence_score, feedback_source, data_quality, validated, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_data.get('enterprise_id', 'DASHBOARD_USER'),
            campaign_data.get('campaign_id'),
            campaign_data.get('campaign_title'),
            campaign_data.get('campaign_type'),
            campaign_data.get('industry'),
            json.dumps(campaign_data.get('target_audience', [])),
            campaign_data.get('budget'),
            campaign_data.get('total_articles_published'),
            campaign_data.get('total_media_reach'),
            campaign_data.get('click_through_rate'),
            campaign_data.get('social_media_shares'),
            campaign_data.get('media_quality_score'),
            campaign_data.get('brand_awareness_lift'),
            campaign_data.get('lead_generation'),
            campaign_data.get('sales_conversion'),
            campaign_data.get('roi_percentage'),
            campaign_data.get('average_engagement_rate'),
            campaign_data.get('comment_sentiment_score', 0.5),
            campaign_data.get('audience_retention_rate'),
            campaign_data.get('budget', 0) / max(campaign_data.get('lead_generation', 1), 1),  # cost_per_acquisition
            0.05,  # cost_per_impression
            95.0,  # budget_utilization
            ground_truth,
            0.85,  # confidence_score
            "enterprise_dashboard",
            "good",
            True,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        st.error(f"Upload Error: {str(e)}")
        return False

def preview_uploaded_data():
    """Preview uploaded campaign data from database"""
    st.subheader("📊 Uploaded Campaign Data")
    
    # Get real data from database
    try:
        import sqlite3
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT campaign_title, campaign_type, industry, budget, 
                   total_articles_published, total_media_reach, lead_generation,
                   sales_conversion, roi_percentage, ground_truth_score, created_at
            FROM ml_feedback_data 
            ORDER BY created_at DESC
        """)
        
        campaigns = cursor.fetchall()
        conn.close()
        
        if not campaigns:
            st.info("No campaign data found in database. Use the 'Upload Data' tab to add your first campaign.")
            return
        
        st.success(f"Found {len(campaigns)} campaigns in database")
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return
    
    # Display campaigns from database
    for i, campaign in enumerate(campaigns):
        # Unpack database row
        title, c_type, industry, budget, articles, reach, leads, conversion, roi, score, created = campaign
        
        with st.expander(f"📋 {title} ({c_type})", expanded=i == 0):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Campaign Details**")
                st.write(f"• Industry: {industry}")
                st.write(f"• Budget: {budget:,} VND")
                st.write(f"• Created: {created[:10]}")
                st.write(f"• Ground Truth Score: {score:.3f}")
            
            with col2:
                st.markdown("**Performance**")
                st.write(f"• ROI: {roi:.1f}%")
                st.write(f"• Articles: {articles}")
                st.write(f"• Reach: {reach:,}")
                st.write(f"• Leads: {leads}")
            
            with col3:
                st.markdown("**Conversion Metrics**")
                st.write(f"• Sales Conversion: {conversion}")
                st.write(f"• Conversion Rate: {(conversion/leads*100):.1f}%" if leads > 0 else "0%")
                st.write(f"• Cost per Lead: {budget/leads:,.0f} VND" if leads > 0 else "N/A")
                st.write(f"• Revenue per Article: {(budget * roi/100)/articles:,.0f} VND" if articles > 0 else "N/A")
            
            # Performance visualization
            metrics = {
                "ROI %": roi,
                "Ground Truth": score * 100,  # Scale to %
                "Reach (K)": reach / 1000,
                "Articles": articles * 10  # Scale for visualization
            }
            
            fig = go.Figure(data=go.Bar(
                x=list(metrics.keys()),
                y=list(metrics.values()),
                marker_color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
            ))
            fig.update_layout(
                title=f"Performance Metrics - {title}",
                yaxis_title="Score/Value",
                height=300
            )
            st.plotly_chart(fig, use_container_width=True, key=f"campaign_chart_{i}")
    
    # Summary statistics from database
    if len(campaigns) > 1:
        st.subheader("📈 Campaign Summary")
        
        # Convert database data to DataFrame
        df = pd.DataFrame(campaigns, columns=[
            'campaign_title', 'campaign_type', 'industry', 'budget',
            'total_articles_published', 'total_media_reach', 'lead_generation',
            'sales_conversion', 'roi_percentage', 'ground_truth_score', 'created_at'
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            # ROI distribution
            fig = px.histogram(
                df,
                x="roi_percentage",
                title="ROI Distribution",
                nbins=10,
                color_discrete_sequence=['#3b82f6']
            )
            st.plotly_chart(fig, use_container_width=True, key="roi_histogram")
        
        with col2:
            # Industry performance
            industry_avg = df.groupby('industry')['roi_percentage'].mean().reset_index()
            fig = px.bar(
                industry_avg,
                x="industry",
                y="roi_percentage",
                title="Average ROI by Industry",
                color="roi_percentage",
                color_continuous_scale="viridis"
            )
            st.plotly_chart(fig, use_container_width=True, key="industry_roi")

def show_analytics():
    """Show analytics dashboard with real database data"""
    st.subheader("📈 Campaign Analytics")
    
    # Get real data from database
    try:
        import sqlite3
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT campaign_title, campaign_type, industry, budget, 
                   total_articles_published, total_media_reach, lead_generation,
                   sales_conversion, roi_percentage, ground_truth_score, created_at
            FROM ml_feedback_data 
            ORDER BY created_at DESC
        """)
        
        campaigns = cursor.fetchall()
        conn.close()
        
        if not campaigns:
            st.info("Upload some campaign data to see analytics.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(campaigns, columns=[
            'campaign_title', 'campaign_type', 'industry', 'budget',
            'total_articles_published', 'total_media_reach', 'lead_generation',
            'sales_conversion', 'roi_percentage', 'ground_truth_score', 'created_at'
        ])
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_roi = df['roi_percentage'].mean()
        st.metric("Average ROI", f"{avg_roi:.1f}%", delta=f"{avg_roi - 100:.1f}%")
    
    with col2:
        total_reach = df['total_media_reach'].sum()
        st.metric("Total Reach", f"{total_reach:,.0f}")
    
    with col3:
        avg_score = df['ground_truth_score'].mean()
        st.metric("Avg Ground Truth", f"{avg_score:.3f}")
    
    with col4:
        total_budget = df['budget'].sum()
        st.metric("Total Budget", f"{total_budget:,.0f} VND")
    
    # Performance over time
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df_sorted = df.sort_values('created_at')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_sorted['created_at'],
            y=df_sorted['roi_percentage'],
            mode='lines+markers',
            name='ROI %',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="ROI Performance Over Time",
            xaxis_title="Upload Date",
            yaxis_title="ROI %",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, key="roi_timeline")
    
    # Correlation analysis
    numeric_cols = [
        'budget', 'total_articles_published', 'total_media_reach',
        'ground_truth_score', 'roi_percentage', 'lead_generation'
    ]
    
    if len(df) > 2:
        correlation_matrix = df[numeric_cols].corr()
        
        fig = px.imshow(
            correlation_matrix,
            title="Correlation Matrix - Key Metrics",
            color_continuous_scale="RdBu_r",
            aspect="auto"
        )
        st.plotly_chart(fig, use_container_width=True, key="correlation_matrix")
    
    # Performance insights
    st.subheader("🔍 Performance Insights")
    
    # Best performing campaign
    best_campaign = df.loc[df['roi_percentage'].idxmax()]
    worst_campaign = df.loc[df['roi_percentage'].idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🏆 Best Performing Campaign**")
        st.success(f"**{best_campaign['campaign_title']}**")
        st.write(f"• ROI: {best_campaign['roi_percentage']:.1f}%")
        st.write(f"• Industry: {best_campaign['industry']}")
        st.write(f"• Ground Truth: {best_campaign['ground_truth_score']:.3f}")
    
    with col2:
        st.markdown("**📉 Needs Improvement**")
        st.warning(f"**{worst_campaign['campaign_title']}**")
        st.write(f"• ROI: {worst_campaign['roi_percentage']:.1f}%")
        st.write(f"• Industry: {worst_campaign['industry']}")
        st.write(f"• Ground Truth: {worst_campaign['ground_truth_score']:.3f}")

def batch_upload_interface(api_base_url: str):
    """Interface for batch uploading campaign data"""
    st.subheader("📂 Batch Upload Campaign Data")
    
    st.markdown("""
    Upload multiple campaigns at once using a CSV file. Download the template below to see the required format.
    """)
    
    # Download template
    if st.button("📥 Download CSV Template"):
        template_data = {
            "campaign_title": ["Example Campaign 1", "Example Campaign 2"],
            "campaign_type": ["product_launch", "brand_awareness"],
            "industry": ["technology", "fintech"],
            "budget": [10000000, 15000000],
            "total_articles_published": [10, 15],
            "total_media_reach": [500000, 750000],
            "click_through_rate": [0.025, 0.035],
            "social_media_shares": [500, 800],
            "media_quality_score": [7.5, 8.0],
            "brand_awareness_lift": [15.0, 20.0],
            "lead_generation": [100, 150],
            "sales_conversion": [20, 30],
            "revenue_generated": [50000000, 80000000],
            "average_engagement_rate": [0.035, 0.045],
            "comment_sentiment_score": [0.6, 0.7],
            "audience_retention_rate": [0.65, 0.70],
            "launch_date": ["2024-01-15", "2024-02-01"],
            "completion_date": ["2024-02-14", "2024-03-02"]
        }
        
        template_df = pd.DataFrame(template_data)
        csv = template_df.to_csv(index=False)
        
        st.download_button(
            label="📄 Download Template CSV",
            data=csv,
            file_name="campaign_data_template.csv",
            mime="text/csv"
        )
    
    # File upload
    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=['csv'],
        help="Upload a CSV file containing campaign data"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            st.success(f"✅ File loaded successfully! Found {len(df)} campaigns.")
            
            # Preview data
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Validation
            required_columns = [
                'campaign_title', 'campaign_type', 'industry', 'budget',
                'total_articles_published', 'total_media_reach', 'lead_generation'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            else:
                st.success("✅ All required columns present")
                
                # Upload button
                if st.button("🚀 Upload All Campaigns", type="primary"):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    success_count = 0
                    total_campaigns = len(df)
                    
                    for i, row in df.iterrows():
                        status_text.text(f"Uploading campaign {i+1}/{total_campaigns}: {row['campaign_title']}")
                        
                        # Convert row to campaign data format
                        campaign_data = row.to_dict()
                        campaign_data['enterprise_id'] = st.session_state.enterprise_id
                        campaign_data['campaign_id'] = f"batch_{datetime.now().strftime('%Y%m%d')}_{i}"
                        campaign_data['feedback_timestamp'] = datetime.now().isoformat()
                        
                        # Upload
                        if upload_campaign_data(api_base_url, campaign_data):
                            success_count += 1
                            st.session_state.uploaded_campaigns.append(campaign_data)
                        
                        progress_bar.progress((i + 1) / total_campaigns)
                    
                    status_text.text("")
                    progress_bar.empty()
                    
                    if success_count == total_campaigns:
                        st.balloons()
                        st.success(f"🎉 All {total_campaigns} campaigns uploaded successfully!")
                        time.sleep(1)  # Brief delay
                        st.rerun()  # Refresh to update statistics
                    else:
                        st.warning(f"⚠️ {success_count}/{total_campaigns} campaigns uploaded successfully.")
                        if success_count > 0:
                            time.sleep(1)  # Brief delay
                            st.rerun()  # Refresh to update statistics
        
        except Exception as e:
            st.error(f"❌ Error reading file: {str(e)}")

def manage_data_tab():
    """Data management tab with delete functionality"""
    st.header("🗑️ Data Management")
    
    # Get data from database
    try:
        import sqlite3
        conn = sqlite3.connect("media_release.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, enterprise_id, campaign_title, campaign_type, industry, 
                   budget, total_media_reach, roi_percentage, created_at
            FROM ml_feedback_data 
            ORDER BY created_at DESC
        """)
        
        campaigns = cursor.fetchall()
        conn.close()
        
        if not campaigns:
            st.info("No campaign data found to manage.")
            return
        
        st.success(f"Found {len(campaigns)} campaigns in database")
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return
    
    # Create DataFrame for easier manipulation
    df = pd.DataFrame(campaigns, columns=[
        'ID', 'Enterprise ID', 'Campaign Title', 'Type', 'Industry', 
        'Budget', 'Media Reach', 'ROI %', 'Created At'
    ])
    
    # Format display
    df['Budget'] = df['Budget'].apply(lambda x: f"{x:,.0f} VND" if pd.notna(x) else "N/A")
    df['Media Reach'] = df['Media Reach'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
    df['ROI %'] = df['ROI %'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
    df['Created At'] = pd.to_datetime(df['Created At']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Display options
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("📊 Campaign Data")
        
    with col2:
        # Bulk delete options
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.session_state.get('confirm_delete_all', False):
                try:
                    conn = sqlite3.connect("media_release.db")
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM ml_feedback_data")
                    deleted_count = cursor.rowcount
                    conn.commit()
                    conn.close()
                    
                    st.success(f"✅ Deleted {deleted_count} campaigns successfully!")
                    st.session_state.confirm_delete_all = False
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error deleting data: {e}")
            else:
                st.session_state.confirm_delete_all = True
                st.warning("⚠️ Click again to confirm deletion of ALL data!")
    
    # Display data with individual delete options
    for i, (idx, row) in enumerate(df.iterrows()):
        with st.expander(f"📋 {row['Campaign Title']} ({row['Type']})", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write(f"**Industry:** {row['Industry']}")
                st.write(f"**Budget:** {row['Budget']}")
                st.write(f"**Media Reach:** {row['Media Reach']}")
                
            with col2:
                st.write(f"**ROI:** {row['ROI %']}")
                st.write(f"**Created:** {row['Created At']}")
                st.write(f"**Enterprise:** {row['Enterprise ID']}")
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{row['ID']}"):
                    try:
                        conn = sqlite3.connect("media_release.db")
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM ml_feedback_data WHERE id = ?", (row['ID'],))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"✅ Deleted campaign: {row['Campaign Title']}")
                        time.sleep(1)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error deleting campaign: {e}")
    
    # Statistics
    st.subheader("📈 Data Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Campaigns", len(campaigns))
    
    with col2:
        total_budget = sum([c[5] for c in campaigns if c[5]])
        st.metric("Total Budget", f"{total_budget:,.0f} VND")
    
    with col3:
        avg_roi = np.mean([c[7] for c in campaigns if c[7]])
        st.metric("Average ROI", f"{avg_roi:.1f}%")
    
    with col4:
        industries = set([c[4] for c in campaigns if c[4]])
        st.metric("Industries", len(industries))

if __name__ == "__main__":
    main()