# models/audit_log.py
from datetime import datetime
from extensions import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    __table_args__ = {'extend_existing': True}  # 🧠 Fixes the duplicate compilation error
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Who performed the action
    action = db.Column(db.String(100), nullable=False)                         # e.g., "CREATE_PRESCRIPTION"
    details = db.Column(db.Text, nullable=True)                               # Detailed description
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)