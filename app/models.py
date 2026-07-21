import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.config import Config, logger

class LeadManager:
    """Manage lead data with file-based persistence"""
    
    def __init__(self):
        self.data_file = Config.LEADS_FILE
        self._ensure_data_directory()
        self.leads = self._load_data()
        logger.info(f"Loaded {len(self.leads)} leads from storage")
    
    def _ensure_data_directory(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    def _load_data(self) -> Dict:
        """Load leads from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading data: {e}")
                return {}
        return {}
    
    def _save_data(self):
        """Save leads to JSON file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.leads, f, indent=2, default=str)
            logger.debug("Data saved successfully")
        except IOError as e:
            logger.error(f"Error saving data: {e}")
    
    def add_lead(self, user_id: str, data: Dict) -> bool:
        """Add a new lead"""
        if user_id in self.leads:
            logger.warning(f"Lead {user_id} already exists")
            return False
        
        self.leads[user_id] = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "status": "new",
            "score": 0,
            "data": data,
            "interactions": [],
            "created_at": datetime.now().isoformat()
        }
        self._save_data()
        logger.info(f"New lead added: {user_id}")
        return True
    
    def update_lead(self, user_id: str, updates: Dict) -> bool:
        """Update lead data"""
        if user_id not in self.leads:
            return False
        
        self.leads[user_id].update(updates)
        self.leads[user_id]["updated_at"] = datetime.now().isoformat()
        self._save_data()
        return True
    
    def get_lead(self, user_id: str) -> Optional[Dict]:
        """Get lead by user ID"""
        return self.leads.get(user_id)
    
    def get_all_leads(self) -> List[Dict]:
        """Get all leads as list"""
        return list(self.leads.values())
    
    def add_interaction(self, user_id: str, interaction_type: str, details: Dict) -> bool:
        """Add interaction to lead"""
        if user_id not in self.leads:
            return False
        
        interaction = {
            "type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.leads[user_id]["interactions"].append(interaction)
        self._save_data()
        return True
    
    def get_stats(self) -> Dict:
        """Get lead statistics"""
        total = len(self.leads)
        status_counts = {}
        total_score = 0
        
        for lead in self.leads.values():
            status = lead.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
            total_score += lead.get("score", 0)
        
        return {
            "total": total,
            "by_status": status_counts,
            "average_score": total_score / total if total > 0 else 0
        }

class LeadQualifier:
    """Lead qualification engine"""
    
    @staticmethod
    def qualify(data: Dict) -> Dict:
        """
        Qualify a lead based on provided data
        Returns: {score: int, status: str, criteria: List[str]}
        """
        score = 0
        criteria = []
        
        # Email validation
        email = data.get("email", "")
        if email:
            if LeadQualifier._is_valid_email(email):
                score += 20
                criteria.append("Valid email")
                
                if LeadQualifier._is_business_email(email):
                    score += 15
                    criteria.append("Business email")
        
        # Company validation
        company = data.get("company", "")
        if company and len(company) > 2:
            score += 20
            criteria.append("Company provided")
        
        # Budget validation
        budget_str = data.get("budget", "")
        if budget_str:
            try:
                budget = float(budget_str.replace(',', ''))
                if budget >= 5000:
                    score += 30
                    criteria.append("High budget")
                elif budget >= 1000:
                    score += 20
                    criteria.append("Medium budget")
                elif budget >= 500:
                    score += 10
                    criteria.append("Low budget")
            except ValueError:
                pass
        
        # Interest level
        interest = data.get("interest", "").lower()
        high_interest_keywords = ["high", "urgent", "ready", "now", "immediate"]
        if any(keyword in interest for keyword in high_interest_keywords):
            score += 20
            criteria.append("High interest")
        
        # Determine status
        if score >= 70:
            status = "qualified"
        elif score >= 40:
            status = "potential"
        else:
            status = "new"
        
        return {
            "score": score,
            "status": status,
            "criteria": criteria
        }
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def _is_business_email(email: str) -> bool:
        """Check if email is from a business domain"""
        domain = email.split('@')[1].lower()
        free_domains = Config.FREE_EMAIL_DOMAINS
        return domain not in free_domains
