"""Seed the database with initial data for the Availability Toggle module."""
from datetime import datetime, timedelta
from app import app, db, Helper, Emergency, ActivityLog


def seed():
    with app.app_context():
        db.create_all()

        # skip if already seeded
        if Helper.query.first():
            print('Database already seeded. Skipping.')
            return

        # ─── Helpers ──────────────────────────────
        helpers = [
            Helper(name='Dr. Rahim Ahmed', role='Blood Donor (A+)', location='Dhaka', avatar='RA', is_online=True),
            Helper(name='Fatima Khatun', role='First Responder', location='Chittagong', avatar='FK', is_online=True),
            Helper(name='Arif Hossain', role='Ambulance Driver', location='Dhaka', avatar='AH', is_online=True),
            Helper(name='Nusrat Jahan', role='Oxygen Supplier', location='Sylhet', avatar='NJ', is_online=True),
            Helper(name='Kamal Uddin', role='Blood Donor (O-)', location='Rajshahi', avatar='KU', is_online=False),
            Helper(name='Sadia Islam', role='First Responder', location='Dhaka', avatar='SI', is_online=True),
        ]
        db.session.add_all(helpers)

        # ─── Emergencies ─────────────────────────
        now = datetime.utcnow()
        emergencies = [
            Emergency(type='Blood', status='completed', location='Dhaka Medical', urgency='high', created_at=now - timedelta(days=2)),
            Emergency(type='Ambulance', status='accepted', location='Chittagong GEC', urgency='medium', created_at=now - timedelta(days=3)),
            Emergency(type='Oxygen', status='completed', location='Sylhet MAG', urgency='high', created_at=now - timedelta(days=4)),
            Emergency(type='Blood', status='cancelled', location='Rajshahi Medical', urgency='low', created_at=now - timedelta(days=6)),
            Emergency(type='Ambulance', status='pending', location='Khulna Sadar', urgency='medium', created_at=now - timedelta(days=7)),
            Emergency(type='Blood', status='active', location='BSMMU Dhaka', urgency='high', created_at=now - timedelta(hours=3)),
            Emergency(type='Oxygen', status='active', location='Comilla Medical', urgency='high', created_at=now - timedelta(hours=5)),
            Emergency(type='Ambulance', status='active', location='Gazipur City', urgency='medium', created_at=now - timedelta(hours=1)),
            Emergency(type='Blood', status='pending', location='Mymensingh Medical', urgency='high', created_at=now - timedelta(hours=2)),
            Emergency(type='Oxygen', status='pending', location='Rangpur Medical', urgency='medium', created_at=now - timedelta(hours=4)),
            Emergency(type='Ambulance', status='active', location='Barisal Sher-e-Bangla', urgency='high', created_at=now - timedelta(hours=6)),
            Emergency(type='Blood', status='active', location='Narayanganj General', urgency='medium', created_at=now - timedelta(minutes=45)),
        ]
        db.session.add_all(emergencies)

        # ─── Activity Log ────────────────────────
        activities = [
            ActivityLog(type='online', text='Dr. Rahim Ahmed came online', icon='🟢', created_at=now - timedelta(minutes=2)),
            ActivityLog(type='accepted', text='Blood request #1042 accepted by Fatima Khatun', icon='✅', created_at=now - timedelta(minutes=5)),
            ActivityLog(type='new', text='New emergency: Oxygen needed at Sylhet Medical', icon='🚨', created_at=now - timedelta(minutes=8)),
            ActivityLog(type='completed', text='Ambulance request #1039 marked as completed', icon='🏁', created_at=now - timedelta(minutes=12)),
            ActivityLog(type='offline', text='Kamal Uddin went offline', icon='🔴', created_at=now - timedelta(minutes=15)),
            ActivityLog(type='online', text='Sadia Islam came online', icon='🟢', created_at=now - timedelta(minutes=20)),
        ]
        db.session.add_all(activities)

        db.session.commit()
        print('Database seeded successfully!')
        print(f'  - {len(helpers)} helpers')
        print(f'  - {len(emergencies)} emergencies')
        print(f'  - {len(activities)} activity log entries')


if __name__ == '__main__':
    seed()
