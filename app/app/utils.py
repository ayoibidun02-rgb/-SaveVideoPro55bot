import re
from datetime import datetime
from typing import Dict, Any

def format_timestamp(timestamp: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return "Unknown"

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    # Remove potentially dangerous characters
    return re.sub(r'[<>{}]', '', text)

def format_lead_summary(lead: Dict[str, Any]) -> str:
    """Format lead data for display"""
    data = lead.get("data", {})
    summary = f"""
📋 **Lead Summary**
━━━━━━━━━━━━━━━━━━━━━
📧 **Email:** {data.get('email', 'N/A')}
🏢 **Company:** {data.get('company', 'N/A')}
💰 **Budget:** ${data.get('budget', 'N/A')}
❓ **Interest:** {data.get('interest', 'N/A')}
📱 **Phone:** {data.get('phone', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━
📊 **Score:** {lead.get('score', 0)}/100
🎯 **Status:** {lead.get('status', 'unknown').upper()}
📅 **Created:** {format_timestamp(lead.get('created_at', ''))}
"""
    return summary

def get_status_emoji(status: str) -> str:
    """Get emoji for lead status"""
    emojis = {
        'qualified': '🟢',
        'potential': '🟡',
        'new': '⚪',
        'lost': '🔴'
    }
    return emojis.get(status, '⚪')
